import numpy as np
import pandas as pd

class ResourcePrioritiser:
    """
    Prioritises wards under a limited intervention resource budget (e.g. N field teams).
    
    Formula:
    Priority Score = minmax(risk) * minmax(population_exposed)
    
    Crucial Rule:
    Confidence is an absolute GATE, not a multiplicative discount!
    - Wards with 'Insufficient confidence' are NEVER funded as active intervention targets.
    - Instead, if high-risk but low-confidence, they are designated 'Verify data first'
      and flagged on a dedicated priority review board (never labelled 'Safe').
    - Confident wards ('Alert', 'Watch', 'Normal') are ranked by priority score and funded
      up to budget N.
      
    Action Mapping:
    - Alert + Funded -> 'Fogging + larvicide'
    - Watch + Funded -> 'Source reduction'
    - Normal + Funded -> 'Inspection drive'
    - Any + Insufficient Confidence (high risk) -> 'Verify data first'
    - Any + Insufficient Confidence (low risk) -> 'Data review required'
    - Confident + Unfunded -> 'Routine surveillance'
    """
    def __init__(self, default_budget_teams=8):
        self.default_budget_teams = default_budget_teams

    def allocate(
        self,
        forecast_df: pd.DataFrame,
        budget_teams: int = None,
        risk_col="point",
        pop_col="population",
        status_col="confidence_status",
        ward_col="ward_id"
    ) -> pd.DataFrame:
        df = forecast_df.copy()
        if budget_teams is None:
            budget_teams = self.default_budget_teams

        # 1. Normalize risk and population to [0, 1]
        risk_vals = df[risk_col].values.astype(float)
        pop_vals = df[pop_col].values.astype(float)

        risk_min, risk_max = np.min(risk_vals), np.max(risk_vals)
        pop_min, pop_max = np.min(pop_vals), np.max(pop_vals)

        norm_risk = (risk_vals - risk_min) / (risk_max - risk_min + 1e-6)
        norm_pop = (pop_vals - pop_min) / (pop_max - pop_min + 1e-6)

        df["priority_score"] = np.round(norm_risk * norm_pop, 4)
        
        # 2. Gate separation: Confident vs Insufficient Confidence
        is_confident = df[status_col] != "Insufficient confidence"
        
        df["is_confident"] = is_confident
        df["funded"] = False
        df["rank"] = np.nan
        df["action"] = "Routine surveillance"

        # Confident candidates sorted by priority score descending
        confident_df = df[is_confident].sort_values(by=["priority_score", risk_col], ascending=[False, False])
        
        funded_indices = confident_df.index[:budget_teams]
        df.loc[funded_indices, "funded"] = True
        
        # Assign ranks
        # Confident funded wards get ranks 1 .. K
        for r, idx in enumerate(funded_indices, start=1):
            df.loc[idx, "rank"] = r
            
        # Confident unfunded get subsequent ranks
        unfunded_confident = confident_df.index[budget_teams:]
        for r, idx in enumerate(unfunded_confident, start=len(funded_indices) + 1):
            df.loc[idx, "rank"] = r

        # Low-confidence wards get designated verification ranks / tags
        low_conf_df = df[~is_confident].sort_values(by=risk_col, ascending=False)
        for r, idx in enumerate(low_conf_df.index, start=len(confident_df) + 1):
            df.loc[idx, "rank"] = r

        # 3. Action Mapping
        for idx, row in df.iterrows():
            stat = row[status_col]
            funded = row["funded"]
            risk = row[risk_col]
            
            if stat == "Insufficient confidence":
                if risk >= 15.0:
                    df.loc[idx, "action"] = "Verify data first"
                else:
                    df.loc[idx, "action"] = "Data review required"
            elif funded:
                if stat == "Alert":
                    df.loc[idx, "action"] = "Fogging + larvicide"
                elif stat == "Watch":
                    df.loc[idx, "action"] = "Source reduction"
                else:
                    df.loc[idx, "action"] = "Inspection drive"
            else:
                df.loc[idx, "action"] = "Routine surveillance"

        df["rank"] = df["rank"].astype(int)
        df = df.sort_values("rank").reset_index(drop=True)
        return df
