import pytest
import numpy as np
import pandas as pd

from src.quality import DataQualityScorer
from src.features import build_features_and_targets
from src.conformal import SplitConformalCalibrator
from src.decision import DecisionEngine
from src.prioritise import ResourcePrioritiser
from src.forecast import BaselineForecasters

def test_quality_score_bounds_and_penalties():
    """
    Test that quality score strictly satisfies bounds [0.0, 1.0],
    clean series gets score ~ 1.0, and completely missing series gets score near 0.
    """
    scorer = DataQualityScorer()
    clean_series = pd.Series([10.0, 12.0, 11.0, 13.0, 10.0] * 5)
    clean_scores = scorer.compute_ward_quality_series(clean_series)
    assert np.all(clean_scores >= 0.0)
    assert np.all(clean_scores <= 1.0)
    assert clean_scores.iloc[-1] >= 0.95
    
    nan_series = pd.Series([np.nan] * 20)
    nan_scores = scorer.compute_ward_quality_series(nan_series)
    assert np.all(nan_scores >= 0.0)
    assert np.all(nan_scores <= 1.0)
    assert nan_scores.iloc[-1] < 0.35

def test_no_leakage_in_time_split():
    """
    Verify feature engineering does not leak future information:
    Past lags and rolling windows must only look backwards.
    Targets are future shifted.
    """
    dates = pd.date_range("2022-01-01", periods=50, freq="W-MON")
    df = pd.DataFrame({
        "date": dates,
        "ward_id": "W01",
        "reported_cases": np.arange(50, dtype=float),
        "true_cases": np.arange(50, dtype=float),
        "rainfall": np.ones(50) * 20.0,
        "temperature": np.ones(50) * 30.0,
        "humidity": np.ones(50) * 75.0,
        "population": 50000,
        "quality_score": 1.0
    })
    wards_meta = pd.DataFrame([{
        "ward_id": "W01",
        "lat": 6.9,
        "lon": 79.8,
        "population": 50000
    }])
    
    featured_df, _ = build_features_and_targets(df, wards_meta, horizons=[2, 4])
    
    idx_10 = 10
    assert featured_df.loc[idx_10, "case_lag_1"] == df.loc[idx_10 - 1, "reported_cases"]
    assert featured_df.loc[idx_10, "case_lag_2"] == df.loc[idx_10 - 2, "reported_cases"]
    assert featured_df.loc[idx_10, "target_h2"] == df.loc[idx_10 + 2, "true_cases"]
    assert featured_df.loc[idx_10, "target_h4"] == df.loc[idx_10 + 4, "true_cases"]

def test_conformal_coverage_near_nominal():
    """
    Test split-conformal calibrator guarantees coverage close to nominal 90%
    on held-out calibration distributions.
    """
    np.random.seed(42)
    n = 1000
    y_true = np.random.normal(50, 10, size=n)
    q05 = y_true - 12 + np.random.normal(0, 2, size=n)
    q50 = y_true + np.random.normal(0, 1, size=n)
    q95 = y_true + 12 + np.random.normal(0, 2, size=n)
    
    calib_df = pd.DataFrame({
        "target_h2": y_true[:500],
        "q05_h2": q05[:500],
        "q50_h2": q50[:500],
        "q95_h2": q95[:500]
    })
    
    conformal = SplitConformalCalibrator(target_coverage=0.90)
    conformal.calibrate(calib_df, horizons=[2])
    
    val_preds = pd.DataFrame({
        "q05": q05[500:],
        "q50": q50[500:],
        "q95": q95[500:]
    })
    intervals = conformal.predict_interval(val_preds, horizon=2)
    res = conformal.evaluate_coverage(y_true[500:], intervals["lower"].values, intervals["upper"].values)
    assert 0.86 <= res["coverage"] <= 0.94

def test_confidence_gate_abstain_never_funded():
    """
    Test that a ward with Insufficient confidence is NEVER funded or ranked as safe,
    even if its point risk is the highest in the city.
    """
    prioritiser = ResourcePrioritiser(default_budget_teams=3)
    df = pd.DataFrame({
        "ward_id": ["W01", "W02", "W03", "W04", "W05"],
        "point": [100.0, 30.0, 28.0, 25.0, 10.0],
        "population": [100000, 80000, 90000, 75000, 50000],
        "confidence_status": ["Insufficient confidence", "Alert", "Alert", "Alert", "Normal"]
    })
    
    allocated = prioritiser.allocate(df, budget_teams=2, risk_col="point", pop_col="population", status_col="confidence_status")
    
    w01_row = allocated[allocated["ward_id"] == "W01"].iloc[0]
    assert w01_row["funded"] == False
    assert w01_row["action"] == "Verify data first"
    
    funded_wards = allocated[allocated["funded"]]["ward_id"].tolist()
    assert "W01" not in funded_wards
    assert len(funded_wards) == 2

def test_budget_allocation_exactness():
    """
    Test that the number of funded wards never exceeds budget teams N.
    """
    prioritiser = ResourcePrioritiser(default_budget_teams=5)
    df = pd.DataFrame({
        "ward_id": [f"W{i:02d}" for i in range(1, 15)],
        "point": np.random.uniform(10, 60, size=14),
        "population": np.random.randint(30000, 100000, size=14),
        "confidence_status": ["Alert"] * 10 + ["Insufficient confidence"] * 4
    })
    
    for budget in [1, 4, 7]:
        allocated = prioritiser.allocate(df, budget_teams=budget, status_col="confidence_status")
        funded_count = allocated["funded"].sum()
        assert funded_count <= budget

def test_sarima_differs_from_persistence():
    """
    Verify that SARIMA produces dynamic autoregressive forecasts that
    differ from naive static persistence on trending / seasonal histories.
    """
    # Create trending series: cases increasing week over week
    trend_history = pd.Series([10.0, 12.0, 15.0, 19.0, 24.0, 30.0, 38.0, 47.0, 58.0, 70.0] * 3)
    persistence_val = float(trend_history.iloc[-1])
    
    sarima_val = BaselineForecasters.fit_predict_sarima(trend_history, steps_ahead=4)
    
    assert isinstance(sarima_val, float)
    assert not np.isnan(sarima_val)
    # Autoregressive SARIMA model projects trend dynamics, differing from static persistence
    assert not np.isclose(sarima_val, persistence_val, atol=0.01), f"SARIMA {sarima_val} was identical to persistence {persistence_val}"
