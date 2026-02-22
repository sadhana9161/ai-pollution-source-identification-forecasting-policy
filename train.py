# backend/app/train.py
''' ML model training logic '''

import os
import pandas as pd
import joblib
import numpy as np

from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

ROOT = os.path.dirname(__file__)
DATA_PATH = os.path.join(ROOT, "..", "data", "observations.csv")
MODELS_DIR = os.path.join(ROOT, "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)


def train_models():
    df = pd.read_csv(DATA_PATH)
    # Feature set
    feat_cols = ["aod", "hotspots", "traffic_index", "industry_index", "temp_c", "rh", "wind_speed"]
    X = df[feat_cols].fillna(0)
    y_pm = df["pm25"]
    y_frac = df[["stubble_frac", "traffic_frac", "industry_frac"]]

    # train pm25 regressor
    X_train, X_test, y_train, y_test = train_test_split(X, y_pm, test_size=0.2, random_state=42)
    pm_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    pm_model.fit(X_train, y_train)
    preds = pm_model.predict(X_test)
    print("PM2.5 MAE:", mean_absolute_error(y_test, preds))
    joblib.dump(pm_model, os.path.join(MODELS_DIR, "pm_model.joblib"))

    # train attribution model (multi-output regression predicting fractions)
    X2_train, X2_test, y2_train, y2_test = train_test_split(X, y_frac, test_size=0.2, random_state=42)
    base = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    attr_model = MultiOutputRegressor(base)
    attr_model.fit(X2_train, y2_train)
    preds2 = attr_model.predict(X2_test)
    print("Attribution MAE per output:", np.mean(np.abs(preds2 - y2_test), axis=0))
    joblib.dump(attr_model, os.path.join(MODELS_DIR, "attr_model.joblib"))


if __name__ == "__main__":
    train_models()
