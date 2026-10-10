"""
Data Audit Module
Conducts comprehensive quality auditing and statistical profiling on raw soil data.
Generates results/data_quality_report.csv and results/metal_availability_report.csv.
"""

import os
import pandas as pd
import numpy as np
from scipy import stats

def run_data_audit(raw_csv_path: str, results_dir: str):
    os.makedirs(results_dir, exist_ok=True)
    df = pd.read_csv(raw_csv_path)
    print(f"Auditing raw dataset from: {raw_csv_path}")
    print(f"Dataset Shape: {df.shape}")
    
    # 1. Overall Data Quality Report
    quality_records = []
    for col in df.columns:
        col_type = str(df[col].dtype)
        n_missing = df[col].isnull().sum()
        pct_missing = round((n_missing / len(df)) * 100.0, 2)
        n_unique = df[col].nunique()
        quality_records.append({
            "column_name": col,
            "data_type": col_type,
            "total_count": len(df),
            "missing_count": n_missing,
            "missing_pct": pct_missing,
            "unique_values": n_unique,
            "is_constant": n_unique <= 1
        })
        
    df_quality = pd.DataFrame(quality_records)
    quality_csv = os.path.join(results_dir, "data_quality_report.csv")
    df_quality.to_csv(quality_csv, index=False)
    print(f"Saved: {quality_csv}")
    
    # Check duplicates
    duplicate_rows = df.duplicated().sum()
    duplicate_coords = df.duplicated(subset=["latitude", "longitude"]).sum()
    print(f"Exact Duplicate Rows: {duplicate_rows}")
    print(f"Duplicate Coordinates: {duplicate_coords}")
    
    # 2. Metal Availability and Geochemical Profiling
    metals = [
        ("lead_mg_kg", "Pb"),
        ("cadmium_mg_kg", "Cd"),
        ("chromium_mg_kg", "Cr"),
        ("nickel_mg_kg", "Ni"),
        ("zinc_mg_kg", "Zn"),
        ("copper_mg_kg", "Cu"),
        ("arsenic_mg_kg", "As")
    ]
    
    metal_records = []
    lat_min, lat_max = df["latitude"].min(), df["latitude"].max()
    lon_min, lon_max = df["longitude"].min(), df["longitude"].max()
    spatial_bbox_str = f"[{lat_min:.2f}-{lat_max:.2f}N, {lon_min:.2f}-{lon_max:.2f}E]"
    
    for col, symbol in metals:
        series = df[col].dropna()
        n_valid = len(series)
        n_missing = df[col].isnull().sum()
        pct_missing = round((n_missing / len(df)) * 100.0, 2)
        
        mean_val = float(series.mean())
        med_val = float(series.median())
        std_val = float(series.std())
        min_val = float(series.min())
        max_val = float(series.max())
        
        q25 = float(np.percentile(series, 25))
        q75 = float(np.percentile(series, 75))
        iqr_val = float(q75 - q25)
        skew_val = float(stats.skew(series))
        
        # Spatial coverage for non-null instances
        valid_df = df[df[col].notnull()]
        spatial_cov = f"{valid_df['region_cluster'].nunique()} clusters / {spatial_bbox_str}"
        
        metal_records.append({
            "metal": symbol,
            "column": col,
            "count": n_valid,
            "missing_count": n_missing,
            "missing_percentage": pct_missing,
            "mean": round(mean_val, 2),
            "median": round(med_val, 2),
            "std": round(std_val, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "IQR": round(iqr_val, 2),
            "skewness": round(skew_val, 3),
            "spatial_coverage": spatial_cov
        })
        
    df_metals = pd.DataFrame(metal_records)
    metal_csv = os.path.join(results_dir, "metal_availability_report.csv")
    df_metals.to_csv(metal_csv, index=False)
    print(f"Saved: {metal_csv}")
    print("\n--- Metal Availability Summary ---")
    print(df_metals[["metal", "count", "missing_percentage", "mean", "median", "skewness"]])
    return df_quality, df_metals

if __name__ == "__main__":
    run_data_audit("soil-pollution-ml/data/raw/tamil_nadu_soil_heavy_metals_raw.csv", "soil-pollution-ml/results")
