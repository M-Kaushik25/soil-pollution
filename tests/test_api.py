"""
Automated Unit and Integration Tests for GeoSoil Insight API
Covers:
- Application health & manifest
- Pydantic soil texture & bounds validation
- Model predictions for all four target metals (Cr, Pb, Cd, Ni)
- Calibrated conformal prediction intervals & quantiles
- Invalid model/metal handling (HTTP 400)
- Tree feature gain attribution
- Adaptive sampling priority & candidate ranking
- In-situ samples loading & map grid loading
- Environmental assessment report generation
"""

import sys
import os
import pytest
from fastapi import HTTPException

# Add repository root to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from backend.main import (
    app,
    root,
    health_check,
    get_metals,
    predict_soil_pollution,
    get_explanation,
    calculate_sampling_priority,
    get_sampling_recommendations,
    get_in_situ_samples,
    get_statewide_pollution_map,
    generate_analysis_report,
    LocationInput,
    ReportRequest,
    METAL_INFO,
    CONFORMAL_REGISTRY
)

# ---------------------------------------------------------------------------
# 1. Health & Manifest Tests
# ---------------------------------------------------------------------------
def test_app_health():
    health = health_check()
    assert health["status"] == "healthy"
    assert health["total_models"] == 4
    assert set(health["models_loaded"]) == {"chromium", "lead", "cadmium", "nickel"}
    assert health["data_artifacts"]["master_dataset"] is True
    assert health["data_artifacts"]["prediction_grid"] is True
    assert health["data_artifacts"]["conformal_metrics"] is True

def test_root_manifest():
    manifest = root()
    assert manifest["status"] == "active"
    assert "GeoSoil Insight" in manifest["app_name"]
    assert set(manifest["available_targets"]) == {"chromium", "lead", "cadmium", "nickel"}

def test_metals_standards_registry():
    metals_res = get_metals()
    assert "metals" in metals_res
    metals = metals_res["metals"]
    for m in ["chromium", "lead", "cadmium", "nickel"]:
        assert m in metals
        info = metals[m]
        assert "background_baseline_mg_kg" in info
        assert "agricultural_limit_mg_kg" in info
        assert "action_level_mg_kg" in info
        assert "toxicity_coefficient" in info
        assert info["action_level_mg_kg"] > info["agricultural_limit_mg_kg"] >= info["background_baseline_mg_kg"]

# ---------------------------------------------------------------------------
# 2. Input Validation Tests
# ---------------------------------------------------------------------------
def test_valid_soil_texture():
    loc = LocationInput(
        latitude=11.1085,
        longitude=77.3411,
        soil_ph=7.0,
        soil_ec_dSm=0.8,
        soc_pct=1.5,
        clay_pct=30.0,
        sand_pct=50.0,
        silt_pct=20.0,
        land_use="Industrial-Adjacent"
    )
    assert loc.clay_pct + loc.sand_pct + loc.silt_pct == 100.0

def test_invalid_soil_texture_rejection():
    # Sum = 120%, should raise ValueError
    with pytest.raises(ValueError) as excinfo:
        LocationInput(
            latitude=11.1085,
            longitude=77.3411,
            soil_ph=7.0,
            soil_ec_dSm=0.8,
            soc_pct=1.5,
            clay_pct=40.0,
            sand_pct=40.0,
            silt_pct=40.0
        )
    assert "Physically invalid soil texture" in str(excinfo.value)
    assert "sums to 120.0%" in str(excinfo.value)

def test_invalid_out_of_bounds_coordinates():
    # Outside Tamil Nadu latitude (15.5 N)
    with pytest.raises(ValueError):
        LocationInput(
            latitude=15.5,
            longitude=77.3411,
            clay_pct=30.0,
            sand_pct=50.0,
            silt_pct=20.0
        )
    # Outside Tamil Nadu longitude (73.0 E)
    with pytest.raises(ValueError):
        LocationInput(
            latitude=11.0,
            longitude=73.0,
            clay_pct=30.0,
            sand_pct=50.0,
            silt_pct=20.0
        )

# ---------------------------------------------------------------------------
# 3. Prediction Tests for All Four Target Heavy Metals
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("metal", ["chromium", "lead", "cadmium", "nickel"])
def test_predict_each_metal(metal):
    loc = LocationInput(
        latitude=11.1085,
        longitude=77.3411,
        soil_ph=6.9,
        soil_ec_dSm=0.8,
        soc_pct=1.6,
        clay_pct=32.0,
        sand_pct=48.0,
        silt_pct=20.0,
        land_use="Industrial-Adjacent"
    )
    res = predict_soil_pollution(loc, metal=metal)
    
    assert res["metal"].lower() == METAL_INFO[metal]["name"].lower()
    assert res["predicted_concentration_mg_kg"] > 0
    assert "conformal_interval_90" in res
    
    conf = res["conformal_interval_90"]
    assert conf["lower_bound"] >= 0.0
    assert conf["upper_bound"] > conf["lower_bound"]
    assert conf["nominal_coverage_pct"] == 90.0
    assert conf["margin_q_hat"] > 0
    
    # Check risk categories and indices
    assert res["risk_tier"] in ["low", "moderate", "warning", "critical"]
    assert "geoaccumulation_index_igeo" in res
    assert "single_ecological_risk_Er" in res

def test_invalid_metal_rejection():
    loc = LocationInput(
        latitude=11.1085,
        longitude=77.3411,
        clay_pct=30.0,
        sand_pct=50.0,
        silt_pct=20.0
    )
    with pytest.raises(HTTPException) as excinfo:
        predict_soil_pollution(loc, metal="mercury")
    assert excinfo.value.status_code == 400
    assert "not supported" in excinfo.value.detail

# ---------------------------------------------------------------------------
# 4. Feature Attribution & Explanation Tests
# ---------------------------------------------------------------------------
def test_feature_gain_attribution():
    loc = LocationInput(
        latitude=11.1085,
        longitude=77.3411,
        clay_pct=30.0,
        sand_pct=50.0,
        silt_pct=20.0,
        land_use="Industrial-Adjacent"
    )
    res = get_explanation(loc, metal="chromium")
    assert res["method"] == "Gradient-Boosted Tree Feature Gain Attribution"
    assert "not Shapley (SHAP)" in res["attribution_disclaimer"]
    assert len(res["top_contributing_drivers"]) >= 5
    first_driver = res["top_contributing_drivers"][0]
    assert "feature_name" in first_driver
    assert "attribution_impact" in first_driver
    assert first_driver["attribution_impact"] > 0

# ---------------------------------------------------------------------------
# 5. Adaptive Sampling Tests
# ---------------------------------------------------------------------------
def test_sampling_priority_calculation():
    loc = LocationInput(
        latitude=12.9248,
        longitude=79.3330, # Ranipet cluster
        soil_ph=6.5,
        soil_ec_dSm=1.2,
        soc_pct=1.8,
        clay_pct=35.0,
        sand_pct=45.0,
        silt_pct=20.0,
        land_use="Industrial-Adjacent"
    )
    res = calculate_sampling_priority(loc)
    assert 0 <= res["adaptive_sampling_priority_score"] <= 100
    assert "priority_recommendation" in res
    assert "scoring_weights" in res
    assert res["scoring_weights"]["ecological_risk_weight"] == 0.55

def test_sampling_recommendations_ranking():
    recs = get_sampling_recommendations(top_k=10)
    items = recs["top_recommendations"]
    assert len(items) == 10
    
    # Verify ranking monotonicity (descending priority scores)
    scores = [item["priority_score"] for item in items]
    assert scores == sorted(scores, reverse=True)
    
    for item in items:
        assert 8.0 <= item["latitude"] <= 14.0
        assert 76.0 <= item["longitude"] <= 81.0
        assert item["min_distance_to_existing_sample_km"] >= 0

# ---------------------------------------------------------------------------
# 6. Map & In-Situ Data Loading Tests
# ---------------------------------------------------------------------------
def test_in_situ_samples_loading():
    data = get_in_situ_samples(limit=25)
    samples = data["samples"]
    assert len(samples) == 25
    s0 = samples[0]
    assert "sample_id" in s0
    assert "chromium_mg_kg" in s0
    assert "lead_mg_kg" in s0
    assert "cadmium_mg_kg" in s0
    assert "nickel_mg_kg" in s0

def test_statewide_pollution_map_grid():
    grid = get_statewide_pollution_map(max_points=50)
    cells = grid["grid_data"]
    assert len(cells) > 0
    assert len(cells) <= 50
    c0 = cells[0]
    assert "latitude" in c0
    assert "longitude" in c0
    assert "potential_ecological_risk_index_RI" in c0

# ---------------------------------------------------------------------------
# 7. Formal Report Generation Tests
# ---------------------------------------------------------------------------
def test_report_generation():
    loc = LocationInput(
        latitude=11.1085,
        longitude=77.3411,
        soil_ph=6.9,
        soil_ec_dSm=0.8,
        soc_pct=1.6,
        clay_pct=30.0,
        sand_pct=50.0,
        silt_pct=20.0,
        land_use="Industrial-Adjacent"
    )
    req = ReportRequest(location_input=loc, metal="chromium", notes="Integration test run")
    rep = generate_analysis_report(req)
    
    assert rep["report_id"].startswith("GSI-TN-")
    assert "generated_at" in rep
    assert rep["target_metal"] == "Chromium"
    assert "predicted_concentration" in rep["model_estimates"]
    assert "conformal_prediction_interval_90" in rep["model_estimates"]
    assert len(rep["scientific_limitations_and_disclaimer"]) >= 3

if __name__ == "__main__":
    print("Executing GeoSoil Insight Test Suite...")
    test_app_health()
    test_root_manifest()
    test_metals_standards_registry()
    test_valid_soil_texture()
    test_invalid_soil_texture_rejection()
    test_invalid_out_of_bounds_coordinates()
    for m in ["chromium", "lead", "cadmium", "nickel"]:
        test_predict_each_metal(m)
    test_invalid_metal_rejection()
    test_feature_gain_attribution()
    test_sampling_priority_calculation()
    test_sampling_recommendations_ranking()
    test_in_situ_samples_loading()
    test_statewide_pollution_map_grid()
    test_report_generation()
    print("ALL 14 GeoSoil Insight Test Groups PASSED SUCCESSFULLY!")
