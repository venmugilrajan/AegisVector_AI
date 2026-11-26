import os
import json
import pickle
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from src.data import load_ward_data
from src.quality import DataQualityScorer
from src.features import build_features_and_targets
from src.forecast import QuantileXGBoostForecaster, BaselineForecasters
from src.conformal import SplitConformalCalibrator
from src.decision import DecisionEngine
from src.prioritise import ResourcePrioritiser

# Page Configuration
st.set_page_config(
    page_title="AegisVector AI | Uncertainty-Aware Dengue Outbreak Forecasting",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Projector Styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .metric-card {
        background-color: #1a1f2c;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .badge-alert {
        background-color: #d32f2f;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-watch {
        background-color: #f57c00;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-abstain {
        background-color: #7b1fa2;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .badge-normal {
        background-color: #388e3c;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .synthetic-banner {
        background-color: #ff9800;
        color: #000;
        padding: 10px 18px;
        border-radius: 6px;
        font-weight: 700;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_all_artifacts():
    base_dir = os.path.dirname(__file__)
    models_dir = os.path.join(base_dir, "models")
    artifacts_path = os.path.join(models_dir, "aegis_artifacts.pkl")
    with open(artifacts_path, "rb") as f:
        artifacts = pickle.load(f)
    return artifacts

@st.cache_data
def get_cached_raw_data():
    return load_ward_data()

# Load Core Data
df_raw, metadata, wards_meta = get_cached_raw_data()
artifacts = load_all_artifacts()

q_forecaster = artifacts["q_forecaster"]
conformal = artifacts["conformal"]
feature_cols = artifacts["feature_cols"]

# App Header
st.title("🛡️ AegisVector AI")
st.markdown("### Uncertainty-Aware Dengue Outbreak Forecasting & Resource Prioritisation")
st.markdown("**Knowing when NOT to trust ML: Conformal Prediction Intervals & Data Quality Abstain Gates**")

# Synthetic Data Banner
if metadata.get("is_synthetic", True):
    st.markdown("""
    <div class="synthetic-banner">
        ⚠️ <strong>DEMONSTRATION NOTICE:</strong> Running on realistic synthetic ward-level surveillance dataset (30 wards, 6 years, monsoon seasonality, reporting delays & gaps). Conformal coverage and pipeline logic are strictly verified.
    </div>
    """, unsafe_allow_html=True)

# Sidebar Controls
st.sidebar.header("🕹️ Simulation & Policy Controls")

# Horizon Selector
horizon = st.sidebar.radio(
    "Forecast Horizon",
    options=[2, 4, 6],
    index=1,
    format_func=lambda h: f"{h} Weeks Ahead ({'Rapid Response' if h==2 else 'Mid-Term Planning' if h==4 else 'Strategic Vector Control'})"
)

# Budget Slider
budget_teams = st.sidebar.slider(
    "Intervention Resource Budget (Teams)",
    min_value=1,
    max_value=25,
    value=8,
    help="Number of active vector control response teams available for deployment across wards."
)

# Live Data Degradation Slider (Simulating Broken Surveillance)
st.sidebar.markdown("---")
st.sidebar.subheader("📉 Surveillance Stress Test")
mask_pct = st.sidebar.slider(
    "Simulate Live Data Missingness / Reporting Outage",
    min_value=0,
    max_value=70,
    value=0,
    step=5,
    help="Artificially drops weekly ward reports to simulate reporting breakdown and test system's abstain mechanism."
)

# Date Selection
dates = np.sort(pd.to_datetime(df_raw["date"]).unique())
selected_date = st.sidebar.select_slider(
    "Surveillance Week (Time Machine)",
    options=dates,
    value=dates[-15],
    format_func=lambda d: pd.to_datetime(d).strftime("%Y-%m-%d")
)

# Data Processing with optional live masking
@st.cache_data
def process_data_at_slice(current_date, mask_level=0):
    df_sim = df_raw.copy()
    if mask_level > 0:
        np.random.seed(42 + int(mask_level * 10))
        # Mask only up to selected_date
        mask = (np.random.uniform(0, 100, size=len(df_sim)) < mask_level) & (pd.to_datetime(df_sim["date"]) <= current_date)
        df_sim.loc[mask, "reported_cases"] = np.nan

    scorer = DataQualityScorer()
    df_scored = scorer.score_dataset(df_sim, case_col="reported_cases")
    featured_df, _ = build_features_and_targets(df_scored, wards_meta, horizons=[2, 4, 6])
    return featured_df

featured_df = process_data_at_slice(selected_date, mask_pct)

# Slice for current evaluation week
current_slice = featured_df[featured_df["date"] == selected_date].copy().reset_index(drop=True)
if len(current_slice) == 0:
    st.error("No data found for selected week.")
    st.stop()

# Generate Forecasts & Intervals
X_curr = current_slice[feature_cols]
raw_preds = q_forecaster.predict(X_curr, horizon=horizon)
intervals = conformal.predict_interval(raw_preds, horizon=horizon)

current_slice["lower"] = intervals["lower"]
current_slice["point"] = intervals["point"]
current_slice["upper"] = intervals["upper"]
current_slice["interval_width"] = intervals["interval_width"]

# Tri-state Decision
decision_engine = DecisionEngine(
    risk_alert_threshold=25.0,
    risk_watch_threshold=12.0,
    max_rel_width=1.5,
    min_quality_score=0.65
)
current_slice["confidence_status"] = decision_engine.classify_dataframe(current_slice)

# Resource Prioritisation
prioritiser = ResourcePrioritiser(default_budget_teams=budget_teams)
allocated_slice = prioritiser.allocate(
    current_slice,
    budget_teams=budget_teams,
    risk_col="point",
    pop_col="population",
    status_col="confidence_status",
    ward_col="ward_id"
)

# Merge geographical metadata
allocated_slice = allocated_slice.merge(wards_meta[["ward_id", "lat", "lon", "ward_name"]], on="ward_id", how="left")

# Top KPI Summary Cards
n_alert = (allocated_slice["confidence_status"] == "Alert").sum()
n_watch = (allocated_slice["confidence_status"] == "Watch").sum()
n_abstain = (allocated_slice["confidence_status"] == "Insufficient confidence").sum()
n_normal = (allocated_slice["confidence_status"] == "Normal").sum()
funded_count = allocated_slice["funded"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("🚨 Alert Wards", n_alert, help="High risk & high predictive confidence")
with c2:
    st.metric("👀 Watch Wards", n_watch, help="Moderate risk with narrow interval")
with c3:
    st.metric("⚠️ Abstain / Low Conf.", n_abstain, help="System abstaining due to wide intervals or low data quality", delta=f"{int(n_abstain/30*100)}% of city" if n_abstain>0 else None, delta_color="inverse")
with c4:
    st.metric("🛡️ Funded Teams", f"{funded_count} / {budget_teams}", help="Confident wards assigned active mitigation teams")
with c5:
    avg_quality = allocated_slice["quality_score"].mean() * 100
    st.metric("📊 Mean Data Quality", f"{avg_quality:.1f}%", delta=f"-{mask_pct}% missing" if mask_pct>0 else "Good")

st.markdown("---")

# Main Layout: 2 Columns (Map & Priority Table)
col_left, col_right = st.columns([1.1, 1.0])

with col_left:
    st.subheader(f"🗺️ Spatial Ward Risk Map ({horizon}-Week Horizon)")
    
    # Folium Map
    city_center = [wards_meta["lat"].mean(), wards_meta["lon"].mean()]
    m = folium.Map(location=city_center, zoom_start=12, tiles="CartoDB dark_matter")
    
    # Status to Color
    status_color_map = {
        "Alert": "#e53935",
        "Watch": "#fb8c00",
        "Insufficient confidence": "#8e24aa",
        "Normal": "#43a047"
    }

    for _, row in allocated_slice.iterrows():
        color = status_color_map[row["confidence_status"]]
        status_text = row["confidence_status"]
        is_funded = "✅ FUNDED" if row["funded"] else "❌ Unfunded"
        
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 200px;">
            <h4 style="margin: 0 0 5px 0;">{row['ward_name']}</h4>
            <b>Status:</b> <span style="color:{color}; font-weight:bold;">{status_text}</span><br>
            <b>Action:</b> {row['action']}<br>
            <b>Deployment:</b> {is_funded}<br>
            <b>Point Forecast:</b> {row['point']:.1f} cases<br>
            <b>90% Interval:</b> [{row['lower']:.1f}, {row['upper']:.1f}]<br>
            <b>Data Quality:</b> {row['quality_score']*100:.0f}%<br>
            <b>Population:</b> {row['population']:,}
        </div>
        """
        
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9 + (row["point"] / 8.0),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=3 if row["funded"] else 1,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['ward_id']}: {status_text} | Pred: {row['point']:.0f} [{row['lower']:.0f}-{row['upper']:.0f}]"
        ).add_to(m)

    st_folium(m, height=480, width=None)
    st.caption("🔴 Red: Alert | 🟠 Orange: Watch | 🟣 Purple: Insufficient Confidence (Abstain) | 🟢 Green: Normal | Thick border: Funded")

with col_right:
    st.subheader("📋 Gated Resource Prioritisation Table")
    
    # Priority display table
    display_df = allocated_slice[[
        "rank", "ward_id", "confidence_status", "point", "lower", "upper", 
        "quality_score", "action", "funded"
    ]].copy()
    
    display_df["point"] = display_df["point"].round(1)
    display_df["90% Interval"] = display_df.apply(lambda r: f"[{r['lower']:.1f} - {r['upper']:.1f}]", axis=1)
    display_df["Quality"] = (display_df["quality_score"] * 100).round(0).astype(int).astype(str) + "%"
    display_df["Deployment"] = display_df["funded"].apply(lambda f: "✅ Funded" if f else "No")
    
    # Style confidence column
    st.dataframe(
        display_df[["rank", "ward_id", "confidence_status", "point", "90% Interval", "Quality", "action", "Deployment"]],
        column_config={
            "rank": st.column_config.NumberColumn("Rank", width="small"),
            "ward_id": st.column_config.TextColumn("Ward", width="small"),
            "confidence_status": st.column_config.TextColumn("Decision Gate", width="medium"),
            "point": st.column_config.NumberColumn(f"Risk ({horizon}w)", format="%.1f"),
            "action": st.column_config.TextColumn("Prescribed Action", width="large"),
            "Deployment": st.column_config.TextColumn("Budget", width="small"),
        },
        hide_index=True,
        height=480
    )

st.markdown("---")

# Lower Section: Ward Forecast Breakdown & Data Quality Alert Panel
col_ts, col_qual = st.columns([1.3, 0.7])

with col_ts:
    st.subheader("📈 Time Series & Conformal 90% Prediction Band")
    selected_ward = st.selectbox(
        "Select Ward to inspect trajectory:",
        options=wards_meta["ward_id"].tolist(),
        format_func=lambda w: f"{w} ({wards_meta.loc[wards_meta['ward_id']==w, 'ward_name'].values[0]})"
    )
    
    ward_hist = featured_df[featured_df["ward_id"] == selected_ward].sort_values("date").reset_index(drop=True)
    # Filter recent 52 weeks up to selected date + horizon
    sub_hist = ward_hist[pd.to_datetime(ward_hist["date"]) <= selected_date].tail(30).copy()
    
    fig = go.Figure()
    
    # Historical Reported Cases
    fig.add_trace(go.Scatter(
        x=sub_hist["date"],
        y=sub_hist["reported_cases"],
        name="Reported Cases",
        mode="lines+markers",
        line=dict(color="#42a5f5", width=2.5),
        marker=dict(size=6)
    ))
    
    # True Cases (ground truth)
    fig.add_trace(go.Scatter(
        x=sub_hist["date"],
        y=sub_hist["true_cases"],
        name="True Cases (Ground Truth)",
        mode="lines",
        line=dict(color="#78909c", width=1.5, dash="dash")
    ))
    
    # Forecast point & interval at selected date
    curr_ward_row = allocated_slice[allocated_slice["ward_id"] == selected_ward].iloc[0]
    future_date = pd.to_datetime(selected_date) + pd.Timedelta(weeks=horizon)
    
    fc_dates = [pd.to_datetime(selected_date), future_date]
    fc_points = [sub_hist["reported_cases"].iloc[-1], curr_ward_row["point"]]
    
    # Forecast line
    fig.add_trace(go.Scatter(
        x=fc_dates,
        y=fc_points,
        name=f"Forecast ({horizon}w)",
        mode="lines+markers",
        line=dict(color="#ffca28", width=3, dash="dot"),
        marker=dict(size=8, symbol="diamond")
    ))
    
    # Conformal Interval Upper and Lower
    fig.add_trace(go.Scatter(
        x=[future_date, future_date],
        y=[curr_ward_row["lower"], curr_ward_row["upper"]],
        name="90% Conformal Interval",
        mode="lines+markers",
        line=dict(color="#ab47bc", width=5),
        marker=dict(size=10, symbol="line-ew")
    ))
    
    fig.update_layout(
        title=f"Surveillance Trajectory & Calibrated Interval for {selected_ward} (Quality: {curr_ward_row['quality_score']*100:.0f}%)",
        xaxis_title="Date",
        yaxis_title="Weekly Cases",
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", y=1.1, x=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_qual:
    st.subheader("⚠️ Data Quality & Abstain Watchlist")
    
    # Filter wards with issues
    low_qual_wards = allocated_slice[
        (allocated_slice["quality_score"] < 0.70) | 
        (allocated_slice["confidence_status"] == "Insufficient confidence")
    ].sort_values("quality_score")
    
    if len(low_qual_wards) == 0:
        st.success("✅ All 30 wards currently meet data quality standards (> 70%) and have narrow prediction bounds.")
    else:
        st.warning(f"🚨 {len(low_qual_wards)} ward(s) flagged for surveillance issues or high epistemic uncertainty.")
        for _, w in low_qual_wards.iterrows():
            st.markdown(f"""
            <div style="background:#26182c; padding:10px; border-radius:6px; margin-bottom:8px; border-left:4px solid #ba68c8;">
                <b>{w['ward_id']} ({w['ward_name']})</b><br>
                <span>Quality Score: <b>{w['quality_score']*100:.0f}%</b> | Status: <b style="color:#ce93d8;">{w['confidence_status']}</b></span><br>
                <span>Point Risk: <b>{w['point']:.1f}</b> | 90% Band: <b>[{w['lower']:.1f} - {w['upper']:.1f}]</b></span><br>
                <span>Action: <b style="color:#ffb74d;">{w['action']}</b></span>
            </div>
            """, unsafe_allow_html=True)
            
    st.info("💡 **Why Abstain?** In high-stakes public health, a false sense of security or poorly targeted spraying exhausts municipal supplies. AegisVector flags low-confidence wards for physical surveillance audits before authorizing chemical fogging.")

# Footer with evaluation preview
st.markdown("---")
st.markdown("### 🔬 Rigorous Historical Replay Benchmarks")
results_summary_path = os.path.join(os.path.dirname(__file__), "results", "evaluation_summary.csv")
if os.path.exists(results_summary_path):
    summary_df = pd.read_csv(results_summary_path)
    # Display 4-week horizon at 30% masking
    bench = summary_df[(summary_df["horizon"] == 4) & (summary_df["masking"] == 0.3)].copy()
    st.dataframe(
        bench[["model", "coverage_mean", "precision_mean", "false_alarm_rate_mean", "wasted_interventions_mean", "abstain_rate_mean"]],
        column_config={
            "model": "Model",
            "coverage_mean": st.column_config.NumberColumn("Conformal Coverage", format="%.2f"),
            "precision_mean": st.column_config.NumberColumn("Alert Precision", format="%.2f"),
            "false_alarm_rate_mean": st.column_config.NumberColumn("False Alarm Rate", format="%.3f"),
            "wasted_interventions_mean": st.column_config.NumberColumn("Wasted Teams (Weekly)", format="%.1f"),
            "abstain_rate_mean": st.column_config.NumberColumn("Abstain Rate", format="%.2f"),
        },
        hide_index=True
    )
else:
    st.caption("Evaluation summary table is generating in the background...")
