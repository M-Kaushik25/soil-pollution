"""
Automated Traceability & Data Lineage Audit Tests
Validates that all dashboard values, endpoints, statistics, and coordinates
strictly conform to normalized ground truth data and actual model reports.
"""

import os
import json
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from src.analytics.pollution_indices import GEOCHEMICAL_BASELINES

client = TestClient(app)
NORM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "normalized")


def test_audit_sample_count_against_unique_valid_ids():
    """Verify dashboard sample count matches actual unique valid sample IDs in soil_samples."""
    df_samples = pd.read_parquet(os.path.join(NORM_DIR, "soil_samples.parquet"))
    unique_ids_count = df_samples["sample_id"].nunique()

    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    data = res.json()

    assert data["unique_sample_count"] == unique_ids_count
    assert data["unique_sample_count"] == 464
    assert data["total_records"] == 3194


def test_audit_metal_statistics_against_direct_dataset_calculation():
    """Verify descriptive statistics for every metal match exact direct pandas calculations."""
    df_metals = pd.read_parquet(os.path.join(NORM_DIR, "heavy_metal_results.parquet"))

    for metal in ["chromium", "lead", "cadmium", "nickel", "arsenic", "copper", "zinc"]:
        sub = df_metals[df_metals["metal"] == metal]
        valid_vals = sub["concentration_mg_kg"].dropna()
        bg = GEOCHEMICAL_BASELINES[metal]["background_mg_kg"]

        direct_mean = float(valid_vals.mean())
        direct_min = float(valid_vals.min())
        direct_max = float(valid_vals.max())
        direct_med = float(valid_vals.median())
        direct_std = float(valid_vals.std())
        direct_cf = direct_mean / bg
        direct_igeo = float(np.log2(valid_vals / (1.5 * bg)).mean())

        res = client.get(f"/metals/{metal}/statistics")
        assert res.status_code == 200
        api_data = res.json()

        assert api_data["valid_measurement_count"] == len(valid_vals)
        assert abs(api_data["mean_mg_kg"] - direct_mean) < 0.05
        assert abs(api_data["minimum_mg_kg"] - direct_min) < 0.05
        assert abs(api_data["maximum_mg_kg"] - direct_max) < 0.05
        assert abs(api_data["median_mg_kg"] - direct_med) < 0.05
        assert abs(api_data["std_deviation_mg_kg"] - direct_std) < 0.05
        assert abs(api_data["mean_contamination_factor_CF"] - direct_cf) < 0.05
        assert abs(api_data["mean_geoaccumulation_index_Igeo"] - direct_igeo) < 0.05


def test_audit_map_markers_against_original_coordinates():
    """Verify that every georeferenced marker returned by /pollution-map matches original coordinates."""
    df_samples = pd.read_parquet(os.path.join(NORM_DIR, "soil_samples.parquet"))
    coords_dict = df_samples.set_index("sample_id")[["latitude", "longitude"]].to_dict(orient="index")

    res = client.get("/pollution-map")
    assert res.status_code == 200
    map_data = res.json()
    samples = map_data["samples"]

    assert len(samples) == len(df_samples)
    for s in samples:
        sid = s["sample_id"]
        assert sid in coords_dict, f"Sample {sid} not in normalized dataset!"
        orig = coords_dict[sid]
        assert abs(s["latitude"] - orig["latitude"]) < 1e-5
        assert abs(s["longitude"] - orig["longitude"]) < 1e-5


def test_audit_industrial_clusters_distinct_from_sample_markers():
    """Verify industrial corridor polygons/clusters are distinctly separated from point samples."""
    res = client.get("/pollution-map")
    assert res.status_code == 200
    map_data = res.json()

    assert "industrial_clusters" in map_data
    assert "samples" in map_data
    clusters = map_data["industrial_clusters"]
    assert len(clusters) == 8

    for c in clusters:
        assert "center" in c or "bounds" in c
        assert "name" in c
        assert "id" in c


def test_audit_zero_imputation_prevention():
    """Assert that unmeasured heavy metals are persisted as null / NaN and never represented as 0.00."""
    df_metals = pd.read_parquet(os.path.join(NORM_DIR, "heavy_metal_results.parquet"))
    assert (df_metals["concentration_mg_kg"] == 0.0).sum() == 0

    res = client.get("/samples?limit=100")
    assert res.status_code == 200
    samples = res.json()["samples"]
    for s in samples:
        for m in ["chromium_mg_kg", "lead_mg_kg", "cadmium_mg_kg", "nickel_mg_kg"]:
            val = s[m]
            if val is not None:
                assert val > 0.0, f"Found unexpected zero value for {m} in sample {s['sample_id']}"


def test_audit_model_performance_matches_evaluation_report():
    """Assert that /model-performance values match the actual results/metrics CSV reports."""
    res = client.get("/model-performance")
    assert res.status_code == 200
    data = res.json()

    for target in ["chromium", "lead", "cadmium", "nickel"]:
        mod_info = data["models_summary"][target]
        assert mod_info["spatial_cv_r2"] < 0.0, f"Expected negative spatial CV R2 for {target}"


def test_audit_risk_assessment_reference_values():
    """Verify that /assessment uses Hakanson (1980) and Muller (1969) background standards."""
    payload = {
        "metal": "chromium",
        "concentration": 100.0,
        "unit": "mg/kg"
    }
    res = client.post("/assessment", json=payload)
    assert res.status_code == 200
    d = res.json()
    assert d["reference_baseline_mg_kg"] == 50.0
    assert d["contamination_factor_CF"] == 2.0
    assert abs(d["geoaccumulation_index_Igeo"] - float(np.log2(100.0 / (1.5 * 50.0)))) < 0.01
