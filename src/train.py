import os
import pickle
import numpy as np
import pandas as pd

from src.data import load_ward_data
from src.quality import DataQualityScorer
from src.features import build_features_and_targets
from src.forecast import QuantileXGBoostForecaster, BaselineForecasters
from src.conformal import SplitConformalCalibrator
from src.decision import DecisionEngine
from src.prioritise import ResourcePrioritiser

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def train_pipeline():
    """
    End-to-end training and split-conformal calibration pipeline:
    1. Loads ward datasets.
    2. Scores historical data quality.
    3. Builds lagged & climate & spatial spillover features (strictly causal, no leakage).
    4. Time-based chronological split:
       - Train: weeks 0 to T_train (~65%)
       - Calibration: weeks T_train to T_calib (~15%)
       - Test: weeks T_calib to end (~20%)
    5. Fits Quantile XGBoost (0.05, 0.50, 0.95) & Point Baselines across horizons [2, 4, 6].
    6. Calibrates prediction intervals on the calibration window using split-conformal prediction.
    7. Evaluates coverage on test window and saves artifacts.
    """
    print("[Pipeline] Loading ward data...")
    df, metadata, wards_meta = load_ward_data()
    
    print("[Pipeline] Scoring data quality per ward...")
    scorer = DataQualityScorer()
    df_scored = scorer.score_dataset(df, case_col="reported_cases")
    
    print("[Pipeline] Building feature tables without lookahead leakage...")
    horizons = [2, 4, 6]
    featured_df, feature_cols = build_features_and_targets(df_scored, wards_meta, horizons=horizons)
    
    # Save processed dataset
    featured_df.to_parquet(os.path.join(PROCESSED_DIR, "featured_dengue.parquet"), index=False)
    
    # Chronological Time Split
    unique_dates = np.sort(featured_df["date"].unique())
    n_dates = len(unique_dates)
    
    train_end_idx = int(n_dates * 0.65)
    calib_end_idx = int(n_dates * 0.80)
    
    train_dates = unique_dates[:train_end_idx]
    calib_dates = unique_dates[train_end_idx:calib_end_idx]
    test_dates = unique_dates[calib_end_idx:]
    
    print(f"[Split] Total dates: {n_dates} | Train: {len(train_dates)} | Calib: {len(calib_dates)} | Test: {len(test_dates)}")
    
    train_df = featured_df[featured_df["date"].isin(train_dates)]
    calib_df = featured_df[featured_df["date"].isin(calib_dates)].copy()
    test_df = featured_df[featured_df["date"].isin(test_dates)].copy()
    
    X_train = train_df[feature_cols]
    y_train_dict = {h: train_df[f"target_h{h}"] for h in horizons}
    
    print("[Pipeline] Training Quantile XGBoost forecasters for horizons [2, 4, 6]...")
    q_forecaster = QuantileXGBoostForecaster(quantiles=[0.05, 0.50, 0.95], horizons=horizons, seed=42)
    q_forecaster.fit(X_train, y_train_dict)
    
    print("[Pipeline] Training Point XGBoost baseline...")
    baselines = BaselineForecasters(horizons=horizons, seed=42)
    baselines.fit_point_xgb(X_train, y_train_dict)
    
    # Predict on Calibration set to obtain non-conformity distributions
    X_calib = calib_df[feature_cols]
    for h in horizons:
        preds = q_forecaster.predict(X_calib, horizon=h)
        calib_df[f"q05_h{h}"] = preds["q05"].values
        calib_df[f"q50_h{h}"] = preds["q50"].values
        calib_df[f"q95_h{h}"] = preds["q95"].values
        
    print("[Pipeline] Calibrating Split-Conformal prediction intervals (target: 90%)...")
    conformal = SplitConformalCalibrator(target_coverage=0.90)
    conformal.calibrate(calib_df, horizons=horizons)
    print(f"[Conformal] Calibrated correction offsets (q_hat): {conformal.q_hat}")
    
    # Test evaluation of empirical coverage
    X_test = test_df[feature_cols]
    test_coverage_report = {}
    for h in horizons:
        preds = q_forecaster.predict(X_test, horizon=h)
        intervals = conformal.predict_interval(preds, horizon=h)
        y_test = test_df[f"target_h{h}"].values
        cov_res = conformal.evaluate_coverage(y_test, intervals["lower"].values, intervals["upper"].values)
        test_coverage_report[h] = cov_res
        print(f"[Test Coverage Horizon {h}w] Empirical coverage: {cov_res['coverage']*100:.1f}%, Mean width: {cov_res['mean_width']:.1f}")

    # Save models and calibration state
    artifacts = {
        "q_forecaster": q_forecaster,
        "baselines": baselines,
        "conformal": conformal,
        "feature_cols": feature_cols,
        "horizons": horizons,
        "test_coverage_report": test_coverage_report,
        "split_info": {
            "train_end": str(train_dates[-1]),
            "calib_end": str(calib_dates[-1]),
            "test_start": str(test_dates[0]),
            "test_end": str(test_dates[-1])
        }
    }
    with open(os.path.join(MODELS_DIR, "aegis_artifacts.pkl"), "wb") as f:
        pickle.dump(artifacts, f)
        
    print("[Pipeline] Training and calibration complete. Artifacts saved to models/aegis_artifacts.pkl.")
    return artifacts

if __name__ == "__main__":
    train_pipeline()
