"""
Automated FastAPI Endpoint Integration Tests
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"

def test_metals_endpoint():
    res = client.get("/metals")
    assert res.status_code == 200
    data = res.json()
    assert "metals" in data
    assert "chromium" in data["metals"]

def test_predict_endpoint():
    payload = {
        "latitude": 11.1085,
        "longitude": 77.3411,
        "soil_ph": 7.1,
        "clay_pct": 32.0,
        "soc_pct": 1.6,
        "land_use": "Industrial-Adjacent"
    }
    res = client.post("/predict?metal=chromium", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_concentration_mg_kg" in data
    assert "conformal_interval_90" in data
    assert data["predicted_concentration_mg_kg"] > 0

def test_explanation_endpoint():
    payload = {
        "latitude": 11.1085,
        "longitude": 77.3411,
        "soil_ph": 7.1,
        "clay_pct": 32.0,
        "land_use": "Industrial-Adjacent"
    }
    res = client.post("/explanation?metal=chromium", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "top_contributing_drivers" in data
    assert len(data["top_contributing_drivers"]) > 0

def test_sampling_priority_endpoint():
    payload = {
        "latitude": 11.1085,
        "longitude": 77.3411,
        "soil_ph": 7.1,
        "clay_pct": 32.0
    }
    res = client.post("/sampling-priority", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "adaptive_sampling_priority_score" in data
    assert 0 <= data["adaptive_sampling_priority_score"] <= 100

if __name__ == "__main__":
    test_root_endpoint()
    test_metals_endpoint()
    test_predict_endpoint()
    test_explanation_endpoint()
    test_sampling_priority_endpoint()
    print("All API Endpoint Tests PASSED!")
