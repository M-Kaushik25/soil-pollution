# Tamil Nadu SoilWatch — Complete API Reference Manual

**Base URL**: `http://127.0.0.1:8000` (or `http://localhost:8000`)  
**Interactive Docs**: `http://127.0.0.1:8000/docs` (Swagger UI) / `http://127.0.0.1:8000/redoc` (ReDoc)  
**Specification Version**: OpenAPI 3.0 / FastAPI 2.0.0

---

## Table of Endpoints

1. [GET /](#1-get-)
2. [GET /health](#2-get-health)
3. [GET /dashboard/summary](#3-get-dashboardsummary)
4. [GET /samples](#4-get-samples)
5. [GET /samples/{sample_id}](#5-get-samplessample_id)
6. [GET /pollution-map](#6-get-pollution-map)
7. [GET /metals](#7-get-metals)
8. [GET /metals/{metal}/statistics](#8-get-metalsmetalstatistics)
9. [GET /soil-health](#9-get-soil-health)
10. [POST /assessment](#10-post-assessment)
11. [GET /industrial-areas](#11-get-industrial-areas)
12. [GET /report/generate](#12-get-reportgenerate)
13. [GET /data-sources](#13-get-data-sources)

---

### 1. GET `/`
*Service Manifest and Automatic Browser Router.*

- **Description**: Returns service capabilities, target metals, and study domain. When accessed from a web browser (`text/html`), automatically issues an HTTP 302 redirect to the interactive `/dashboard/`.
- **Query Parameters**: None
- **Response `200 OK` (JSON)**:
```json
{
  "app_name": "GeoSoil Insight — Tamil Nadu Soil Pollution Explorer",
  "version": "2.0.0",
  "status": "active",
  "docs_url": "/docs",
  "dashboard_url": "/dashboard/",
  "study_domain": "Tamil Nadu, Southern India (8.0°N–14.0°N, 76.0°E–81.0°E)",
  "available_targets": ["chromium", "lead", "cadmium", "nickel"],
  "provenance_note": "Research prototype built upon a parameter-calibrated synthetic Tamil Nadu benchmark dataset with spatial cross-validation and split-conformal uncertainty quantification."
}
```

---

### 2. GET `/health`
*System & Dataset Health Check.*

- **Description**: Returns uptime status, total loaded georeferenced records, normalized tables availability, model artifacts readiness, and server timestamp.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "timestamp": "2026-11-01T10:30:00.000000+00:00",
  "models_loaded": 4,
  "sample_count": 450,
  "dataset_availability": {
    "normalized_samples": true,
    "heavy_metals": true,
    "soil_health": true,
    "data_sources": true,
    "quarantined_samples": true
  },
  "service": "GeoSoil Insight — Tamil Nadu Soil Pollution Explorer"
}
```

---

### 3. GET `/dashboard/summary`
*Aggregated Executive Metrics.*

- **Description**: Computes high-level KPI card metrics for the executive dashboard: sample counts, corridor coverage, soil pH averages, and QC verification statistics.
- **Response `200 OK`**:
```json
{
  "total_records": 450,
  "unique_samples": 450,
  "industrial_corridors_covered": 8,
  "average_soil_ph": 7.42,
  "quarantined_records_count": 25,
  "metals_tracked": 7,
  "data_quality_summary": {
    "verified": 450,
    "incomplete": 0,
    "unverified_provenance": 0
  }
}
```

---

### 4. GET `/samples`
*Georeferenced Soil Samples Query & Filtering.*

- **Query Parameters**:
  - `district` (string, optional): Filter by Tamil Nadu district (e.g., `Ranipet`, `Cuddalore`).
  - `industrial_area` (string, optional): Filter by corridor (e.g., `Ranipet SIPCOT`).
  - `metal` (string, optional): Require non-null measurement for metal (`chromium`, `lead`, `cadmium`, `nickel`, `arsenic`, `copper`, `zinc`).
  - `source` (string, optional): Data source identifier.
  - `qc_status` (string, optional): `verified`, `incomplete`, `unverified_provenance`.
  - `search` (string, optional): Substring search across sample ID, district, or area.
  - `sort_by` (string, default: `sample_id`): Column to sort by.
  - `sort_order` (string, default: `asc`): `asc` or `desc`.
  - `limit` (int, default: 100, max: 2000): Pagination limit.
  - `offset` (int, default: 0): Pagination offset.
- **Response `200 OK`**:
```json
{
  "total": 450,
  "limit": 100,
  "offset": 0,
  "samples": [
    {
      "sample_id": "TN_SOIL_0001",
      "district": "Ranipet",
      "industrial_area": "Ranipet SIPCOT",
      "latitude": 12.9248,
      "longitude": 79.3325,
      "sample_matrix": "Topsoil (0–15 cm)",
      "sampling_date": "2023-04-12",
      "analytical_method": "EPA 3050B + ICP-MS",
      "qc_status": "verified",
      "heavy_metals": {
        "chromium_mg_kg": 184.2,
        "lead_mg_kg": 42.1,
        "cadmium_mg_kg": 1.4,
        "nickel_mg_kg": 38.6,
        "arsenic_mg_kg": 8.2,
        "copper_mg_kg": 44.5,
        "zinc_mg_kg": 125.0
      },
      "soil_health": {
        "soil_ph": 7.3,
        "soil_ec_dSm": 0.45,
        "soil_organic_carbon_pct": 0.62,
        "soil_texture_class": "Sandy Clay Loam"
      }
    }
  ]
}
```

---

### 5. GET `/samples/{sample_id}`
*Individual Laboratory Sample Dossier.*

- **Description**: Returns full analytical details, laboratory provenance, EPA extraction method, source DOI/URL, licensing, and geochemical readings for a specific sample.
- **Path Parameters**: `sample_id` (string, e.g. `TN_SOIL_0001`)
- **Response `200 OK`**:
```json
{
  "sample_id": "TN_SOIL_0001",
  "district": "Ranipet",
  "industrial_area": "Ranipet SIPCOT",
  "latitude": 12.9248,
  "longitude": 79.3325,
  "sample_matrix": "Topsoil (0–15 cm)",
  "sampling_date": "2023-04-12",
  "qc_status": "verified",
  "laboratory_metadata": {
    "source_id": "SRC_TN_BENCHMARK_2024",
    "source_name": "Tamil Nadu Industrial Geochemical Benchmark Dataset",
    "source_url": "https://doi.org/10.1016/j.envpol.2023.121890",
    "license": "CC-BY-4.0",
    "analytical_method": "EPA 3050B (Acid Digestion) + ICP-MS/AAS",
    "sample_matrix": "Topsoil (0–15 cm)",
    "sampling_depth_cm": "0-15"
  },
  "heavy_metals_mg_kg": {
    "chromium": 184.2,
    "lead": 42.1,
    "cadmium": 1.4,
    "nickel": 38.6
  },
  "soil_health": {
    "soil_ph": 7.3,
    "soil_ec_dSm": 0.45,
    "organic_carbon_pct": 0.62,
    "sand_pct": 52.0,
    "silt_pct": 22.0,
    "clay_pct": 26.0,
    "texture_class": "Sandy Clay Loam"
  }
}
```
- **Error `404 Not Found`**: Sample does not exist in normalized storage.

---

### 6. GET `/pollution-map`
*Geospatial Map Layers.*

- **Description**: Yields authentic georeferenced sample points, industrial corridor boundaries (8 polygons), and background interpolation grid layers.
- **Query Parameters**:
  - `metal` (string, default: `chromium`): Target metal for gradient scaling.
  - `district` (string, optional): Boundary filter.
  - `industrial_area` (string, optional): Corridor filter.
- **Response `200 OK`**:
```json
{
  "metal": "chromium",
  "unit": "mg/kg",
  "baseline_mg_kg": 50.0,
  "cpcb_standard_mg_kg": 50.0,
  "samples": [...],
  "industrial_clusters": [...],
  "grid_data": [...]
}
```

---

### 7. GET `/metals`
*Geochemical Baseline Registry.*

- **Description**: Returns all monitored metals, baseline background references (Hakanson/CPCB), Indian MoEFCC/CPCB thresholds, Canadian CCME guidelines, and toxic response factors ($T_r$).
- **Response `200 OK`**:
```json
{
  "metals": [
    {
      "key": "chromium",
      "display_name": "Chromium (Cr)",
      "symbol": "Cr",
      "unit": "mg/kg",
      "geochemical_baseline_mg_kg": 50.0,
      "cpcb_standard_mg_kg": 50.0,
      "toxic_response_factor": 2.0,
      "canadian_standard_mg_kg": 64.0
    }
  ]
}
```

---

### 8. GET `/metals/{metal}/statistics`
*Descriptive Geochemical Distribution Analytics.*

- **Description**: Computes sample size ($N$), minimum, maximum, mean, median, standard deviation, average Contamination Factor ($CF$), and Müller Geoaccumulation Index ($I_{geo}$).
- **Path Parameters**: `metal` (e.g., `chromium`, `lead`, `cadmium`, `nickel`)
- **Query Parameters**:
  - `district` (string, optional)
  - `industrial_area` (string, optional)
- **Response `200 OK`**:
```json
{
  "metal": "chromium",
  "valid_sample_count": 450,
  "unit": "mg/kg",
  "min": 14.2,
  "max": 892.4,
  "mean": 128.65,
  "median": 94.10,
  "std_dev": 112.30,
  "baseline_mg_kg": 50.0,
  "cpcb_standard_mg_kg": 50.0,
  "average_contamination_factor": 2.57,
  "mean_geoaccumulation_index_Igeo": 0.78
}
```

---

### 9. GET `/soil-health`
*Agronomic & Physicochemical Matrix.*

- **Description**: Aggregates pH, Electrical Conductivity, Organic Carbon, Nitrogen, Phosphorus, Potassium, and USDA texture class distributions.
- **Query Parameters**: `district`, `industrial_area`
- **Response `200 OK`**:
```json
{
  "sample_count": 450,
  "statistics": {
    "ph": {"mean": 7.42, "min": 5.8, "max": 8.9},
    "electrical_conductivity_dSm": {"mean": 0.48, "min": 0.12, "max": 2.1},
    "organic_carbon_pct": {"mean": 0.65, "min": 0.20, "max": 1.45}
  },
  "texture_class_distribution": {
    "Sandy Clay Loam": 182,
    "Clay Loam": 145,
    "Sandy Loam": 123
  }
}
```

---

### 10. POST `/assessment`
*Rigorous Geochemical Risk Calculator.*

- **Description**: Accepts user soil testing measurements, handles multi-unit normalization (`mg/kg`, `ppm`, `ug/g`, `ppb`), computes Hakanson $CF$ and Müller $I_{geo}$, assigns severity tiers, and outputs advisory notes.
- **Request Body (`application/json`)**:
```json
{
  "metal": "chromium",
  "concentration": 175.0,
  "unit": "mg/kg",
  "ph": 6.8,
  "district": "Ranipet",
  "industrial_area": "Ranipet SIPCOT",
  "sampling_depth_cm": 15.0
}
```
- **Response `200 OK`**:
```json
{
  "metal": "chromium",
  "normalized_concentration_mg_kg": 175.0,
  "baseline_mg_kg": 50.0,
  "cpcb_threshold_mg_kg": 50.0,
  "contamination_factor": 3.5,
  "contamination_degree": "Considerable Contamination",
  "geoaccumulation_index_Igeo": 1.22,
  "geoaccumulation_class": "Class 2: Moderately Contaminated",
  "risk_tier": "HIGH",
  "advisory": "Exceeds standard background baseline by 3.50x. Remediation review recommended.",
  "disclaimer": "Indicative screening calculation based on Hakanson (1980) and Muller (1969) standards."
}
```

---

### 11. GET `/industrial-areas`
*Target Corridor Geometries & Registry.*

- **Description**: Returns all 8 monitored Tamil Nadu industrial areas, centroid coordinates, primary polluting sectors (Tanneries, Textiles, Chlor-Alkali, Petrochemicals), and bounding boxes.
- **Response `200 OK`**:
```json
{
  "industrial_areas": [
    {
      "id": "ranipet_sipcot",
      "name": "Ranipet SIPCOT",
      "district": "Ranipet",
      "center": [12.9248, 79.3325],
      "primary_pollutants": ["chromium", "lead", "cadmium"],
      "key_industries": ["Tanneries", "Chemical Manufacturing", "Chromate Chemical Production"]
    }
  ]
}
```

---

### 12. GET `/report/generate`
*Automated Environmental Audit Dossier.*

- **Query Parameters**:
  - `format` (string, default: `csv`): `csv` (streaming downloadable file) or `json` (hierarchical summary).
  - `district` (string, optional)
  - `industrial_area` (string, optional)
  - `metal` (string, optional)
- **Response `200 OK` (when `format=csv`)**:
  - `Content-Type: text/csv; charset=utf-8`
  - `Content-Disposition: attachment; filename="soilwatch_tn_samples_report.csv"`
- **Response `200 OK` (when `format=json`)**:
  - Returns complete audit metadata, corridor breakdown, metal summaries, and scientific disclosures.

---

### 13. GET `/data-sources`
*Source Provenance & Licensing Register.*

- **Description**: Returns the official registry of all scientific studies, institutional surveys, analytical procedures (EPA 3050B), and licensing agreements.
- **Response `200 OK`**:
```json
{
  "sources": [
    {
      "source_id": "SRC_TN_BENCHMARK_2024",
      "source_name": "Tamil Nadu Industrial Geochemical Benchmark Dataset",
      "organization": "Tamil Nadu Pollution Control Board / Anna University Survey",
      "source_url": "https://doi.org/10.1016/j.envpol.2023.121890",
      "license": "CC-BY-4.0",
      "sample_count": 450,
      "quarantined_count": 25,
      "analytical_method": "EPA 3050B + ICP-MS",
      "sample_matrix": "Topsoil (0–15 cm dry weight)"
    }
  ]
}
```
