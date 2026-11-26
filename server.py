import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.data import load_ward_data
from src.quality import DataQualityScorer
from src.features import build_features_and_targets
from src.forecast import QuantileXGBoostForecaster, BaselineForecasters
from src.conformal import SplitConformalCalibrator
from src.decision import DecisionEngine
from src.prioritise import ResourcePrioritiser

app = FastAPI(
    title="AegisVector AI API",
    description="Uncertainty-Aware Dengue Outbreak Forecasting & Allocation Service",
    version="1.0.0"
)

# Enable CORS for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global caches
artifacts = None
raw_data = None
wards_meta = None
metadata = None
feature_cols = None
q_forecaster = None
conformal = None
dates_list = []

def load_system():
    global artifacts, raw_data, wards_meta, metadata, feature_cols, q_forecaster, conformal, dates_list
    base_dir = os.path.dirname(os.path.abspath(__file__))
    artifacts_path = os.path.join(base_dir, "models", "aegis_artifacts.pkl")
    with open(artifacts_path, "rb") as f:
        artifacts = pickle.load(f)
    
    q_forecaster = artifacts["q_forecaster"]
    conformal = artifacts["conformal"]
    feature_cols = artifacts["feature_cols"]
    
    df_raw, meta, w_meta = load_ward_data()
    raw_data = df_raw
    metadata = meta
    wards_meta = w_meta
    
    dates_list = sorted([str(d)[:10] for d in pd.to_datetime(df_raw["date"]).unique()])

# Load on startup
load_system()

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "system": "AegisVector AI",
        "wards_count": len(wards_meta),
        "is_synthetic": metadata.get("is_synthetic", True),
        "available_dates_count": len(dates_list)
    }

@app.get("/api/metadata")
def get_metadata():
    return {
        "is_synthetic": metadata.get("is_synthetic", True),
        "data_source": metadata.get("source", "OpenDengue/Open-Meteo Synthetic Fallback"),
        "dates": dates_list,
        "default_date": dates_list[-15] if len(dates_list) >= 15 else dates_list[-1],
        "horizons": [2, 4, 6],
        "wards": wards_meta.to_dict(orient="records")
    }

class ForecastRequest(BaseModel):
    date: str
    horizon: int = 4
    budget_teams: int = 8
    mask_pct: float = 0.0
    risk_alert_threshold: float = 25.0
    risk_watch_threshold: float = 12.0
    max_rel_width: float = 1.5
    min_quality_score: float = 0.65

@app.post("/api/forecast")
def run_forecast(req: ForecastRequest):
    if req.date not in dates_list:
        raise HTTPException(status_code=400, detail=f"Date {req.date} not found in surveillance timeline.")
    
    selected_date = pd.to_datetime(req.date)
    
    # 1. Apply simulation masking if requested
    df_sim = raw_data.copy()
    if req.mask_pct > 0:
        np.random.seed(42 + int(req.mask_pct * 10))
        mask = (np.random.uniform(0, 100, size=len(df_sim)) < req.mask_pct) & (pd.to_datetime(df_sim["date"]) <= selected_date)
        df_sim.loc[mask, "reported_cases"] = np.nan
        
    # 2. Quality scoring
    scorer = DataQualityScorer()
    df_scored = scorer.score_dataset(df_sim, case_col="reported_cases")
    
    # 3. Features
    featured_df, _ = build_features_and_targets(df_scored, wards_meta, horizons=[2, 4, 6])
    
    # 4. Current slice
    current_slice = featured_df[featured_df["date"] == selected_date].copy().reset_index(drop=True)
    if len(current_slice) == 0:
        raise HTTPException(status_code=404, detail="No feature slice available for this date.")
    
    # 5. Predict with Conformal Intervals
    X_curr = current_slice[feature_cols]
    raw_preds = q_forecaster.predict(X_curr, horizon=req.horizon)
    intervals = conformal.predict_interval(raw_preds, horizon=req.horizon)
    
    current_slice["lower"] = intervals["lower"]
    current_slice["point"] = intervals["point"]
    current_slice["upper"] = intervals["upper"]
    current_slice["interval_width"] = intervals["interval_width"]
    
    # 6. Tri-state decision logic
    decision_engine = DecisionEngine(
        risk_alert_threshold=req.risk_alert_threshold,
        risk_watch_threshold=req.risk_watch_threshold,
        max_rel_width=req.max_rel_width,
        min_quality_score=req.min_quality_score
    )
    current_slice["confidence_status"] = decision_engine.classify_dataframe(current_slice)
    
    # 7. Priority and Resource Allocation
    prioritiser = ResourcePrioritiser(default_budget_teams=req.budget_teams)
    allocated = prioritiser.allocate(
        current_slice,
        budget_teams=req.budget_teams,
        risk_col="point",
        pop_col="population",
        status_col="confidence_status",
        ward_col="ward_id"
    )
    
    # Merge ward spatial coordinates
    merged = allocated.merge(wards_meta[["ward_id", "lat", "lon", "ward_name"]], on="ward_id", how="left")
    
    # Compute summary KPIs
    n_alert = int((merged["confidence_status"] == "Alert").sum())
    n_watch = int((merged["confidence_status"] == "Watch").sum())
    n_abstain = int((merged["confidence_status"] == "Insufficient confidence").sum())
    n_normal = int((merged["confidence_status"] == "Normal").sum())
    n_funded = int(merged["funded"].sum())
    n_verify = int((merged["action"] == "Verify data first").sum())
    mean_quality = float(merged["quality_score"].mean())
    avg_rel_width = float((merged["interval_width"] / (merged["point"] + 1.0)).mean())
    
    # Convert records for response
    wards_results = []
    for _, row in merged.iterrows():
        wards_results.append({
            "ward_id": str(row["ward_id"]),
            "ward_name": str(row["ward_name"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "population": int(row["population"]),
            "reported_cases": float(row["reported_cases"]) if not pd.isna(row["reported_cases"]) else None,
            "quality_score": round(float(row["quality_score"]), 3),
            "point": round(float(row["point"]), 1),
            "lower": round(float(row["lower"]), 1),
            "upper": round(float(row["upper"]), 1),
            "interval_width": round(float(row["interval_width"]), 1),
            "confidence_status": str(row["confidence_status"]),
            "priority_score": round(float(row["priority_score"]), 4),
            "priority_rank": int(row["rank"]) if not pd.isna(row["rank"]) else None,
            "is_funded": bool(row["funded"]),
            "action": str(row["action"])
        })
        
    return {
        "date": req.date,
        "horizon": req.horizon,
        "budget_teams": req.budget_teams,
        "mask_pct": req.mask_pct,
        "kpis": {
            "total_wards": len(merged),
            "alert_count": n_alert,
            "watch_count": n_watch,
            "abstain_count": n_abstain,
            "normal_count": n_normal,
            "funded_teams_count": n_funded,
            "verify_data_count": n_verify,
            "mean_quality_score": round(mean_quality, 3),
            "avg_relative_uncertainty": round(avg_rel_width, 2)
        },
        "wards": wards_results
    }

@app.get("/api/ward-history/{ward_id}")
def get_ward_history(ward_id: str):
    df_w = raw_data[raw_data["ward_id"] == ward_id].copy().sort_values("date")
    if len(df_w) == 0:
        raise HTTPException(status_code=404, detail=f"Ward {ward_id} not found.")
    
    w_meta = wards_meta[wards_meta["ward_id"] == ward_id].iloc[0]
    
    # Recent 52 weeks
    recent = df_w.tail(52).copy()
    history = []
    for _, r in recent.iterrows():
        history.append({
            "date": str(r["date"])[:10],
            "reported_cases": float(r["reported_cases"]) if not pd.isna(r["reported_cases"]) else None,
            "rainfall_mm": float(r["rainfall_mm"]) if "rainfall_mm" in r and not pd.isna(r["rainfall_mm"]) else 0.0,
            "temp_c": float(r["temp_c"]) if "temp_c" in r and not pd.isna(r["temp_c"]) else 28.0,
            "humidity_pct": float(r["humidity_pct"]) if "humidity_pct" in r and not pd.isna(r["humidity_pct"]) else 70.0
        })
        
    return {
        "ward_id": ward_id,
        "ward_name": str(w_meta["ward_name"]),
        "population": int(w_meta["population"]),
        "lat": float(w_meta["lat"]),
        "lon": float(w_meta["lon"]),
        "history": history
    }

@app.get("/api/evaluation-benchmarks")
def get_evaluation_benchmarks():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    summary_path = os.path.join(base_dir, "results", "evaluation_summary.csv")
    if os.path.exists(summary_path):
        df_sum = pd.read_csv(summary_path)
        return df_sum.replace({np.nan: None}).to_dict(orient="records")
    return []

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

# Root Landing Page: Serve the KV Freight 3D Globe Hero
@app.get("/")
def get_landing():
    landing_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if os.path.exists(landing_path):
        with open(landing_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>AegisVector AI Landing</h1>")

# Mount React GIS Dashboard at /app
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/app", StaticFiles(directory=frontend_dist, html=True), name="app_static")
    # Also mount static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets_static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

