# backend/app/predict.py
''' prediction logic '''

import os
import joblib
import numpy as np
import pandas as pd

ROOT = os.path.dirname(__file__)
MODELS_DIR = os.path.join(ROOT, "..", "models")
PM_MODEL_PATH = os.path.join(MODELS_DIR, "pm_model.joblib")
ATTR_MODEL_PATH = os.path.join(MODELS_DIR, "attr_model.joblib")

_feature_cols = ["aod", "hotspots", "traffic_index", "industry_index", "temp_c", "rh", "wind_speed"]

_pm_model = None
_attr_model = None


def load_models():
    global _pm_model, _attr_model
    if _pm_model is None:
        _pm_model = joblib.load(PM_MODEL_PATH)
    if _attr_model is None:
        _attr_model = joblib.load(ATTR_MODEL_PATH)
    return _pm_model, _attr_model


def predict_pm25(feature_dict):
    pm_model, _ = load_models()
    X = pd.DataFrame([feature_dict])[ _feature_cols ]
    return float(pm_model.predict(X)[0])


def predict_attribution(feature_dict):
    _, attr_model = load_models()
    X = pd.DataFrame([feature_dict])[ _feature_cols ]
    preds = attr_model.predict(X)[0]
    # ensure non-negative and normalized
    preds = np.maximum(preds, 0)
    s = preds.sum()
    if s <= 0:
        preds = np.array([0.33, 0.33, 0.34])
    else:
        preds = preds / s
    return {
        "stubble_frac": float(preds[0]),
        "traffic_frac": float(preds[1]),
        "industry_frac": float(preds[2]),
    }
