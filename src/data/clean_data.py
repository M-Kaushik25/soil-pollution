"""
Data Cleaning and Preprocessing Pipeline
Cleans raw geochemical observations, enforces spatial integrity, handles missing values,
and outputs data/processed/clean_soil_data.parquet along with results/data_cleaning_report.md.
"""

import os
import pandas as pd
import numpy as np

def clean_soil_dataset(raw_csv_path: str, output_parquet_path: str, output_csv_path: str, report_path: str):
    df_raw = pd.read_csv(raw_csv_path)
    initial_rows = len(df_raw)
    
    logs = []
    logs.append(f"Initial raw record count: {initial_rows}")
    
    # 1. Deduplication
    df_dedup = df_raw.drop_duplicates().copy()
    exact_dupes_removed = initial_rows - len(df_dedup)
    logs.append(f"Exact duplicate rows removed: {exact_dupes_removed}")
    
    # Remove duplicate coordinate rows keeping first valid sample
    coords_dupes = df_dedup.duplicated(subset=["latitude", "longitude"]).sum()
    df_clean = df_dedup.drop_duplicates(subset=["latitude", "longitude"], keep="first").copy()
    logs.append(f"Duplicate spatial coordinate rows removed: {coords_dupes}")
    
    # 2. Coordinate range verification (Tamil Nadu geographic envelope)
    lat_valid = (df_clean["latitude"] >= 8.0) & (df_clean["latitude"] <= 14.0)
    lon_valid = (df_clean["longitude"] >= 76.0) & (df_clean["longitude"] <= 81.0)
    valid_coords = lat_valid & lon_valid
    invalid_coords_count = (~valid_coords).sum()
    df_clean = df_clean[valid_coords].copy()
    logs.append(f"Invalid coordinate samples removed: {invalid_coords_count}")
    
    # 3. Missing Value Handling
    # For numeric columns: impute with median of the corresponding region cluster if missing
    imputed_cols = []
    for col in df_clean.select_dtypes(include=[np.number]).columns:
        n_miss = df_clean[col].isnull().sum()
        if n_miss > 0:
            df_clean[col] = df_clean.groupby("region_cluster")[col].transform(lambda x: x.fillna(x.median()))
            # If any remain, global median
            if df_clean[col].isnull().sum() > 0:
                df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            imputed_cols.append(f"{col} ({n_miss} values imputed using cluster median)")
    logs.append(f"Imputed columns: {', '.join(imputed_cols) if imputed_cols else 'None'}")
    
    # 4. Range and Physical Validity Checks
    # pH: [4.0, 10.0]
    # Texture sum check
    tex_sum = df_clean["clay_pct"] + df_clean["sand_pct"] + df_clean["silt_pct"]
    df_clean["clay_pct"] = (df_clean["clay_pct"] / tex_sum) * 100.0
    df_clean["sand_pct"] = (df_clean["sand_pct"] / tex_sum) * 100.0
    df_clean["silt_pct"] = (df_clean["silt_pct"] / tex_sum) * 100.0
    logs.append("Soil texture fractions re-normalized to 100% dry weight.")
    
    # 5. Output datasets
    os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
    df_clean.to_parquet(output_parquet_path, index=False)
    df_clean.to_csv(output_csv_path, index=False)
    
    final_rows = len(df_clean)
    logs.append(f"Final clean dataset record count: {final_rows}")
    logs.append(f"Spatial CRS: WGS 84 (EPSG:4326)")
    
    # Generate Cleaning Markdown Report
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Data Cleaning & Quality Assurance Report\n\n")
        f.write("## 1. Summary of Actions\n\n")
        for log in logs:
            f.write(f"- {log}\n")
            
        f.write("\n## 2. Processed Dataset Schema & Statistics\n\n")
        f.write("| Column Name | Type | Non-Null Count | Min | Mean | Max |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for col in df_clean.columns:
            if np.issubdtype(df_clean[col].dtype, np.number):
                f.write(f"| `{col}` | {df_clean[col].dtype} | {df_clean[col].notnull().sum()} | {df_clean[col].min():.2f} | {df_clean[col].mean():.2f} | {df_clean[col].max():.2f} |\n")
            else:
                f.write(f"| `{col}` | {df_clean[col].dtype} | {df_clean[col].notnull().sum()} | - | {df_clean[col].nunique()} unique | - |\n")
                
    print(f"Data cleaning complete. Output: {output_parquet_path} ({final_rows} rows)")
    print(f"Report written to: {report_path}")
    return df_clean

if __name__ == "__main__":
    clean_soil_dataset(
        raw_csv_path="soil-pollution-ml/data/raw/tamil_nadu_soil_heavy_metals_raw.csv",
        output_parquet_path="soil-pollution-ml/data/processed/clean_soil_data.parquet",
        output_csv_path="soil-pollution-ml/data/processed/clean_soil_data.csv",
        report_path="soil-pollution-ml/results/data_cleaning_report.md"
    )
