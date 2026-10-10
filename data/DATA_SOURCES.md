# Data Sources and Lineage Registry

## 1. Primary In-Situ Soil Geochemical Dataset

* **Dataset Identifier:** `TNAU-TNSOIL-HM-2024`
* **Dataset Name:** Tamil Nadu Regional Soil Heavy-Metal & Geochemical Survey
* **Storage Location:** `data/raw/tamil_nadu_soil_heavy_metals_raw.csv`
* **File Format:** CSV (Comma Separated Values), UTF-8
* **SHA-256 Checksum:** `1262804b118c25973301cbcb31800244e1377c1f0d73869b02974d0b76fd19b2`
* **Acquisition Date:** 2026-09-02
* **Geographic Coverage:** Tamil Nadu, India ($10.0^\circ\text{N} - 13.5^\circ\text{N}, 76.8^\circ\text{E} - 80.2^\circ\text{E}$)
* **Sample Count:** 451 raw records (448 unique georeferenced topsoil samples)
* **Depth Interval:** $0\text{–}15\text{ cm}$ (Topsoil)
* **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0)
* **Analytical Protocol:** Strong Acid Digestion ($\text{HNO}_3 + \text{HClO}_4 + \text{HF}$, EPA Method 3050B) with Inductively Coupled Plasma Mass Spectrometry (ICP-MS) and Atomic Absorption Spectrophotometry (AAS).
* **Target Pollutants:** Lead ($\text{Pb}$), Cadmium ($\text{Cd}$), Chromium ($\text{Cr}$), Nickel ($\text{Ni}$), Zinc ($\text{Zn}$), Copper ($\text{Cu}$), Arsenic ($\text{As}$) in $\text{mg/kg}$ dry soil.

---

## 2. External Environmental Covariates Lineage

### A. Digital Elevation Model (DEM) & Topography
* **Source:** NASA SRTM v3.0 / Copernicus DEM GLO-30
* **Variables:** Elevation ($\text{m}$), Slope ($^\circ$), Aspect (degrees / sin-cos components), Topographic Wetness Index ($\text{TWI}$), Multiresolution Index of Valley Bottom Flatness ($\text{MrVBF}$).
* **Spatial Resolution:** $30\text{ m}$ / $250\text{ m}$ aggregated.

### B. SoilGrids 250m Global Soil Properties (ISRIC)
* **Source:** ISRIC — World Soil Information (SoilGrids 2.0)
* **Variables:**
  - Sand, Silt, Clay fractions ($\text{g/kg}$) at $0\text{–}5\text{ cm}$ and $5\text{–}15\text{ cm}$
  - Soil Organic Carbon content ($\text{SOC}, \text{dg/kg}$)
  - Cation Exchange Capacity ($\text{CEC}, \text{mmol(c)/kg}$)
  - Soil pH in $\text{H}_2\text{O}$ ($\text{pH} \times 10$)
  - Bulk Density of the fine earth fraction ($\text{cg/cm}^3$)

### C. High-Resolution Bioclimatic Variables (WorldClim v2.1 / CHELSA)
* **Source:** WorldClim 2.1 (Fick & Hijmans) / CHELSA Bioclim
* **Variables:**
  - `bio_1`: Annual Mean Temperature ($^\circ\text{C}$)
  - `bio_4`: Temperature Seasonality ($\text{Standard Deviation} \times 100$)
  - `bio_12`: Annual Precipitation ($\text{mm}$)
  - `bio_15`: Precipitation Seasonality (Coefficient of Variation)

### D. Multi-Spectral Remote Sensing (Sentinel-2 Harmonized)
* **Source:** European Space Agency (ESA) Copernicus Sentinel-2 MSI
* **Spectral Indices Extracted:**
  - $\text{NDVI} = \frac{\text{B8} - \text{B4}}{\text{B8} + \text{B4}}$ (Normalized Difference Vegetation Index)
  - $\text{EVI} = 2.5 \times \frac{\text{B8} - \text{B4}}{\text{B8} + 6\text{B4} - 7.5\text{B2} + 1}$ (Enhanced Vegetation Index)
  - $\text{BSI} = \frac{(\text{B11} + \text{B4}) - (\text{B8} + \text{B2})}{(\text{B11} + \text{B4}) + (\text{B8} + \text{B2})}$ (Bare Soil Index)
  - $\text{CMI} = \frac{\text{B11}}{\text{B12}}$ (Clay Mineral Index)
  - $\text{IOI} = \frac{\text{B4}}{\text{B2}}$ (Iron Oxide Index)

### E. Anthropogenic & Proximity Predictors
* **Source:** OpenStreetMap (OSM) & Global Human Settlement Layer (GHSL)
* **Variables:**
  - `dist_to_industrial_km`: Euclidean distance to nearest industrial cluster / SEZ
  - `dist_to_major_road_km`: Distance to National / State Highways
  - `dist_to_river_km`: Distance to major drainage network (Noyyal, Cauvery, Palar, Vaigai)
  - `population_density_sqkm`: Ambient population density per square kilometer

---

## 3. Data Governance & Integrity Rule
1. Raw data files stored in `data/raw/` are strictly write-protected and immutable.
2. All preprocessing, coordinate checks, transformations, and imputations are logged inside reproducible scripts under `src/data/` and `src/features/`.
3. Processed parquet files in `data/processed/` are compiled deterministically with explicit random seeds.
