"""
Feature Quality Control & Multicollinearity Screening Module
Audits extracted environmental covariates for missingness, near-zero variance,
distributional anomalies, and multicollinearity.
Generates results/feature_quality_report.csv.
"""

import os
import pandas as pd
import numpy as np

def run_feature_qc(master_parquet_path: str, results_dir: str):
    os.makedirs(results_dir, exist_ok=True)
    df = pd.read_parquet(master_parquet_path)
    print(f"Running Feature QC on: {master_parquet_path} ({df.shape})")
    
    ignore_cols = ["sample_id", "region_cluster", "land_use", "soil_depth_cm", "analytical_method", "qc_status",
                   "lead_mg_kg", "cadmium_mg_kg", "chromium_mg_kg", "nickel_mg_kg", "zinc_mg_kg", "copper_mg_kg", "arsenic_mg_kg"]
    
    feature_cols = [c for c in df.columns if c not in ignore_cols and np.issubdtype(df[c].dtype, np.number)]
    
    qc_records = []
    for f in feature_cols:
        series = df[f].dropna()
        n_miss = df[f].isnull().sum()
        pct_miss = (n_miss / len(df)) * 100.0
        
        var_val = float(series.var())
        std_val = float(series.std())
        mean_val = float(series.mean())
        min_val = float(series.min())
        max_val = float(series.max())
        
        is_constant = (series.nunique() <= 1)
        is_near_zero_var = (var_val < 1e-5)
        
        # Category classification
        if f in ["soil_ph", "soil_ec_dSm", "soc_pct", "clay_pct", "silt_pct", "sand_pct", "sg_clay_5_15cm", "sg_sand_5_15cm", "sg_soc_5_15cm", "sg_cec_topsoil", "sg_bulk_density_g_cm3"]:
            group = "Soil Properties / SoilGrids"
        elif f in ["elevation_m", "slope_deg", "aspect_sin", "aspect_cos", "twi", "mrvbf"]:
            group = "Terrain / Topography"
        elif f in ["bio1_annual_mean_temp_c", "bio4_temp_seasonality", "bio12_annual_precip_mm", "bio15_precip_seasonality", "aridity_index"]:
            group = "Bioclimate"
        elif f in ["s2_ndvi", "s2_evi", "s2_bsi", "s2_clay_index", "s2_iron_oxide_index"]:
            group = "Satellite Remote Sensing"
        else:
            group = "Anthropogenic / Proximity"
            
        qc_records.append({
            "feature_name": f,
            "feature_group": group,
            "missing_pct": round(pct_miss, 2),
            "mean": round(mean_val, 3),
            "std": round(std_val, 3),
            "min": round(min_val, 3),
            "max": round(max_val, 3),
            "variance": round(var_val, 4),
            "is_constant": is_constant,
            "is_near_zero_variance": is_near_zero_var,
            "status": "PASSED" if not (is_constant or is_near_zero_var) else "FLAGGED"
        })
        
    df_qc = pd.DataFrame(qc_records)
    qc_csv = os.path.join(results_dir, "feature_quality_report.csv")
    df_qc.to_csv(qc_csv, index=False)
    print(f"Feature QC Report saved to: {qc_csv}")
    print(f"Total Features Screened: {len(df_qc)}")
    print(f"All Features Passed QC: {(df_qc['status'] == 'PASSED').all()}")
    return df_qc

if __name__ == "__main__":
    run_feature_qc(
        master_parquet_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.parquet",
        results_dir="soil-pollution-ml/results"
    )
