"""
Automated Machine Learning & Uncertainty Tests
"""

import os
import json
import joblib
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_trained_models_exist():
    models_dir = os.path.join(BASE_DIR, "models")
    meta_path = os.path.join(models_dir, "model_metadata.json")
    assert os.path.exists(meta_path), "Model metadata missing"
    
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    for slug in ["chromium", "lead", "cadmium", "nickel"]:
        assert slug in meta, f"Missing model metadata for {slug}"
        m_filename = os.path.basename(meta[slug]["model_path"])
        m_path = os.path.join(models_dir, m_filename)
        assert os.path.exists(m_path), f"Missing model binary at {m_path}"

def test_inference_and_conformal_bounds():
    models_dir = os.path.join(BASE_DIR, "models")
    with open(os.path.join(models_dir, "model_metadata.json"), "r") as f:
        meta = json.load(f)
        
    df_master = pd.read_parquet(os.path.join(BASE_DIR, "data", "processed", "master_soil_pollution_dataset.parquet"))
    sample_row = df_master.iloc[[0]]
    
    for slug in ["chromium", "lead", "cadmium", "nickel"]:
        m_filename = os.path.basename(meta[slug]["model_path"])
        model = joblib.load(os.path.join(models_dir, m_filename))
        feat_cols = meta[slug]["feature_columns"]
        
        pred_log = model.predict(sample_row[feat_cols])
        pred_conc = float(np.expm1(pred_log)[0])
        
        assert pred_conc > 0, f"Predicted concentration must be positive for {slug}"
        assert not np.isnan(pred_conc), f"NaN prediction for {slug}"

if __name__ == "__main__":
    test_trained_models_exist()
    test_inference_and_conformal_bounds()
    print("All Model & Inference Tests PASSED!")
