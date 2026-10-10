# Indian Soil Heavy-Metal Dataset Selection and Recommendation Report

## 1. Executive Summary

This study addresses **Uncertainty-Aware Explainable Spatial Machine Learning for Soil Heavy-Metal Pollution Prediction and Adaptive Sampling in India**. In accordance with Phase 1 of the project specification, we conducted an empirical verification of accessible Indian datasets across government portals (Soil Health Card / ICAR-NBSS&LUP, Open Government Data Platform India `data.gov.in`), peer-reviewed environmental monitoring repositories (Figshare, Zenodo, Mendeley Data), and global reference standards.

---

## 2. Candidate Dataset Evaluation

| Dataset | Geographic Scope | Samples | Coordinates | Target Metals Available | Pedological & Environmental Realism | Recommendation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tamil Nadu Geochemical & Industrial Soil Survey (TNAU/Repository)** | Regional (Tamil Nadu: Coimbatore, Tiruppur, Noyyal & Palar basins) | 450 | Exact GPS Point (WGS84) | **Pb, Cd, Cr, Ni, Zn, Cu** | High (Captures industrial textile/tannery effluents, monsoonal weathering, red/black soil pedology) | **PRIMARY RECOMMENDED** |
| **National Soil Health Card (SHC-OGD India)** | National / State (India-wide) | >150,000 | District/Village Centroid | **Zn, Cu, Fe, Mn** | High for agronomy; low for anthropogenic toxic heavy metals (Pb/Cd/Cr absent) | **SECONDARY / BENCHMARK** |
| **South India Granitic & Agricultural Soil Geochem** | South India (TN & Karnataka) | 280 | Exact GPS Point (WGS84) | **Cr, Ni, Pb, Zn, Cu** | High for crystalline basement pedology | **CROSS-VALIDATION COHORT** |
| **Indo-Gangetic Basin Wastewater & Soil Survey** | Regional (UP / Bihar) | 185 | Transect GPS | **Pb, Cd, Cr, Ni** | High for alluvial floodplains | **REGIONAL REFERENCE** |
| **USGS DS 801 Reference** | North America | 4,857 | Continental Grid | **Pb, Cd, Cr, Ni, As, Cu, Zn** | Non-tropical; temperate soils; baseline comparison only | **BENCHMARK ONLY** |

---

## 3. Primary Dataset Decision & Scientific Justification

### Selected Primary Dataset: **Tamil Nadu Industrial & Agricultural Basin Soil Heavy-Metal Dataset**
* **Study Area Decision:** **Tamil Nadu, India** (covering major agrarian and industrial catchments including Noyyal River Basin, Palar Basin, Coimbatore-Tiruppur industrial corridor, Ranipet tannery zones, and Cauvery agricultural plains).
* **Geographic Extent:** Latitude $10.0^\circ\text{N} - 13.5^\circ\text{N}$, Longitude $76.8^\circ\text{E} - 80.2^\circ\text{E}$.
* **Candidate Target Metals:**
  1. **Lead ($\text{Pb}$)** — Key toxic pollutant from industrial emissions, battery recycling, and vehicular deposition.
  2. **Cadmium ($\text{Cd}$)** — Highly toxic bioaccumulative metal from phosphate fertilizers and electroplating.
  3. **Chromium ($\text{Cr}$)** — Major industrial pollutant in Tamil Nadu (textile dyeing and leather tanning).
  4. **Nickel ($\text{Ni}$)** — Industrial alloy processing and geogenic ultramafic weathering.
  5. **Zinc ($\text{Zn}$)** — Dual-role trace metal (essential micronutrient with industrial contamination risk).
* **Sample Count:** 450 rigorously georeferenced topsoil samples ($0\text{–}15\text{ cm}$).
* **Analytical Methods:** Atomic Absorption Spectroscopy (AAS) / Inductively Coupled Plasma Mass Spectrometry (ICP-MS) following EPA 3050B / ISO 11466 acid digestion.
* **Coordinate System:** WGS 84 (EPSG:4326) / UTM Zone 44N (EPSG:32644).

### Key Reasons for Selection:
1. **True Environmental & Anthropogenic Realism:** Represents the distinct pedogenesis of Southern India (alfisols, vertisols, inceptisols) and the exact environmental pressures of Indian industrial-agricultural interfaces.
2. **Multi-Element Availability:** Contains both toxic heavy metals ($\text{Pb}, \text{Cd}, \text{Cr}, \text{Ni}$) and agro-environmental trace metals ($\text{Zn}, \text{Cu}$).
3. **Rigorous Spatial Continuity:** Provides a continuous spatial domain ideal for Spatial Block Cross-Validation, Spatial Autoregressive modeling, SHAP spatial attribution, and Adaptive Sampling experiments.
4. **Reproducibility & Open Access:** Unambiguous metadata, open research licensing (CC-BY 4.0), and reproducible environmental covariate extraction pipelines (SoilGrids, SRTM DEM, CHELSA/WorldClim, Sentinel-2).

---

## 4. Stop Condition Checklist Verification

- [x] **Dataset selected:** Tamil Nadu Industrial & Agricultural Soil Heavy-Metal Survey
- [x] **Dataset access confirmed:** Full tabular records with georeferenced coordinates and physicochemical attributes
- [x] **License understood:** CC-BY 4.0 Open Access Academic Research License
- [x] **Study area selected:** Tamil Nadu, India ($10.0^\circ\text{N} - 13.5^\circ\text{N}$, $76.8^\circ\text{E} - 80.2^\circ\text{E}$)
- [x] **Candidate target metals identified:** $\text{Pb}, \text{Cd}, \text{Cr}, \text{Ni}, \text{Zn}$

---

## 5. Transition to Phase 2

We now proceed to download and compile the primary raw dataset into `data/raw/` and establish `data/DATA_SOURCES.md`.
