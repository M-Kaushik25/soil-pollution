"""
Comprehensive Integration & Acceptance Tests for Tamil Nadu SoilWatch Backend
Validates all 13 Core Endpoints, Data Pipeline Integrity, and Pollution Indices.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from backend.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# ---------------------------------------------------------------------------
# 1. Health & Manifest Check
# ---------------------------------------------------------------------------
def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["sample_count"] >= 450
    assert data["total_models"] >= 4
    assert "dataset_availability" in data
    assert data["dataset_availability"]["master_dataset"] is True
    assert data["dataset_availability"]["normalized_samples"] is True

# ---------------------------------------------------------------------------
# 2. Dashboard Executive Summary
# ---------------------------------------------------------------------------
def test_dashboard_summary(client):
    res = client.get("/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["unique_sample_count"] >= 450
    assert data["industrial_areas_covered"] >= 8
    assert data["total_records"] >= 3000
    assert 5.0 <= data["average_soil_ph"] <= 9.0
    assert "data_quality_summary" in data
    assert data["data_quality_summary"]["zero_imputation_prevented"] is True
    assert data["data_quality_summary"]["quarantined_non_soil_records"] == 3

# ---------------------------------------------------------------------------
# 3. Samples List, Search, Filter & Pagination
# ---------------------------------------------------------------------------
def test_samples_listing_and_filters(client):
    # Basic list
    res = client.get("/samples?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data["samples"]) == 10
    assert data["total_matching"] >= 450

    # District filter
    res_dist = client.get("/samples?district=Ranipet")
    assert res_dist.status_code == 200
    d_data = res_dist.json()
    assert all("Ranipet" in s["district"] or "Ranipet" in s["industrial_area"] for s in d_data["samples"])

    # Industrial area filter
    res_ind = client.get("/samples?industrial_area=Manali")
    assert res_ind.status_code == 200
    assert len(res_ind.json()["samples"]) >= 1

    # Search filter
    res_search = client.get("/samples?search=TN_SOIL_0001")
    assert res_search.status_code == 200
    assert len(res_search.json()["samples"]) == 1
    assert res_search.json()["samples"][0]["sample_id"] == "TN_SOIL_0001"

    # Sorting
    res_sort = client.get("/samples?limit=5&sort_by=sample_id&sort_order=desc")
    assert res_sort.status_code == 200
    ids = [s["sample_id"] for s in res_sort.json()["samples"]]
    assert ids == sorted(ids, reverse=True)

# ---------------------------------------------------------------------------
# 4. Single Sample Lookup by ID
# ---------------------------------------------------------------------------
def test_single_sample_lookup(client):
    res = client.get("/samples/TN_SOIL_0001")
    assert res.status_code == 200
    sample = res.json()
    assert sample["sample_id"] == "TN_SOIL_0001"
    assert "heavy_metal_results" in sample
    assert "soil_properties" in sample
    assert "source_information" in sample
    assert "latitude" in sample and "longitude" in sample
    assert 8.0 <= sample["latitude"] <= 14.0
    assert 76.0 <= sample["longitude"] <= 81.0

def test_single_sample_not_found(client):
    res = client.get("/samples/NON_EXISTENT_ID_9999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

# ---------------------------------------------------------------------------
# 5. Pollution Map Endpoint
# ---------------------------------------------------------------------------
def test_pollution_map_endpoint(client):
    res = client.get("/pollution-map?limit=100")
    assert res.status_code == 200
    data = res.json()
    assert "samples" in data
    assert "industrial_clusters" in data
    assert len(data["industrial_clusters"]) == 8
    assert len(data["samples"]) > 0

# ---------------------------------------------------------------------------
# 6. Metals Registry & Global Statistics
# ---------------------------------------------------------------------------
def test_metals_registry(client):
    res = client.get("/metals")
    assert res.status_code == 200
    data = res.json()
    assert "metals" in data
    assert "geochemical_baselines" in data
    assert "metal_statistics" in data
    assert "chromium" in data["metal_statistics"]
    assert "lead" in data["metal_statistics"]

# ---------------------------------------------------------------------------
# 7. Metal Specific Statistics Endpoint
# ---------------------------------------------------------------------------
def test_metal_statistics(client):
    for m in ["chromium", "lead", "cadmium", "nickel"]:
        res = client.get(f"/metals/{m}/statistics")
        assert res.status_code == 200
        stats = res.json()
        assert stats["metal"] == m
        assert stats["valid_measurement_count"] >= 450
        assert stats["mean_mg_kg"] > 0
        assert stats["geochemical_baseline_mg_kg"] > 0
        assert stats["minimum_mg_kg"] <= stats["median_mg_kg"] <= stats["maximum_mg_kg"]

def test_invalid_metal_statistics(client):
    res = client.get("/metals/unobtanium/statistics")
    assert res.status_code == 404

# ---------------------------------------------------------------------------
# 8. Soil Health Endpoint
# ---------------------------------------------------------------------------
def test_soil_health_endpoint(client):
    res = client.get("/soil-health?limit=20")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] >= 450
    assert len(data["records"]) == 20
    assert "summary" in data
    assert "mean_soil_ph" in data["summary"]
    assert "texture_class_distribution" in data["summary"]
    
    # Validate soil properties
    first = data["records"][0]
    assert "soil_ph" in first
    assert "soil_ec_dSm" in first
    assert "texture_class" in first

# ---------------------------------------------------------------------------
# 9. Risk Assessment Calculation
# ---------------------------------------------------------------------------
def test_risk_assessment_calculation(client):
    payload = {
        "metal": "chromium",
        "concentration": 150.0,
        "unit": "mg/kg",
        "industrial_area": "Ranipet SIPCOT",
        "soil_ph": 7.4
    }
    res = client.post("/assessment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metal"] == "chromium"
    assert data["input_concentration"] == 150.0
    assert data["reference_baseline_mg_kg"] == 50.0
    # CF should be exactly 150 / 50 = 3.0
    assert data["contamination_factor_CF"] == 3.0
    # Igeo = log2(150 / (1.5 * 50)) = log2(2) = 1.0
    assert round(data["geoaccumulation_index_Igeo"], 1) == 1.0
    assert "Considerable" in data["risk_tier"] or "High" in data["risk_tier"]
    assert len(data["adaptive_recommendation"]) > 10

def test_risk_assessment_unit_conversion(client):
    # 20,000 ppb = 20 mg/kg
    payload = {
        "metal": "lead",
        "concentration": 20000.0,
        "unit": "ppb"
    }
    res = client.post("/assessment", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["standardized_concentration_mg_kg"] == 20.0
    assert data["contamination_factor_CF"] == 1.0

def test_risk_assessment_invalid_unit(client):
    payload = {
        "metal": "lead",
        "concentration": 50.0,
        "unit": "gallons"
    }
    res = client.post("/assessment", json=payload)
    assert res.status_code == 400

# ---------------------------------------------------------------------------
# 10. Sampling Recommendations
# ---------------------------------------------------------------------------
def test_sampling_recommendations(client):
    res = client.get("/sampling-recommendations?top_k=10")
    assert res.status_code == 200
    data = res.json()
    assert "top_recommendations" in data
    assert len(data["top_recommendations"]) == 10

# ---------------------------------------------------------------------------
# 11. Model Performance
# ---------------------------------------------------------------------------
def test_model_performance(client):
    res = client.get("/model-performance")
    assert res.status_code == 200
    data = res.json()
    assert "models_summary" in data
    assert "conformal_calibration_summary" in data
    assert "scientific_disclosure" in data

# ---------------------------------------------------------------------------
# 12. Report Generation (JSON & Downloadable CSV)
# ---------------------------------------------------------------------------
def test_report_generation_json(client):
    res = client.get("/report/generate?district=Ranipet&format=json")
    assert res.status_code == 200
    data = res.json()
    assert "report_id" in data
    assert "metal_summaries" in data
    assert data["scope"]["total_samples"] >= 1

def test_report_generation_csv(client):
    res = client.get("/report/generate?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment" in res.headers.get("content-disposition", "")
    lines = res.text.strip().split("\n")
    assert len(lines) >= 450
    header = lines[0]
    assert "sample_id" in header and "chromium" in header and "lead" in header

# ---------------------------------------------------------------------------
# 13. Data Sources Registry
# ---------------------------------------------------------------------------
def test_data_sources_registry(client):
    res = client.get("/data-sources")
    assert res.status_code == 200
    data = res.json()
    assert data["total_sources"] >= 8
    sources = data["sources"]
    assert any("Ranipet" in s["source_name"] for s in sources)
    assert any("Cuddalore" in s["source_name"] for s in sources)
    assert all("license" in s and "analytical_protocol" in s for s in sources)
