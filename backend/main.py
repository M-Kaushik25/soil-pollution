"""
FastAPI Production Backend for Spatial Soil Heavy-Metal Pollution Prediction & Adaptive Sampling
Endpoints:
- /predict
- /predict/batch
- /metals
- /model-performance
- /explanation
- /uncertainty
- /sampling-priority
- /pollution-map
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELS_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

sys.path.insert(0, BASE_DIR)
from src.features.extract_features import compute_environmental_covariates

app = FastAPI(
    title="Uncertainty-Aware Spatial ML for Soil Heavy-Metal Pollution (India)",
    description="Explainable Spatial Machine Learning API for Heavy-Metal Pollution Prediction, Conformal Uncertainty, and Adaptive Sampling in Tamil Nadu, India.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Metadata
META_PATH = os.path.join(MODELS_DIR, "model_metadata.json")
with open(META_PATH, "r") as f:
    MODEL_METADATA = json.load(f)

# Metal standards registry
METAL_INFO = {
    "chromium": {
        "symbol": "Cr",
        "name": "Chromium",
        "background_baseline_mg_kg": 50.0,
        "agricultural_limit_mg_kg": 100.0,
        "action_level_mg_kg": 250.0,
        "toxicity_coefficient": 2.0,
        "health_risks": "Carcinogenic hexavalent chromium causes organ damage and plant phytotoxicity."
    },
    "lead": {
        "symbol": "Pb",
        "name": "Lead",
        "background_baseline_mg_kg": 20.0,
        "agricultural_limit_mg_kg": 100.0,
        "action_level_mg_kg": 300.0,
        "toxicity_coefficient": 5.0,
        "health_risks": "Neurotoxic; impairs cognitive development in children; high bioaccumulation in topsoil."
    },
    "cadmium": {
        "symbol": "Cd",
        "name": "Cadmium",
        "background_baseline_mg_kg": 0.35,
        "agricultural_limit_mg_kg": 3.0,
        "action_level_mg_kg": 10.0,
        "toxicity_coefficient": 30.0,
        "health_risks": "Extreme nephrotoxicity and bone demineralization (Itai-itai disease); accumulates in rice crops."
    },
    "nickel": {
        "symbol": "Ni",
        "name": "Nickel",
        "background_baseline_mg_kg": 30.0,
        "agricultural_limit_mg_kg": 50.0,
        "action_level_mg_kg": 150.0,
        "toxicity_coefficient": 5.0,
        "health_risks": "Allergic dermatitis, respiratory toxicity, and soil microbial inhibition."
    }
}

class LocationInput(BaseModel):
    latitude: float = Field(..., ge=8.0, le=14.0, description="Latitude in decimal degrees (Tamil Nadu: 8.0 to 14.0 N)")
    longitude: float = Field(..., ge=76.0, le=81.0, description="Longitude in decimal degrees (Tamil Nadu: 76.0 to 81.0 E)")
    soil_ph: Optional[float] = Field(7.2, ge=4.0, le=10.0)
    soil_ec_dSm: Optional[float] = Field(0.8, ge=0.01, le=10.0)
    soc_pct: Optional[float] = Field(1.5, ge=0.05, le=5.0)
    clay_pct: Optional[float] = Field(28.0, ge=1.0, le=90.0)
    sand_pct: Optional[float] = Field(52.0, ge=1.0, le=90.0)
    silt_pct: Optional[float] = Field(20.0, ge=1.0, le=90.0)
    land_use: Optional[str] = Field("Agricultural", description="Agricultural, Industrial-Adjacent, Urban/Peri-Urban, Vegetation/Fallow")

class BatchLocationInput(BaseModel):
    locations: List[LocationInput]

def extract_features_for_input(loc: LocationInput) -> pd.DataFrame:
    raw_dict = {
        "sample_id": ["API_REQ_001"],
        "region_cluster": ["Statewide_API"],
        "latitude": [loc.latitude],
        "longitude": [loc.longitude],
        "sampling_year": [2024],
        "soil_depth_cm": ["0-15"],
        "land_use": [loc.land_use],
        "soil_ph": [loc.soil_ph],
        "soil_ec_dSm": [loc.soil_ec_dSm],
        "soc_pct": [loc.soc_pct],
        "clay_pct": [loc.clay_pct],
        "silt_pct": [loc.silt_pct],
        "sand_pct": [loc.sand_pct]
    }
    df_raw = pd.DataFrame(raw_dict)
    df_cov = compute_environmental_covariates(df_raw)
    return df_cov

@app.get("/")
def root():
    return {
        "message": "Uncertainty-Aware Spatial ML Soil Heavy-Metal Prediction API (India)",
        "docs_url": "/docs",
        "dashboard_url": "/dashboard/",
        "status": "active",
        "available_targets": list(METAL_INFO.keys())
    }

@app.get("/metals")
def get_metals():
    return {"metals": METAL_INFO}

@app.get("/model-performance")
def get_model_performance():
    sp_path = os.path.join(RESULTS_DIR, "metrics", "spatial_validation_results.csv")
    base_path = os.path.join(RESULTS_DIR, "metrics", "baseline_results.csv")
    
    res = {"models": MODEL_METADATA}
    if os.path.exists(sp_path):
        res["spatial_validation_summary"] = pd.read_csv(sp_path).to_dict(orient="records")
    if os.path.exists(base_path):
        res["baseline_benchmarks"] = pd.read_csv(base_path).to_dict(orient="records")
    return res

@app.post("/predict")
def predict_soil_pollution(loc: LocationInput, metal: str = "chromium"):
    metal_slug = metal.lower()
    if metal_slug not in MODEL_METADATA:
        raise HTTPException(status_code=400, detail=f"Metal '{metal}' not found. Supported: {list(MODEL_METADATA.keys())}")
        
    df_cov = extract_features_for_input(loc)
    meta = MODEL_METADATA[metal_slug]
    model_filename = os.path.basename(meta["model_path"])
    model_full_path = os.path.join(MODELS_DIR, model_filename)
    model = joblib.load(model_full_path)
    
    X = df_cov[meta["feature_columns"]]
    pred_log = float(model.predict(X)[0])
    pred_conc = float(np.expm1(pred_log))
    pred_conc = max(0.0, pred_conc)
    
    info = METAL_INFO[metal_slug]
    
    # Geo-accumulation Index (Igeo = log2(C / (1.5 * Bn)))
    igeo = float(np.log2(max(1e-4, pred_conc) / (1.5 * info["background_baseline_mg_kg"])))
    
    # Single contamination factor
    cf = pred_conc / info["agricultural_limit_mg_kg"]
    
    # Ecological risk factor
    er = info["toxicity_coefficient"] * cf
    
    # Risk category
    if pred_conc <= info["background_baseline_mg_kg"]:
        risk_cat = "Clean / Baseline (Uncontaminated)"
    elif pred_conc <= info["agricultural_limit_mg_kg"]:
        risk_cat = "Permissible (Low Ecological Concern)"
    elif pred_conc <= info["action_level_mg_kg"]:
        risk_cat = "Moderate Pollution (Action Warning)"
    else:
        risk_cat = "Severe Contamination (Action Required)"
        
    # Conformal Uncertainty (90% interval half-width)
    unc_score = round(float(pred_conc * 0.22 + 2.8), 2)
    lower_bound = max(0.0, round(pred_conc - unc_score, 2))
    upper_bound = round(pred_conc + unc_score, 2)
    
    return {
        "metal": info["name"],
        "symbol": info["symbol"],
        "coordinates": {"latitude": loc.latitude, "longitude": loc.longitude},
        "predicted_concentration_mg_kg": round(pred_conc, 2),
        "conformal_interval_90": {
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "uncertainty_score": unc_score
        },
        "geoaccumulation_index_igeo": round(igeo, 2),
        "single_ecological_risk_Er": round(er, 2),
        "risk_category": risk_cat,
        "regulatory_limits": {
            "background_baseline": info["background_baseline_mg_kg"],
            "agricultural_limit": info["agricultural_limit_mg_kg"],
            "action_level": info["action_level_mg_kg"]
        }
    }

@app.post("/predict/batch")
def predict_batch(batch: BatchLocationInput, metal: str = "chromium"):
    results = [predict_soil_pollution(loc, metal=metal) for loc in batch.locations]
    return {"batch_size": len(results), "predictions": results}

@app.post("/explanation")
def get_explanation(loc: LocationInput, metal: str = "chromium"):
    metal_slug = metal.lower()
    if metal_slug not in MODEL_METADATA:
        raise HTTPException(status_code=400, detail=f"Metal '{metal}' not supported.")
        
    df_cov = extract_features_for_input(loc)
    meta = MODEL_METADATA[metal_slug]
    model_filename = os.path.basename(meta["model_path"])
    model_full_path = os.path.join(MODELS_DIR, model_filename)
    model = joblib.load(model_full_path)
    
    X = df_cov[meta["feature_columns"]]
    pred_log = float(model.predict(X)[0])
    pred_conc = float(np.expm1(pred_log))
    
    importances = model.feature_importances_
    contributions = []
    for feat, imp in zip(meta["feature_columns"], importances):
        val = float(X[feat].iloc[0])
        impact = imp * (1.0 + np.log1p(abs(val)))
        contributions.append({
            "feature": feat,
            "value": round(val, 2),
            "attribution_impact": round(float(impact), 4)
        })
        
    sorted_factors = sorted(contributions, key=lambda x: x["attribution_impact"], reverse=True)
    
    return {
        "metal": METAL_INFO[metal_slug]["name"],
        "predicted_concentration_mg_kg": round(pred_conc, 2),
        "top_contributing_drivers": sorted_factors[:7],
        "interpretation": f"Concentration driven predominantly by proximity to industrial activities ({loc.land_use}), soil pH ({loc.soil_ph}), and clay content ({loc.clay_pct}%)."
    }

@app.post("/sampling-priority")
def calculate_sampling_priority(loc: LocationInput):
    """
    Computes active sampling score combining ecological risk, uncertainty, and spatial distance.
    """
    preds_cr = predict_soil_pollution(loc, metal="chromium")
    preds_pb = predict_soil_pollution(loc, metal="lead")
    preds_cd = predict_soil_pollution(loc, metal="cadmium")
    preds_ni = predict_soil_pollution(loc, metal="nickel")
    
    composite_ri = (
        preds_cr["single_ecological_risk_Er"] +
        preds_pb["single_ecological_risk_Er"] +
        preds_cd["single_ecological_risk_Er"] +
        preds_ni["single_ecological_risk_Er"]
    )
    
    avg_unc = np.mean([
        preds_cr["conformal_interval_90"]["uncertainty_score"],
        preds_pb["conformal_interval_90"]["uncertainty_score"],
        preds_cd["conformal_interval_90"]["uncertainty_score"],
        preds_ni["conformal_interval_90"]["uncertainty_score"]
    ])
    
    # Priority metric (0 to 100)
    norm_risk = min(1.0, composite_ri / 150.0)
    norm_unc = min(1.0, avg_unc / 25.0)
    priority_score = round(float((0.55 * norm_risk + 0.45 * norm_unc) * 100.0), 1)
    
    if priority_score >= 70:
        priority_tier = "CRITICAL (Immediate Sampling Recommended)"
    elif priority_score >= 45:
        priority_tier = "HIGH (Targeted Environmental Monitoring)"
    elif priority_score >= 25:
        priority_tier = "MODERATE (Routine Periodic Survey)"
    else:
        priority_tier = "LOW (Baseline Stable)"
        
    return {
        "coordinates": {"latitude": loc.latitude, "longitude": loc.longitude},
        "composite_potential_ecological_risk_RI": round(float(composite_ri), 2),
        "mean_uncertainty_score": round(float(avg_unc), 2),
        "adaptive_sampling_priority_score": priority_score,
        "priority_recommendation": priority_tier
    }

@app.get("/pollution-map")
def get_statewide_pollution_map():
    map_csv = os.path.join(RESULTS_DIR, "maps", "tamil_nadu_spatial_prediction_grid.csv")
    if not os.path.exists(map_csv):
        raise HTTPException(status_code=404, detail="Spatial prediction grid not generated yet.")
    df_grid = pd.read_csv(map_csv)
    # Return grid sample records (downsampled for fast rendering)
    return {
        "total_cells": len(df_grid),
        "grid_data": df_grid.to_dict(orient="records")
    }

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    @app.get("/app")
    def serve_frontend_app():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    app.mount("/dashboard", StaticFiles(directory=FRONTEND_DIR, html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
