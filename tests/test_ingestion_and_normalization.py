"""
Automated Tests for Ingestion, Normalization, Matrix Quarantining, and Industrial APIs.
"""

import os
import sys
import math
import pytest
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data.importers.base_importer import (
    validate_coordinates,
    validate_matrix,
    validate_metal_concentration,
    determine_texture_class
)
from src.analytics.pollution_indices import (
    calculate_contamination_factor,
    calculate_geoaccumulation_index,
    calculate_potential_ecological_risk,
    calculate_descriptive_stats,
    GEOCHEMICAL_BASELINES
)
from backend.main import (
    get_in_situ_samples,
    get_industrial_areas,
    get_analytics_summary,
    INDUSTRIAL_CLUSTERS
)

# ---------------------------------------------------------------------------
# 1. Coordinate & Bounds Validation Tests
# ---------------------------------------------------------------------------
def test_coordinate_validation():
    # Valid Tamil Nadu coordinate
    is_valid, msgs = validate_coordinates(11.1271, 78.6569)
    assert is_valid is True
    assert len(msgs) == 0

    # Outside bounds: Delhi
    is_valid, msgs = validate_coordinates(28.6139, 77.2090)
    assert is_valid is False
    assert any("Latitude" in m for m in msgs)

    # Outside bounds: Bay of Bengal
    is_valid, msgs = validate_coordinates(11.1271, 85.0000)
    assert is_valid is False
    assert any("Longitude" in m for m in msgs)


# ---------------------------------------------------------------------------
# 2. Matrix Validation & Quarantine Tests
# ---------------------------------------------------------------------------
def test_matrix_quarantine_rules():
    # True soil matrices must pass
    for valid_m in ["soil", "topsoil", "surface_soil", "agricultural_soil"]:
        is_soil, norm, reason = validate_matrix(valid_m)
        assert is_soil is True
        assert norm == "soil"
        assert reason == ""

    # Water, sediment, vegetation, effluent must be quarantined
    for non_soil in ["water", "groundwater", "sediment", "river_sediment", "vegetation", "crop_foliage", "effluent"]:
        is_soil, norm, reason = validate_matrix(non_soil)
        assert is_soil is False, f"Expected {non_soil} to be quarantined!"
        assert "Quarantined non-soil" in reason or "soil" in reason


# ---------------------------------------------------------------------------
# 3. Zero-Imputation Prevention Tests
# ---------------------------------------------------------------------------
def test_metal_validation_never_imputes_zero():
    # Missing value must return None, NOT zero
    conc, err = validate_metal_concentration(None, "chromium")
    assert conc is None

    conc_nan, err = validate_metal_concentration(float("nan"), "lead")
    assert conc_nan is None

    # Positive measurement must be preserved
    conc_valid, err = validate_metal_concentration(124.5, "chromium")
    assert conc_valid == 124.5
    assert err is None

    # Non-positive values (<= 0) are rejected / flagged
    conc_zero, err = validate_metal_concentration(0.0, "cadmium")
    assert conc_zero is None
    assert "cannot be <= 0" in err


# ---------------------------------------------------------------------------
# 4. Normalized Tables & Referential Integrity Tests
# ---------------------------------------------------------------------------
def test_normalized_database_integrity():
    norm_dir = os.path.join(BASE_DIR, "data", "normalized")
    assert os.path.exists(os.path.join(norm_dir, "soil_samples.parquet"))
    assert os.path.exists(os.path.join(norm_dir, "heavy_metal_results.parquet"))
    assert os.path.exists(os.path.join(norm_dir, "soil_health_results.parquet"))
    assert os.path.exists(os.path.join(norm_dir, "data_sources.parquet"))
    assert os.path.exists(os.path.join(norm_dir, "quarantined_samples.parquet"))

    df_samples = pd.read_parquet(os.path.join(norm_dir, "soil_samples.parquet"))
    df_metals = pd.read_parquet(os.path.join(norm_dir, "heavy_metal_results.parquet"))
    df_health = pd.read_parquet(os.path.join(norm_dir, "soil_health_results.parquet"))
    df_quarantine = pd.read_parquet(os.path.join(norm_dir, "quarantined_samples.parquet"))

    # All samples must be soil
    assert (df_samples["sample_matrix"] == "soil").all()

    # All quarantined records must be non-soil matrices
    assert len(df_quarantine) >= 3
    assert set(df_quarantine["sample_matrix"]).issubset({"effluent", "sediment", "vegetation"})

    # Referential integrity: all metals belong to valid samples
    valid_ids = set(df_samples["sample_id"])
    assert set(df_metals["sample_id"]).issubset(valid_ids)
    assert set(df_health["sample_id"]).issubset(valid_ids)


# ---------------------------------------------------------------------------
# 5. Industrial Clusters Coverage Tests
# ---------------------------------------------------------------------------
def test_eight_target_industrial_areas():
    areas_resp = get_industrial_areas()
    assert areas_resp["state"] == "Tamil Nadu"
    assert areas_resp["total_clusters"] == 8

    cluster_names = [c["name"] for c in areas_resp["industrial_areas"]]
    expected_areas = [
        "Ranipet SIPCOT",
        "Cuddalore SIPCOT",
        "Manali",
        "Coimbatore SIDCO Kurichi",
        "Tiruppur",
        "Mettur",
        "Erode",
        "Thoothukudi SIPCOT"
    ]
    for exp in expected_areas:
        assert exp in cluster_names, f"Missing target industrial area: {exp}"

    # Confirm each cluster has coordinates in Tamil Nadu
    for c in areas_resp["industrial_areas"]:
        assert 8.0 <= c["center"]["latitude"] <= 14.0
        assert 76.0 <= c["center"]["longitude"] <= 81.0
        assert len(c["industrial_sectors"]) > 0


# ---------------------------------------------------------------------------
# 6. API Filtering Tests
# ---------------------------------------------------------------------------
def test_samples_endpoint_filtering():
    # 1. Filter by district
    res_ranipet = get_in_situ_samples(district="Ranipet", limit=50)
    assert res_ranipet["total_matching"] > 0
    for s in res_ranipet["samples"]:
        assert "Ranipet" in s["district"] or "Ranipet" in s["industrial_area"]

    # 2. Filter by industrial area
    res_ind = get_in_situ_samples(industrial_area="Cuddalore SIPCOT", limit=50)
    assert res_ind["total_matching"] > 0
    for s in res_ind["samples"]:
        assert "Cuddalore" in s["industrial_area"]

    # 3. Filter by metal
    res_cr = get_in_situ_samples(metal="chromium", limit=20)
    assert res_cr["total_matching"] > 0
    for s in res_cr["samples"]:
        assert s["chromium_mg_kg"] is not None
        assert s["chromium_mg_kg"] > 0

    # 4. Filter by matrix (only topsoil)
    res_soil = get_in_situ_samples(sample_matrix="soil", limit=20)
    assert res_soil["total_matching"] > 0
    for s in res_soil["samples"]:
        assert s["sample_matrix"] == "soil"


# ---------------------------------------------------------------------------
# 7. Pollution Indices & Analytics Tests
# ---------------------------------------------------------------------------
def test_pollution_indices():
    # CF test (Cr baseline is 50 mg/kg)
    cf, desc = calculate_contamination_factor(150.0, "chromium")
    assert cf == 3.0
    assert desc == "Considerable Contamination"

    # Igeo test: Müller formula
    igeo, desc = calculate_geoaccumulation_index(150.0, "chromium")
    expected_igeo = round(math.log2(150.0 / (1.5 * 50.0)), 2)
    assert igeo == expected_igeo

    # Ecological Risk test
    ri_res = calculate_potential_ecological_risk({"chromium": 100.0, "lead": 40.0, "cadmium": 0.70})
    assert ri_res["potential_ecological_risk_index_RI"] > 0
    assert "individual_ecological_risks_Er" in ri_res

    # Analytics summary endpoint
    summary = get_analytics_summary(district="Ranipet")
    assert "metals_analyzed" in summary
    assert "chromium" in summary["metals_analyzed"]
    cr_stat = summary["metals_analyzed"]["chromium"]
    assert cr_stat["sample_count"] > 0
    assert "mean_contamination_factor_CF" in cr_stat


if __name__ == "__main__":
    test_coordinate_validation()
    test_matrix_quarantine_rules()
    test_metal_validation_never_imputes_zero()
    test_normalized_database_integrity()
    test_eight_target_industrial_areas()
    test_samples_endpoint_filtering()
    test_pollution_indices()
    print("ALL Ingestion, Normalization & Industrial API Tests PASSED SUCCESSFULLY!")
