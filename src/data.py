import os
import json
import logging
import numpy as np
import pandas as pd
import requests
from datetime import datetime, timedelta

DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
DATA_PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

METADATA_FILE = os.path.join(DATA_RAW_DIR, "data_source_metadata.json")

def downscale_district_data_to_wards(district_df: pd.DataFrame, wards_meta: pd.DataFrame) -> pd.DataFrame:
    """
    Downscales district-level weekly dengue cases to ward-level using population + weather weights:
    W_w = (Pop_w / Pop_total) * (Weather_Vulnerability_w)
    Normalized so sum(W_w) == 1.
    """
    total_pop = wards_meta["population"].sum()
    pop_shares = wards_meta.set_index("ward_id")["population"] / total_pop
    vuln_shares = wards_meta.set_index("ward_id")["vulnerability"]
    
    combined_weights = pop_shares * vuln_shares
    norm_weights = combined_weights / combined_weights.sum()

    records = []
    for _, row in district_df.iterrows():
        d_date = row["date"]
        d_cases = float(row["cases"])
        rain = float(row.get("rainfall", 25.0))
        temp = float(row.get("temperature", 29.0))
        humid = float(row.get("humidity", 75.0))

        for w_id, w_weight in norm_weights.items():
            w_meta = wards_meta[wards_meta["ward_id"] == w_id].iloc[0]
            ward_cases = np.random.poisson(lam=max(0.0, d_cases * w_weight))
            records.append({
                "date": d_date,
                "ward_id": w_id,
                "reported_cases": float(ward_cases),
                "true_cases": int(ward_cases),
                "rainfall": round(rain + np.random.normal(0, 3.0), 2),
                "temperature": round(temp + np.random.normal(0, 0.5), 2),
                "humidity": round(np.clip(humid + np.random.normal(0, 2.0), 40, 99), 2),
                "population": int(w_meta["population"])
            })

    return pd.DataFrame(records)

def generate_synthetic_dataset(
    n_wards=30,
    n_years=6,
    start_date="2018-01-01",
    seed=42
):
    """
    Generates a realistic synthetic ward-level dengue dataset:
    - 30 wards with geographical coordinates around a tropical metro area
    - Ward populations (20,000 to 180,000)
    - 6 years of weekly data (~312 weeks)
    - Monsoon seasonality with dual peak (May-July and Oct-Dec)
    - Rainfall-lagged outbreaks (rainfall peak leads dengue cases by 3-5 weeks)
    - Realistic reporting artifacts: delays, batching, and missingness
    """
    np.random.seed(seed)
    weeks = pd.date_range(start=start_date, periods=n_years * 52, freq="W-MON")
    n_weeks = len(weeks)

    center_lat, center_lon = 6.9271, 79.8612
    
    wards = []
    for i in range(n_wards):
        w_id = f"W{i+1:02d}"
        angle = 2 * np.pi * i / n_wards
        radius = 0.02 + 0.08 * (i % 5) / 5.0
        lat = center_lat + radius * np.cos(angle) + np.random.normal(0, 0.005)
        lon = center_lon + radius * np.sin(angle) + np.random.normal(0, 0.005)
        pop = int(np.random.choice([25000, 45000, 70000, 110000, 160000], p=[0.2, 0.3, 0.25, 0.15, 0.1]) * np.random.uniform(0.85, 1.25))
        vulnerability = float(np.random.uniform(0.6, 1.8))
        reporting_reliability = float(np.random.choice([0.98, 0.92, 0.85, 0.70], p=[0.5, 0.3, 0.15, 0.05]))
        wards.append({
            "ward_id": w_id,
            "ward_name": f"Ward-{w_id}",
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "population": pop,
            "vulnerability": round(vulnerability, 3),
            "reporting_reliability": reporting_reliability
        })
    
    wards_df = pd.DataFrame(wards)
    wards_df.to_csv(os.path.join(DATA_RAW_DIR, "wards_metadata.csv"), index=False)

    records = []
    week_of_year = np.array([d.isocalendar()[1] for d in weeks])
    
    monsoon_1 = np.exp(-0.5 * ((week_of_year - 22) / 3.5) ** 2)
    monsoon_2 = np.exp(-0.5 * ((week_of_year - 44) / 4.0) ** 2)
    seasonal_rain = 15.0 + 85.0 * monsoon_1 + 110.0 * monsoon_2
    seasonal_temp = 28.5 + 2.5 * np.sin(2 * np.pi * (week_of_year - 10) / 52.0)
    seasonal_humidity = 68.0 + 18.0 * (monsoon_1 + monsoon_2) / 1.5

    for w_idx, ward in wards_df.iterrows():
        w_id = ward["ward_id"]
        vuln = ward["vulnerability"]
        pop = ward["population"]
        reliability = ward["reporting_reliability"]

        rain_noise = np.random.gamma(shape=2.0, scale=4.0, size=n_weeks)
        rainfall = np.maximum(0, seasonal_rain * np.random.uniform(0.8, 1.2) + rain_noise)
        temperature = seasonal_temp + np.random.normal(0, 0.8, size=n_weeks)
        humidity = np.clip(seasonal_humidity + np.random.normal(0, 3.0, size=n_weeks), 45, 99)

        rain_lag3 = np.roll(rainfall, 3)
        rain_lag4 = np.roll(rainfall, 4)
        rain_lag3[:4] = seasonal_rain[:4]
        rain_lag4[:4] = seasonal_rain[:4]
        
        vector_breeding_pressure = (0.5 * rain_lag3 + 0.5 * rain_lag4) / 40.0
        temp_factor = np.clip((temperature - 22.0) / 8.0, 0.4, 1.5)
        
        base_rate = (pop / 10000.0) * 1.2 * vuln
        year_multiplier = np.array([1.0 + 0.9 * (d.year in [2019, 2023]) for d in weeks])
        
        true_cases = np.zeros(n_weeks)
        current = base_rate * 1.5
        for t in range(n_weeks):
            forcing = vector_breeding_pressure[t] * temp_factor[t] * year_multiplier[t]
            transmission = 0.55 * current + 1.2 * forcing * base_rate + np.random.poisson(lam=max(0.5, base_rate * 0.4))
            current = 0.85 * current + 0.15 * transmission
            true_cases[t] = max(0, current + np.random.normal(0, np.sqrt(current + 1.0)))
        
        true_cases = np.round(true_cases).astype(int)

        reported_cases = true_cases.astype(float).copy()
        missing_mask = np.random.uniform(0, 1, size=n_weeks) > reliability
        
        delayed_buffer = 0
        for t in range(n_weeks):
            if missing_mask[t]:
                delayed_buffer += reported_cases[t]
                reported_cases[t] = np.nan
            else:
                if delayed_buffer > 0 and np.random.uniform() < 0.6:
                    reported_cases[t] += delayed_buffer
                    delayed_buffer = 0

        for t in range(n_weeks):
            records.append({
                "date": weeks[t].strftime("%Y-%m-%d"),
                "ward_id": w_id,
                "reported_cases": reported_cases[t],
                "true_cases": true_cases[t],
                "rainfall": round(rainfall[t], 2),
                "temperature": round(temperature[t], 2),
                "humidity": round(humidity[t], 2),
                "population": pop
            })

    df = pd.DataFrame(records)
    raw_path = os.path.join(DATA_RAW_DIR, "dengue_ward_weekly_synthetic.csv")
    df.to_csv(raw_path, index=False)
    
    metadata = {
        "data_source": "SYNTHETIC",
        "description": "Synthetic ward-level dengue dataset with dual monsoon seasonality, lagged rainfall dynamics, and realistic reporting artifacts (delays, missingness, batching).",
        "n_wards": n_wards,
        "n_weeks": n_weeks,
        "start_date": start_date,
        "is_synthetic": True,
        "generated_at": datetime.now().isoformat()
    }
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"[Data] Successfully generated realistic synthetic dataset: {len(df)} records across {n_wards} wards.")
    return df, metadata

def load_ward_data():
    """
    Data Source Switch:
    1. Checks if a real OpenDengue file exists at data/raw/opendengue_data.csv.
       If present, downscales from district level to wards using population + vulnerability weights.
    2. Otherwise, falls back to the realistic synthetic dataset.
    """
    opendengue_path = os.path.join(DATA_RAW_DIR, "opendengue_data.csv")
    wards_meta_path = os.path.join(DATA_RAW_DIR, "wards_metadata.csv")
    
    if os.path.exists(opendengue_path):
        print(f"[Data Source] Real OpenDengue file detected at {opendengue_path}.")
        try:
            district_df = pd.read_csv(opendengue_path)
            if not os.path.exists(wards_meta_path):
                generate_synthetic_dataset()
            wards_meta = pd.read_csv(wards_meta_path)
            
            df = downscale_district_data_to_wards(district_df, wards_meta)
            metadata = {
                "data_source": "OPENDENGUE_REAL",
                "description": "Real OpenDengue surveillance data downscaled to wards via population & vulnerability weights.",
                "n_wards": len(wards_meta),
                "n_weeks": df["date"].nunique(),
                "is_synthetic": False,
                "loaded_at": datetime.now().isoformat()
            }
            with open(METADATA_FILE, "w") as f:
                json.dump(metadata, f, indent=2)
            return df, metadata, wards_meta
        except Exception as e:
            print(f"[Data Source Warning] Failed reading OpenDengue file ({e}). Falling back to synthetic.")

    raw_path = os.path.join(DATA_RAW_DIR, "dengue_ward_weekly_synthetic.csv")
    if not os.path.exists(raw_path) or not os.path.exists(wards_meta_path):
        df, metadata = generate_synthetic_dataset()
        wards_meta = pd.read_csv(wards_meta_path)
    else:
        df = pd.read_csv(raw_path)
        with open(METADATA_FILE, "r") as f:
            metadata = json.load(f)
        wards_meta = pd.read_csv(wards_meta_path)
        
    return df, metadata, wards_meta

if __name__ == "__main__":
    load_ward_data()
