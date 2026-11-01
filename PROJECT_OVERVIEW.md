# Tamil Nadu SoilWatch — Project Overview & Architecture

## 1. Executive Summary
**Tamil Nadu SoilWatch** is an enterprise-grade geospatial intelligence and environmental risk monitoring platform engineered to assess, map, and predict industrial soil heavy-metal pollution across the state of Tamil Nadu, India ($8.0^\circ\text{N}–14.0^\circ\text{N}, 76.0^\circ\text{E}–81.0^\circ\text{E}$).

The platform combines authentic georeferenced topsoil monitoring data, validated geochemical baselines for the Peninsular Indian Shield, standardized pollution indices (Contamination Factor $CF$, Geoaccumulation Index $I_{geo}$), and machine-learning spatial models equipped with 90% Split-Conformal Prediction intervals.

---

## 2. Problem Statement & Objectives
Unregulated industrial discharge, legacy tannery sludge, metallurgical slag, and textile effluent have generated severe localized trace metal contamination in critical Tamil Nadu industrial corridors (such as Hexavalent Chromium in Ranipet SIPCOT and Lead/Cadmium in Manali petrochemical basin).

### Key Project Objectives:
1. **Traceable Multi-Source Data Ingestion**: Normalize in-situ monitoring data while preserving raw provenance, analytical protocols, and sample matrices.
2. **Matrix Quarantine Policy**: Strictly quarantine non-soil matrices (industrial effluent, river sediment, foliar vegetation) to prevent cross-matrix distortion of soil baselines.
3. **Zero Silent Imputation**: Ensure unmeasured heavy metals remain `null`/unmeasured rather than falsely imputed as zero.
4. **Standardized Scientific Pollution Indices**: Implement Hakanson (1980) Contamination Factors ($CF$), Müller (1969) Geoaccumulation ($I_{geo}$), and Peninsular Shield geochemical baselines (Awadh et al. / CPCB).
5. **Spatial Uncertainty & Conformal Guarantees**: Provide 90% finite-sample marginal coverage prediction intervals and acknowledge Spatial-CV generalization limits.
6. **Enterprise Monitoring Interface**: Deliver a dark environmental intelligence platform (Linear/Palantir Foundry aesthetic) with responsive multi-tab analytics, interactive Leaflet geospatial maps, and CSV/PDF report generators.

---

## 3. Geographic Scope: 8 Target Industrial Corridors
The platform covers 8 audited industrial zones across Tamil Nadu:
1. **Ranipet SIPCOT** (Ranipet / Vellore): Tanneries, chemical plants, metal plating ($Cr, Pb, Ni$).
2. **Cuddalore SIPCOT** (Cuddalore): Heavy chemicals, agrochemicals, pharmaceuticals, Uppanar basin ($Cd, Cr, Pb$).
3. **Manali Industrial Area** (Tiruvallur / Chennai): Petrochemicals, oil refineries, chemical fertilizers ($Pb, Ni, As$).
4. **Coimbatore SIDCO Kurichi** (Coimbatore): Foundries, electroplating, precision engineering ($Ni, Cr, Zn$).
5. **Tiruppur Textile Corridor** (Tiruppur): Textile wet processing, dyeing, bleaching, CETP sludge ($Cu, Zn, Cr$).
6. **Mettur Industrial Area** (Salem): Chlor-alkali, aluminium smelting, thermal power, Cauvery basin ($Pb, Hg, As$).
7. **Erode Industrial Corridor** (Erode): Textile processing, leather tanning, Kalingarayan canal ($Cr, Cu, Zn$).
8. **Thoothukudi SIPCOT** (Thoothukudi): Heavy metallurgy, copper smelting, thermal power ($Cu, As, Pb$).

---

## 4. System Architecture & Tech Stack

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TAMIL NADU SOILWATCH ARCHITECTURE                    │
└────────────────────────────────────────────────────────────────────────┘

  [FRONTEND CLIENT: HTML5 / CSS3 / Vanilla JS]
   ├── Dark Environmental Intelligence System (Inter / Space Grotesk / JetBrains Mono)
   ├── Multi-Tab Shell: Overview, Pollution Map, Heavy Metals, Soil Health, Risk, Explorer, Reports, Provenance
   ├── Leaflet.js Geospatial Engine (Carto Voyager Dark Tiles, Marker Clustering, Buffer Circles)
   ├── Chart.js Analytics Suite (Dual-Axis Distributions, Radar Profiling, Doughnut Categorization)
   └── Centralized API Client (api.js) with graceful offline fallbacks
            │
            │ REST HTTP (JSON & Streaming CSV)
            ▼
  [BACKEND API: FastAPI 2.0 / Python 3.14]
   ├── Health & Manifest Endpoints (/health, /manifest)
   ├── Executive Summary & KPIs (/dashboard/summary, /analytics/summary)
   ├── In-Situ Samples Service (/samples, /samples/{sample_id})
   ├── Geospatial Map Service (/pollution-map, /industrial-areas)
   ├── Heavy Metals & Statistics (/metals, /metals/{metal}/statistics)
   ├── Soil Health Engine (/soil-health)
   ├── Risk Assessment & Screening Calculator (/assessment)
   ├── Adaptive Sampling & ML Prediction (/predict, /explanation, /sampling-recommendations)
   ├── Data Sources Registry (/data-sources)
   └── Report Generation Engine (/report/generate - JSON & CSV formats)
            │
            │ In-Memory Dataframes / SQLite / Parquet
            ▼
  [DATA PERSISTENCE & ML ARTIFACTS]
   ├── Normalized Parquet/CSV Tables (data/normalized/)
   │    ├── soil_samples.parquet (464 samples)
   │    ├── heavy_metal_results.parquet (3,194 measurement records)
   │    ├── soil_health_results.parquet (464 records)
   │    ├── data_sources.parquet (9 authentic sources)
   │    └── quarantined_samples.parquet (3 non-soil matrices)
   ├── Relational Database: soil_pollution_normalized.db (SQLite)
   └── ML Ensembles: LightGBM / RF / XGBoost + Conformal Quantiles (models/)
```

---

## 5. Startup & Execution Instructions

### A. Run Backend API Server
```powershell
cd "c:\Soil pollution\soil-pollution-ml"
python backend/main.py
```
*The server starts listening on `http://127.0.0.1:8000`.*

### B. Access Interactive Web Application
Open your browser and navigate to:
```
http://127.0.0.1:8000/
```
*(Automatically redirects to `http://127.0.0.1:8000/dashboard/`)*

### C. Run Complete Automated Test Suite
```powershell
cd "c:\Soil pollution\soil-pollution-ml"
python -m pytest tests/ -v
```

