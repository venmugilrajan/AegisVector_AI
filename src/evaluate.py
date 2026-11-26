import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.data import load_ward_data
from src.quality import DataQualityScorer
from src.features import build_features_and_targets
from src.forecast import QuantileXGBoostForecaster, BaselineForecasters
from src.conformal import SplitConformalCalibrator
from src.decision import DecisionEngine
from src.prioritise import ResourcePrioritiser

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
os.makedirs(RESULTS_DIR, exist_ok=True)

def simulate_masked_data(df: pd.DataFrame, mask_prob: float, seed: int) -> pd.DataFrame:
    """
    Simulates real-world reporting breakdowns by randomly masking mask_prob of weekly reports.
    """
    np.random.seed(seed)
    df_masked = df.copy()
    mask = np.random.uniform(0, 1, size=len(df_masked)) < mask_prob
    df_masked.loc[mask, "reported_cases"] = np.nan
    return df_masked

def calculate_lead_time_gained(
    test_df: pd.DataFrame,
    alert_flags: np.ndarray,
    outbreak_threshold: float = 25.0
) -> float:
    """
    Computes lead time gained:
    For each ward that experiences an epidemic peak, calculates the number of weeks
    between the FIRST alert sounded for that surge and the actual peak week.
    Returns the average lead time in weeks.
    """
    df_sub = test_df.copy()
    df_sub["alert"] = alert_flags
    df_sub["date"] = pd.to_datetime(df_sub["date"])
    
    lead_times = []
    for w_id, group in df_sub.groupby("ward_id"):
        g = group.sort_values("date").reset_index(drop=True)
        # Identify local outbreak peaks (cases >= threshold and peak within 8-week window)
        true_cases = g["true_cases"].values
        alerts = g["alert"].values
        
        for i in range(1, len(g) - 1):
            if true_cases[i] >= outbreak_threshold and true_cases[i] >= true_cases[i-1] and true_cases[i] >= true_cases[i+1]:
                # Found a peak at index i. Look back up to 8 weeks for the first alert
                lookback = max(0, i - 8)
                alert_indices = np.where(alerts[lookback:i])[0]
                if len(alert_indices) > 0:
                    first_alert_idx = lookback + alert_indices[0]
                    lead_weeks = i - first_alert_idx
                    lead_times.append(lead_weeks)
                else:
                    lead_times.append(0.0) # Missed or zero advance lead time

    return float(np.mean(lead_times)) if len(lead_times) > 0 else 0.0

def run_evaluation_suite(n_repeats=20, horizons=[2, 4, 6], masking_levels=[0.10, 0.30, 0.50]):
    """
    Comprehensive historical evaluation suite:
    - 20 random seeds
    - 3 masking levels (10%, 30%, 50%)
    - 3 horizons (2, 4, 6 weeks)
    - Fair metrics:
      1. Alert Precision on ALL wards (unfiltered)
      2. Alert Precision on CONFIDENT wards only (gated)
      3. False Alarm Rate
      4. Abstain Rate (% wards marked Insufficient Confidence)
      5. Empirical Coverage (reported as 'n/a' for Point XGBoost since it has no valid conformal interval)
      6. Lead Time Gained (weeks prior to actual peak)
      7. Wasted Interventions under budget (teams funded where target < 25)
    """
    print(f"[Evaluation] Starting comprehensive evaluation: {n_repeats} repeats across masking {masking_levels}...")
    
    df_raw, metadata, wards_meta = load_ward_data()
    
    artifacts_path = os.path.join(MODELS_DIR, "aegis_artifacts.pkl")
    with open(artifacts_path, "rb") as f:
        artifacts = pickle.load(f)
        
    q_forecaster = artifacts["q_forecaster"]
    baselines = artifacts["baselines"]
    conformal = artifacts["conformal"]
    feature_cols = artifacts["feature_cols"]
    
    decision_engine = DecisionEngine(risk_alert_threshold=25.0, risk_watch_threshold=12.0)
    prioritiser = ResourcePrioritiser(default_budget_teams=8)
    scorer = DataQualityScorer()

    records = []
    unique_dates = np.sort(pd.to_datetime(df_raw["date"]).unique())
    test_dates = unique_dates[int(len(unique_dates) * 0.80):]
    test_dates_str = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in test_dates]
    
    OUTBREAK_THRESHOLD = 25.0
    BUDGET_TEAMS = 8

    for m_level in masking_levels:
        print(f"--- Testing Masking Level: {int(m_level*100)}% ---")
        for rep in range(n_repeats):
            seed = 1000 + rep * 17 + int(m_level * 100)
            
            df_curr = simulate_masked_data(df_raw, mask_prob=m_level, seed=seed)
            df_curr_scored = scorer.score_dataset(df_curr, case_col="reported_cases")
            featured_df, _ = build_features_and_targets(df_curr_scored, wards_meta, horizons=horizons)
            
            test_df = featured_df[featured_df["date"].isin(test_dates)].copy().reset_index(drop=True)
            X_test = test_df[feature_cols].reset_index(drop=True)
            
            for h in horizons:
                y_true = test_df[f"target_h{h}"].values
                valid_mask = ~np.isnan(y_true)
                y_true_v = y_true[valid_mask]
                true_outbreak = (y_true_v >= OUTBREAK_THRESHOLD)
                
                # ----------------------------------------------------
                # 1. AegisVector AI
                # ----------------------------------------------------
                raw_preds = q_forecaster.predict(X_test, horizon=h)
                calib_intervals = conformal.predict_interval(raw_preds, horizon=h)
                
                test_df_eval = test_df.copy()
                test_df_eval["lower"] = calib_intervals["lower"]
                test_df_eval["point"] = calib_intervals["point"]
                test_df_eval["upper"] = calib_intervals["upper"]
                test_df_eval["interval_width"] = calib_intervals["interval_width"]
                test_df_eval["status"] = decision_engine.classify_dataframe(test_df_eval)
                
                # Empirical conformal coverage
                cov_aegis = conformal.evaluate_coverage(
                    y_true_v,
                    calib_intervals.loc[valid_mask, "lower"].values,
                    calib_intervals.loc[valid_mask, "upper"].values
                )["coverage"]
                
                # Precision on ALL wards (if raw point >= threshold)
                all_raw_alerts = (calib_intervals.loc[valid_mask, "point"].values >= OUTBREAK_THRESHOLD)
                tp_all = np.sum(all_raw_alerts & true_outbreak)
                fp_all = np.sum(all_raw_alerts & (~true_outbreak))
                prec_all_aegis = tp_all / (tp_all + fp_all + 1e-6)
                
                # Precision on CONFIDENT wards only (status == "Alert")
                confident_alerts = (test_df_eval.loc[valid_mask, "status"] == "Alert").values
                tp_conf = np.sum(confident_alerts & true_outbreak)
                fp_conf = np.sum(confident_alerts & (~true_outbreak))
                tn_conf = np.sum((~confident_alerts) & (~true_outbreak))
                prec_conf_aegis = tp_conf / (tp_conf + fp_conf + 1e-6)
                fa_rate_aegis = fp_conf / (fp_conf + tn_conf + 1e-6)
                
                abstain_rate_aegis = np.mean(test_df_eval.loc[valid_mask, "status"] == "Insufficient confidence")
                
                # Lead time gained
                lead_time_aegis = calculate_lead_time_gained(test_df_eval, test_df_eval["status"] == "Alert")
                
                # Wasted deployments under budget
                wasted_aegis = 0
                for d, d_group in test_df_eval.groupby("date"):
                    alloc = prioritiser.allocate(d_group, budget_teams=BUDGET_TEAMS, status_col="status")
                    funded_wards = alloc[alloc["funded"]]
                    wasted_aegis += np.sum(funded_wards[f"target_h{h}"] < OUTBREAK_THRESHOLD)

                records.append({
                    "model": "AegisVector AI",
                    "masking": m_level,
                    "repeat": rep,
                    "horizon": h,
                    "coverage": cov_aegis,
                    "has_valid_interval": True,
                    "precision_all": prec_all_aegis,
                    "precision_confident": prec_conf_aegis,
                    "false_alarm_rate": fa_rate_aegis,
                    "abstain_rate": abstain_rate_aegis,
                    "lead_time_weeks": lead_time_aegis,
                    "wasted_interventions": wasted_aegis,
                    "mean_interval_width": np.mean(calib_intervals["interval_width"])
                })
                
                # ----------------------------------------------------
                # 2. Plain XGBoost Baseline (Point Forecast - No Valid Conformal Interval)
                # ----------------------------------------------------
                point_xgb_preds = baselines.predict_point_xgb(X_test, horizon=h)
                xgb_alerts = (point_xgb_preds[valid_mask] >= OUTBREAK_THRESHOLD)
                
                tp_xgb = np.sum(xgb_alerts & true_outbreak)
                fp_xgb = np.sum(xgb_alerts & (~true_outbreak))
                tn_xgb = np.sum((~xgb_alerts) & (~true_outbreak))
                prec_xgb = tp_xgb / (tp_xgb + fp_xgb + 1e-6)
                fa_rate_xgb = fp_xgb / (fp_xgb + tn_xgb + 1e-6)
                
                lead_time_xgb = calculate_lead_time_gained(test_df, point_xgb_preds >= OUTBREAK_THRESHOLD)

                test_df_xgb = test_df.copy()
                test_df_xgb["pred"] = point_xgb_preds
                wasted_xgb = 0
                for d, d_group in test_df_xgb.groupby("date"):
                    g = d_group.copy()
                    r_min, r_max = g["pred"].min(), g["pred"].max()
                    p_min, p_max = g["population"].min(), g["population"].max()
                    norm_r = (g["pred"] - r_min) / (r_max - r_min + 1e-6)
                    norm_p = (g["population"] - p_min) / (p_max - p_min + 1e-6)
                    g["p_score"] = norm_r * norm_p
                    top_funded = g.sort_values(by=["p_score", "pred"], ascending=[False, False]).iloc[:BUDGET_TEAMS]
                    wasted_xgb += np.sum(top_funded[f"target_h{h}"] < OUTBREAK_THRESHOLD)

                records.append({
                    "model": "Plain XGBoost",
                    "masking": m_level,
                    "repeat": rep,
                    "horizon": h,
                    "coverage": np.nan,  # Plain XGBoost has NO real predictive interval -> reported as n/a
                    "has_valid_interval": False,
                    "precision_all": prec_xgb,
                    "precision_confident": prec_xgb, # Never abstains
                    "false_alarm_rate": fa_rate_xgb,
                    "abstain_rate": 0.0,
                    "lead_time_weeks": lead_time_xgb,
                    "wasted_interventions": wasted_xgb,
                    "mean_interval_width": np.nan
                })
                
                # ----------------------------------------------------
                # 3. Persistence Baseline
                # ----------------------------------------------------
                persist_preds = baselines.predict_persistence(test_df, horizon=h)
                persist_alerts = (persist_preds[valid_mask] >= OUTBREAK_THRESHOLD)
                
                tp_p = np.sum(persist_alerts & true_outbreak)
                fp_p = np.sum(persist_alerts & (~true_outbreak))
                tn_p = np.sum((~persist_alerts) & (~true_outbreak))
                prec_p = tp_p / (tp_p + fp_p + 1e-6)
                fa_rate_p = fp_p / (fp_p + tn_p + 1e-6)
                
                lead_time_p = calculate_lead_time_gained(test_df, persist_preds >= OUTBREAK_THRESHOLD)

                test_df_p = test_df.copy()
                test_df_p["pred"] = persist_preds
                wasted_persist = 0
                for d, d_group in test_df_p.groupby("date"):
                    g = d_group.copy()
                    r_min, r_max = g["pred"].min(), g["pred"].max()
                    p_min, p_max = g["population"].min(), g["population"].max()
                    norm_r = (g["pred"] - r_min) / (r_max - r_min + 1e-6)
                    norm_p = (g["population"] - p_min) / (p_max - p_min + 1e-6)
                    g["p_score"] = norm_r * norm_p
                    top_funded = g.sort_values(by=["p_score", "pred"], ascending=[False, False]).iloc[:BUDGET_TEAMS]
                    wasted_persist += np.sum(top_funded[f"target_h{h}"] < OUTBREAK_THRESHOLD)

                records.append({
                    "model": "Persistence",
                    "masking": m_level,
                    "repeat": rep,
                    "horizon": h,
                    "coverage": np.nan,
                    "has_valid_interval": False,
                    "precision_all": prec_p,
                    "precision_confident": prec_p,
                    "false_alarm_rate": fa_rate_p,
                    "abstain_rate": 0.0,
                    "lead_time_weeks": lead_time_p,
                    "wasted_interventions": wasted_persist,
                    "mean_interval_width": np.nan
                })

                # ----------------------------------------------------
                # 4. SARIMA Baseline (True dynamic fit per ward)
                # ----------------------------------------------------
                sarima_preds = BaselineForecasters.batch_predict_sarima(df_curr_scored, test_dates, horizon=h)
                sarima_alerts = (sarima_preds[valid_mask] >= OUTBREAK_THRESHOLD)
                
                tp_s = np.sum(sarima_alerts & true_outbreak)
                fp_s = np.sum(sarima_alerts & (~true_outbreak))
                tn_s = np.sum((~sarima_alerts) & (~true_outbreak))
                prec_s = tp_s / (tp_s + fp_s + 1e-6)
                fa_rate_s = fp_s / (fp_s + tn_s + 1e-6)
                
                lead_time_s = calculate_lead_time_gained(test_df, sarima_preds >= OUTBREAK_THRESHOLD)

                test_df_s = test_df.copy()
                test_df_s["pred"] = sarima_preds
                wasted_sarima = 0
                for d, d_group in test_df_s.groupby("date"):
                    g = d_group.copy()
                    r_min, r_max = g["pred"].min(), g["pred"].max()
                    p_min, p_max = g["population"].min(), g["population"].max()
                    norm_r = (g["pred"] - r_min) / (r_max - r_min + 1e-6)
                    norm_p = (g["population"] - p_min) / (p_max - p_min + 1e-6)
                    g["p_score"] = norm_r * norm_p
                    top_funded = g.sort_values(by=["p_score", "pred"], ascending=[False, False]).iloc[:BUDGET_TEAMS]
                    wasted_sarima += np.sum(top_funded[f"target_h{h}"] < OUTBREAK_THRESHOLD)

                records.append({
                    "model": "SARIMA",
                    "masking": m_level,
                    "repeat": rep,
                    "horizon": h,
                    "coverage": np.nan,
                    "has_valid_interval": False,
                    "precision_all": prec_s,
                    "precision_confident": prec_s,
                    "false_alarm_rate": fa_rate_s,
                    "abstain_rate": 0.0,
                    "lead_time_weeks": lead_time_s,
                    "wasted_interventions": wasted_sarima,
                    "mean_interval_width": np.nan
                })

    eval_df = pd.DataFrame(records)
    eval_csv_path = os.path.join(RESULTS_DIR, "evaluation_raw_runs.csv")
    eval_df.to_csv(eval_csv_path, index=False)
    print(f"[Evaluation] Saved all raw simulation runs to {eval_csv_path}")

    # Aggregated Summary table
    summary = eval_df.groupby(["model", "masking", "horizon"]).agg({
        "coverage": ["mean", "std"],
        "precision_all": ["mean", "std"],
        "precision_confident": ["mean", "std"],
        "false_alarm_rate": ["mean", "std"],
        "wasted_interventions": ["mean", "std"],
        "abstain_rate": ["mean", "std"],
        "lead_time_weeks": ["mean", "std"],
        "mean_interval_width": ["mean", "std"]
    }).reset_index()

    summary.columns = [
        f"{col[0]}_{col[1]}" if col[1] else col[0]
        for col in summary.columns
    ]
    summary_path = os.path.join(RESULTS_DIR, "evaluation_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"[Evaluation] Saved aggregated summary table to {summary_path}")

    plot_evaluation_results(eval_df)
    return eval_df, summary

def plot_evaluation_results(eval_df: pd.DataFrame):
    sns.set_theme(style="whitegrid", font="sans-serif")
    palette = {
        "AegisVector AI": "#1E88E5",
        "Plain XGBoost": "#D81B60",
        "SARIMA": "#FFC107",
        "Persistence": "#757575"
    }

    # 1. Precision on Confident Wards (Horizon 4w)
    plt.figure(figsize=(9, 5))
    h4_df = eval_df[eval_df["horizon"] == 4].copy()
    h4_df["masking_pct"] = (h4_df["masking"] * 100).astype(int).astype(str) + "%"
    
    sns.barplot(
        data=h4_df,
        x="masking_pct",
        y="precision_confident",
        hue="model",
        palette=palette,
        errorbar="sd",
        capsize=0.1
    )
    plt.title("Alert Precision under Missing Data (4-Week Horizon)", fontsize=14, weight="bold")
    plt.xlabel("Simulated Missing Weekly Reports", fontsize=12)
    plt.ylabel("Precision on Active Alerts", fontsize=12)
    plt.ylim(0, 1.05)
    plt.legend(title="Method", loc="lower left")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "precision_under_masking.png"), dpi=300)
    plt.close()

    # 2. Lead Time Gained
    plt.figure(figsize=(9, 5))
    sns.barplot(
        data=h4_df,
        x="masking_pct",
        y="lead_time_weeks",
        hue="model",
        palette=palette,
        errorbar="sd",
        capsize=0.1
    )
    plt.title("Proactive Lead Time Gained Before Epidemic Peak (Weeks)", fontsize=14, weight="bold")
    plt.xlabel("Simulated Missing Weekly Reports", fontsize=12)
    plt.ylabel("Lead Time (Weeks)", fontsize=12)
    plt.legend(title="Method", loc="upper right")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "lead_time_gained.png"), dpi=300)
    plt.close()

    # 3. Abstain Dynamics
    fig, ax1 = plt.subplots(figsize=(9, 5))
    aegis_df = eval_df[eval_df["model"] == "AegisVector AI"].copy()
    aegis_df["masking_pct"] = (aegis_df["masking"] * 100).astype(int).astype(str) + "%"

    sns.barplot(
        data=aegis_df,
        x="masking_pct",
        y="abstain_rate",
        hue="horizon",
        palette="Blues",
        ax=ax1,
        errorbar="sd"
    )
    ax1.set_title("AegisVector Knowing When NOT to Trust Itself (Abstain Rate)", fontsize=14, weight="bold")
    ax1.set_xlabel("Missing Data Degradation Rate", fontsize=12)
    ax1.set_ylabel("Abstain Rate (% Marked Insufficient Confidence)", fontsize=12)
    ax1.set_ylim(0, 1.0)
    ax1.legend(title="Forecast Horizon")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "aegis_abstain_dynamics.png"), dpi=300)
    plt.close()

if __name__ == "__main__":
    run_evaluation_suite(n_repeats=20)
