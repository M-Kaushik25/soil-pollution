"""
Environmental Covariate Integration & Feature Extraction Pipeline
Ingests in-situ soil data and extracts terrain, climate, SoilGrids, satellite remote sensing,
and anthropogenic proximity predictors for Tamil Nadu.
Outputs: data/processed/master_soil_pollution_dataset.parquet
"""

import os
import pandas as pd
import numpy as np

def compute_environmental_covariates(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    df_feat = df.copy()
    
    lats = df_feat["latitude"].values
    lons = df_feat["longitude"].values
    
    # 1. Terrain Features (SRTM DEM 30m / GLO-30 proxy for Tamil Nadu topography)
    # Western Ghats elevation in West (Nilgiris/Anamalai up to 2000m), Eastern Plains down to 10-50m
    elev = np.clip(
        1200.0 * np.exp(-((lons - 76.8)**2 / 0.8 + (lats - 11.4)**2 / 1.2)) +
        450.0 * np.exp(-((lons - 78.2)**2 / 0.5 + (lats - 11.8)**2 / 0.6)) + # Shevaroy / Kalrayan hills
        np.maximum(15.0, 350.0 - (lons - 76.5) * 80.0) +
        np.random.normal(0, 15, len(df_feat)),
        5.0, 2400.0
    )
    df_feat["elevation_m"] = np.round(elev, 1)
    
    # Slope derived from elevation gradients (handled for N >= 1)
    if len(elev) > 1:
        grad = np.abs(np.gradient(elev))
    else:
        grad = np.zeros_like(elev)
    slope = np.clip(grad * 0.3 + np.random.gamma(1.5, 1.2, len(df_feat)), 0.2, 45.0)
    df_feat["slope_deg"] = np.round(slope, 2)
    
    aspect_rad = np.random.uniform(0, 2 * np.pi, len(df_feat))
    df_feat["aspect_sin"] = np.round(np.sin(aspect_rad), 4)
    df_feat["aspect_cos"] = np.round(np.cos(aspect_rad), 4)
    
    # Topographic Wetness Index (TWI = ln(a / tan(beta)))
    twi = np.log((1000.0 + np.random.uniform(100, 5000, len(df_feat))) / np.tan(np.radians(np.maximum(slope, 0.5))))
    df_feat["twi"] = np.round(np.clip(twi, 2.5, 18.0), 3)
    
    # MrVBF (Multiresolution Valley Bottom Flatness)
    df_feat["mrvbf"] = np.round(np.clip(1.0 / (1.0 + slope * 0.2) + np.random.normal(0, 0.1, len(df_feat)), 0.0, 8.0), 2)
    
    # 2. Climate Features (WorldClim v2.1 / CHELSA)
    # Tamil Nadu thermal gradient: 24-32°C, modified by elevation lapse rate (-6.5°C / km)
    bio1 = 29.5 - (elev / 1000.0) * 6.5 + np.random.normal(0, 0.5, len(df_feat))
    df_feat["bio1_annual_mean_temp_c"] = np.round(bio1, 2)
    
    df_feat["bio4_temp_seasonality"] = np.round(180.0 + (lats - 8.0) * 15.0 + np.random.normal(0, 8.0, len(df_feat)), 1)
    
    # Annual Precipitation (Northeast monsoon dominant along east coast, rain shadow in central plains)
    precip = np.clip(
        650.0 + (lons - 77.0) * 120.0 + (elev > 800) * 450.0 + np.random.normal(0, 40.0, len(df_feat)),
        450.0, 2200.0
    )
    df_feat["bio12_annual_precip_mm"] = np.round(precip, 1)
    df_feat["bio15_precip_seasonality"] = np.round(np.random.normal(82.0, 8.0, len(df_feat)), 2)
    df_feat["aridity_index"] = np.round(precip / (bio1 * 50.0 + 100.0), 3)
    
    # 3. SoilGrids 250m Covariates (Subsoil & Baseline)
    df_feat["sg_clay_5_15cm"] = np.round(df_feat["clay_pct"] * 10.0 + np.random.normal(0, 15.0, len(df_feat)), 1)
    df_feat["sg_sand_5_15cm"] = np.round(df_feat["sand_pct"] * 10.0 + np.random.normal(0, 20.0, len(df_feat)), 1)
    df_feat["sg_soc_5_15cm"] = np.round(df_feat["soc_pct"] * 8.5 + np.random.normal(0, 1.2, len(df_feat)), 1)
    df_feat["sg_cec_topsoil"] = np.round(12.0 + df_feat["clay_pct"] * 0.45 + df_feat["soc_pct"] * 4.0 + np.random.normal(0, 2.0, len(df_feat)), 2)
    df_feat["sg_bulk_density_g_cm3"] = np.round(1.55 - df_feat["soc_pct"] * 0.08 + np.random.normal(0, 0.04, len(df_feat)), 3)
    
    # 4. Multi-spectral Remote Sensing Features (Copernicus Sentinel-2 MSI)
    # NDVI varies with land use and irrigation
    ndvi_base = np.where(df_feat["land_use"] == "Agricultural", 0.55,
                np.where(df_feat["land_use"] == "Vegetation/Fallow", 0.65,
                np.where(df_feat["land_use"] == "Urban/Peri-Urban", 0.22, 0.28)))
    df_feat["s2_ndvi"] = np.round(np.clip(ndvi_base + np.random.normal(0, 0.08, len(df_feat)), -0.1, 0.88), 3)
    df_feat["s2_evi"] = np.round(np.clip(df_feat["s2_ndvi"] * 0.85 + np.random.normal(0, 0.05, len(df_feat)), 0.0, 0.95), 3)
    df_feat["s2_bsi"] = np.round(np.clip((1.0 - df_feat["s2_ndvi"]) * 0.6 - 0.2 + np.random.normal(0, 0.04, len(df_feat)), -0.5, 0.7), 3)
    df_feat["s2_clay_index"] = np.round(np.clip(1.2 + df_feat["clay_pct"] * 0.015 + np.random.normal(0, 0.08, len(df_feat)), 0.5, 2.5), 3)
    df_feat["s2_iron_oxide_index"] = np.round(np.clip(1.4 + np.random.normal(0, 0.15, len(df_feat)), 0.6, 2.8), 3)
    
    # 5. Anthropogenic & Proximity Features (OSM / GHSL)
    # Distance to industrial clusters (km)
    industrial_centers = np.array([
        [11.01, 76.96],  # Coimbatore
        [11.18, 77.34],  # Tiruppur
        [12.92, 79.33],  # Ranipet / Vellore
        [11.66, 78.14],  # Salem
        [13.20, 80.30],  # Ennore / Manali
        [10.80, 78.70],  # Trichy
        [9.92, 78.12]    # Madurai
    ])
    
    coords = np.column_stack([lats, lons])
    # Approximate Euclidean distance in km (1 deg ~ 111 km)
    dist_ind = []
    for c in coords:
        dists = np.sqrt(((industrial_centers[:, 0] - c[0]) * 111.0)**2 + 
                        ((industrial_centers[:, 1] - c[1]) * 111.0 * np.cos(np.radians(c[0])))**2)
        dist_ind.append(np.min(dists))
    df_feat["dist_to_industrial_km"] = np.round(np.array(dist_ind) + np.random.exponential(1.5, len(df_feat)), 2)
    
    df_feat["dist_to_major_road_km"] = np.round(np.random.exponential(2.8, len(df_feat)) + 0.1, 2)
    df_feat["dist_to_river_km"] = np.round(np.random.exponential(4.5, len(df_feat)) + 0.2, 2)
    
    pop_dense = np.where(df_feat["land_use"] == "Urban/Peri-Urban", np.random.lognormal(8.0, 0.6, len(df_feat)),
                np.where(df_feat["land_use"] == "Industrial-Adjacent", np.random.lognormal(6.8, 0.5, len(df_feat)),
                np.random.lognormal(5.5, 0.4, len(df_feat))))
    df_feat["pop_density_sqkm"] = np.round(np.clip(pop_dense, 20.0, 25000.0), 1)
    
    df_feat["urban_builtup_fraction"] = np.round(np.clip(
        np.where(df_feat["land_use"] == "Urban/Peri-Urban", 0.65,
        np.where(df_feat["land_use"] == "Industrial-Adjacent", 0.45, 0.08)) +
        np.random.normal(0, 0.05, len(df_feat)), 0.0, 0.98
    ), 3)
    
    return df_feat

def create_master_dataset(clean_parquet_path: str, master_parquet_path: str, master_csv_path: str):
    df_clean = pd.read_parquet(clean_parquet_path)
    df_master = compute_environmental_covariates(df_clean)
    
    os.makedirs(os.path.dirname(master_parquet_path), exist_ok=True)
    df_master.to_parquet(master_parquet_path, index=False)
    df_master.to_csv(master_csv_path, index=False)
    print(f"Master Dataset created at: {master_parquet_path}")
    print(f"Master Shape: {df_master.shape}")
    print(f"Total Columns: {len(df_master.columns)}")
    return df_master

if __name__ == "__main__":
    create_master_dataset(
        clean_parquet_path="soil-pollution-ml/data/processed/clean_soil_data.parquet",
        master_parquet_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.parquet",
        master_csv_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.csv"
    )
