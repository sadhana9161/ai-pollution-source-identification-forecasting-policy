'''  FastAPI app  '''

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import math
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select # backend/app/main.py
from app.data_gen import generate_synthetic_observations # synthetic data generate
from app.db import engine, SessionLocal  # database engine and session
from app.models import Base, Observation  # SQLAI chemy modeals
import app.train as train_module   # training module
import app.predict as pred     # prediction module
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="AI-Driven Pollution Forecast & Policy API")
 # allow frontend js fetch calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Allows requests from any origin
    allow_methods=["*"],    # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],      # Allows all headers
)
# Serve frontend folder at root URL
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Ensure tables exist
Base.metadata.create_all(bind=engine)



def ingest_csv_to_db(csv_path: str):
    df = pd.read_csv(csv_path)
    session = SessionLocal()
    for _, row in df.iterrows():
        obs = Observation(
            timestamp_utc=row["timestamp_utc"],
            station_id=row["station_id"],
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            aod=float(row["aod"]),
            hotspots=int(row["hotspots"]),
            traffic_index=float(row["traffic_index"]),
            industry_index=float(row["industry_index"]),
            temp_c=float(row["temp_c"]),
            rh=float(row["rh"]),
            wind_speed=float(row["wind_speed"]),
            pm25=float(row["pm25"]),
            stubble_frac=float(row["stubble_frac"]),
            traffic_frac=float(row["traffic_frac"]),
            industry_frac=float(row["industry_frac"]),
        )
        session.add(obs)
    session.commit()
    session.close()
app = FastAPI()
@app.post("/ingest/synthetic")
def ingest_synthetic():
    try:
        df = generate_synthetic_observations()

        if df.empty:
            raise ValueError("Generated DataFrame is empty.")

        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(data_dir, exist_ok=True)
        csv_path = os.path.join(data_dir, "observations.csv")

        df.to_csv(csv_path, index=False)

        rows_ingested = ingest_csv_to_db(csv_path)

        return {"status": "ok", "rows": len(df), "ingested": rows_ingested}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
def train_all():
    try:
        train_module.train_models()
        return {"status": "trained"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Policy Recommendation Function

def policy_recommendation(source: dict):
    policies = []

    #  Traffic-related pollution
    if source.get("traffic_frac", 0) > 0.4:
        policies.append("Implement stricter vehicle emission norms")
        policies.append("Promote public transport and EV adoption")

    #  Stubble burning-related pollution
    if source.get("stubble_frac", 0) > 0.3:
        policies.append("Promote in-situ stubble management technologies")
        policies.append("Provide incentives for bio-decomposers and crop diversification")

    #  Industrial pollution
    if source.get("industry_frac", 0) > 0.3:
        policies.append("Enforce industrial emission control measures")
        policies.append("Install real-time emission monitoring in factories")

    #  If pollution is mixed
    if not policies:
        policies.append("Maintain current pollution control measures")
        policies.append("Continue monitoring air quality regularly")

    return policies

#  Function: AQI Category
def aqi_category(pm):
    if pm <= 50:
        return "Good"
    if pm <= 100:
        return "Moderate"
    if pm <= 250:
        return "Unhealthy"
    if pm <= 350:
        return "Very Unhealthy"
    return "Hazardous"



@app.get("/aqi")  # api get location
def get_aqi(lat: float, lon: float):
    session = SessionLocal()
    rows = session.execute(select(Observation)).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No observations found. Run /ingest/synthetic first.")

    def dist(r):
        return math.hypot(r.lat - lat, r.lon - lon)

    nearest = min(rows, key=lambda r: dist(r, (lat, lon)))
# Features for prediction
    feature = {
        "aod": nearest.aod,
        "hotspots": nearest.hotspots,
        "traffic_index": nearest.traffic_index,
        "industry_index": nearest.industry_index,
        "temp_c": nearest.temp_c,
        "rh": nearest.rh,
        "wind_speed": nearest.wind_speed
    }
    pm25 = float(nearest.pm25)
 # Predict source attribution
    try:
        attrib = pred.predict_attribution(feature)
    except Exception:
        attrib = {
            "stubble_frac": nearest.stubble_frac,
            "traffic_frac": nearest.traffic_frac,
            "industry_frac": nearest.industry_frac
        }

 # Generate policy recommendations
    policy = policy_recommendation(attrib)

    session.close()
    return {
        "lat": nearest.lat,
        "lon": nearest.lon,
        "pm25": pm25,
        "aqi_category": aqi_category(pm25),
        "source_contribution": attrib,
        "policy_recommendations": policy
    }


@app.get("/forecast")
def forecast(lat: float, lon: float, hours: int = 24):
    session = SessionLocal()
    rows = session.execute(select(Observation)).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No observations found. Run /ingest/synthetic first.")

    def dist(r):
        return math.hypot(r.lat - lat, r.lon - lon)

    nearest = min(rows, key=lambda r: dist(r, (lat, lon)))
    
    base_feature = {
        "aod": nearest.aod,
        "hotspots": nearest.hotspots,
        "traffic_index": nearest.traffic_index,
        "industry_index": nearest.industry_index,
        "temp_c": nearest.temp_c,
        "rh": nearest.rh,
        "wind_speed": nearest.wind_speed
    }

    try:
        pm_model, attr_model = pred.load_models()
    except Exception:
        pm_model = None
        attr_model = None

    forecasts = []
    import datetime
    now = datetime.datetime.fromisoformat(nearest.timestamp_utc)

    for h in range(1, hours + 1):
        feat = base_feature.copy()
        feat["aod"] = max(0.01, feat["aod"] * (1 + 0.05 * math.sin(2 * math.pi * (h / 24))))
        if pm_model:
            pm_pred = float(pm_model.predict(pd.DataFrame([feat])[pred._feature_cols])[0])
            attr = pred.predict_attribution(feat)
        else:
            pm_pred = float(nearest.pm25)
            attr = {
                "stubble_frac": nearest.stubble_frac,
                "traffic_frac": nearest.traffic_frac,
                "industry_frac": nearest.industry_frac
            }
        forecasts.append({
            "timestamp": (now + datetime.timedelta(hours=h)).isoformat(),
            "pm25": pm_pred,
            "aqi_category": aqi_category(pm_pred),
            "source_contribution": attr,
            "policy_recommendations": policy_recommendation(attr)
        })

    session.close()
    return {"forecasts": forecasts}  

