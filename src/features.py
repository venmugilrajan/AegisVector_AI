import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

def compute_spatial_adjacency(wards_meta: pd.DataFrame, k_neighbors=3):
    """
    Computes k-nearest neighbour adjacency dictionary between wards based on coordinates.
    """
    coords = wards_meta[["lat", "lon"]].values
    dists = cdist(coords, coords)
    adj = {}
    for i, w_id in enumerate(wards_meta["ward_id"]):
        # Sort indices by distance, omit self (index 0)
        closest_idx = np.argsort(dists[i])[1:k_neighbors+1]
        adj[w_id] = [wards_meta.iloc[idx]["ward_id"] for idx in closest_idx]
    return adj

def build_features_and_targets(df: pd.DataFrame, wards_meta: pd.DataFrame, horizons=[2, 4, 6]):
    """
    Feature engineering for epidemiological forecasting:
    - Lagged reported cases (1, 2, 3, 4, 5, 6, 7, 8 weeks)
    - Short-term case growth rate (diff(1) / (lag1 + 1))
    - Rainfall lags (2, 3, 4, 5, 6, 7, 8 weeks)
    - Temperature and humidity (contemporaneous + 2-week lag)
    - Week-of-year cyclical encoding (sin/cos of 2*pi*week/52)
    - Spatial spillover: mean reported cases in k-nearest neighbouring wards (lag 1 and lag 2)
    - Explicit Data Quality Score as a feature
    - Targets: future true cases at horizons h in [2, 4, 6]
    Strict time ordering: NO forward leakage.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ward_id", "date"]).reset_index(drop=True)

    # Impute missing reported cases forward with zero fill fallback for lag calculation
    # but retain the original reported_cases to compute quality score
    df["cases_imputed"] = df.groupby("ward_id")["reported_cases"].transform(lambda s: s.ffill().fillna(0.0))

    adj_dict = compute_spatial_adjacency(wards_meta, k_neighbors=3)

    # Pre-compute spatial lag map: (date, ward_id) -> mean neighbor cases
    pivot_cases = df.pivot(index="date", columns="ward_id", values="cases_imputed")
    
    neighbor_lag1 = {}
    neighbor_lag2 = {}
    for w_id in wards_meta["ward_id"]:
        neighbors = adj_dict[w_id]
        neighbor_lag1[w_id] = pivot_cases[neighbors].mean(axis=1).shift(1)
        neighbor_lag2[w_id] = pivot_cases[neighbors].mean(axis=1).shift(2)

    df_list = []
    for w_id, group in df.groupby("ward_id"):
        g = group.copy().sort_values("date").reset_index(drop=True)
        
        # Week of year cyclical features
        woy = g["date"].dt.isocalendar().week.astype(float)
        g["sin_week"] = np.sin(2 * np.pi * woy / 52.14)
        g["cos_week"] = np.cos(2 * np.pi * woy / 52.14)
        
        # Case lags (1 to 8 weeks)
        for lag in range(1, 9):
            g[f"case_lag_{lag}"] = g["cases_imputed"].shift(lag)
            
        # Case growth rates
        g["case_growth_1w"] = (g["case_lag_1"] - g["case_lag_2"]) / (g["case_lag_2"] + 1.0)
        g["case_growth_4w"] = (g["case_lag_1"] - g["case_lag_4"]) / (g["case_lag_4"] + 1.0)

        # Rainfall lags (2 to 8 weeks, critical for vector development)
        for rlag in range(2, 9):
            g[f"rain_lag_{rlag}"] = g["rainfall"].shift(rlag)
            
        # Weather features
        g["temp_lag_0"] = g["temperature"]
        g["temp_lag_2"] = g["temperature"].shift(2)
        g["humid_lag_0"] = g["humidity"]
        g["humid_lag_2"] = g["humidity"].shift(2)

        # Neighbor spatial lags
        g["neighbor_lag_1"] = g["date"].map(neighbor_lag1[w_id]).values
        g["neighbor_lag_2"] = g["date"].map(neighbor_lag2[w_id]).values

        # Targets for horizons h in [2, 4, 6]
        # Target is true_cases (or reported if evaluating field ground truth) h weeks ahead
        for h in horizons:
            g[f"target_h{h}"] = g["true_cases"].shift(-h)

        df_list.append(g)

    featured_df = pd.concat(df_list, axis=0).sort_values(["date", "ward_id"]).reset_index(drop=True)
    
    # Feature columns list
    feature_cols = [
        "sin_week", "cos_week",
        "quality_score",
        "population",
        "case_growth_1w", "case_growth_4w",
        "temp_lag_0", "temp_lag_2", "humid_lag_0", "humid_lag_2",
        "neighbor_lag_1", "neighbor_lag_2"
    ] + [f"case_lag_{i}" for i in range(1, 9)] + [f"rain_lag_{i}" for i in range(2, 9)]

    return featured_df, feature_cols
