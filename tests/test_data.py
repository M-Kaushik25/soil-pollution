"""
Automated Data Quality & Spatial Bounds Tests
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def test_raw_data_exists():
    raw_path = os.path.join(BASE_DIR, "data", "raw", "tamil_nadu_soil_heavy_metals_raw.csv")
    assert os.path.exists(raw_path), f"Raw dataset missing: {raw_path}"
    df = pd.read_csv(raw_path)
    assert len(df) >= 400, "Raw dataset must contain at least 400 samples"
    assert "latitude" in df.columns and "longitude" in df.columns

def test_clean_data_integrity():
    clean_path = os.path.join(BASE_DIR, "data", "processed", "clean_soil_data.parquet")
    assert os.path.exists(clean_path), f"Clean dataset missing: {clean_path}"
    df = pd.read_parquet(clean_path)
    
    # Verify no duplicate coordinates
    assert df.duplicated(subset=["latitude", "longitude"]).sum() == 0, "Duplicate coordinates found in clean dataset"
    
    # Verify geographic bounds of Tamil Nadu
    assert (df["latitude"] >= 8.0).all() and (df["latitude"] <= 14.0).all(), "Latitudes out of bounds"
    assert (df["longitude"] >= 76.0).all() and (df["longitude"] <= 81.0).all(), "Longitudes out of bounds"
    
    # Verify target metals are non-null and strictly positive
    for target in ["lead_mg_kg", "cadmium_mg_kg", "chromium_mg_kg", "nickel_mg_kg"]:
        assert df[target].isnull().sum() == 0, f"Missing values in {target}"
        assert (df[target] > 0).all(), f"Non-positive values in {target}"

def test_master_feature_dataset():
    master_path = os.path.join(BASE_DIR, "data", "processed", "master_soil_pollution_dataset.parquet")
    assert os.path.exists(master_path), f"Master dataset missing: {master_path}"
    df = pd.read_parquet(master_path)
    
    # Must contain at least 30 environmental predictor features
    assert len(df.columns) >= 35, f"Expected >=35 columns, got {len(df.columns)}"
    assert df.isnull().sum().sum() == 0, "Master dataset contains unhandled null values"

if __name__ == "__main__":
    test_raw_data_exists()
    test_clean_data_integrity()
    test_master_feature_dataset()
    print("All Data Integrity Tests PASSED!")
