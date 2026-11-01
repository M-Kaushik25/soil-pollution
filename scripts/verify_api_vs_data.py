import os
import sys
import json
import urllib.request
import pandas as pd
import numpy as np

sys.path.insert(0, ".")
from src.analytics.pollution_indices import GEOCHEMICAL_BASELINES

# Check 1: Dashboard sample count against actual unique valid sample IDs
df_samples = pd.read_parquet("data/normalized/soil_samples.parquet")
actual_unique_ids = df_samples["sample_id"].nunique()
actual_total_rows = len(df_samples)

summary_res = urllib.request.urlopen("http://127.0.0.1:8000/dashboard/summary")
summary = json.loads(summary_res.read())

print(f"=== CHECK 1: SAMPLE COUNT ===")
print(f"Dashboard summary 'total_records': {summary['total_records']}")
print(f"Dashboard summary 'unique_samples': {summary['unique_samples']}")
print(f"Actual unique sample IDs in parquet: {actual_unique_ids}")
print(f"Actual total rows in parquet: {actual_total_rows}")

# Check 2: Metal statistics vs direct dataset calculations
df_metals = pd.read_parquet("data/normalized/heavy_metal_results.parquet")
print(f"\n=== CHECK 2: METAL STATISTICS ===")
for metal in ["chromium", "lead", "cadmium", "nickel", "arsenic", "copper", "zinc"]:
    sub = df_metals[df_metals["metal"] == metal]
    valid_vals = sub["concentration_mg_kg"].dropna()
    c_min = float(valid_vals.min())
    c_max = float(valid_vals.max())
    c_mean = float(valid_vals.mean())
    c_med = float(valid_vals.median())
    c_std = float(valid_vals.std())
    bg = GEOCHEMICAL_BASELINES.get(metal, {}).get("background_mg_kg", 50.0)
    cf_mean = c_mean / bg
    igeo_vals = np.log2(valid_vals / (1.5 * bg))
    igeo_mean = float(igeo_vals.mean())

    api_res = urllib.request.urlopen(f"http://127.0.0.1:8000/metals/{metal}/statistics")
    api_d = json.loads(api_res.read())

    print(f"Metal: {metal}")
    print(f"  Parquet: N={len(valid_vals)}, min={c_min:.2f}, max={c_max:.2f}, mean={c_mean:.2f}, med={c_med:.2f}, std={c_std:.2f}, CF={cf_mean:.2f}, Igeo={igeo_mean:.2f}")
    print(f"  API    : N={api_d['valid_sample_count']}, min={api_d['min']:.2f}, max={api_d['max']:.2f}, mean={api_d['mean']:.2f}, med={api_d['median']:.2f}, std={api_d['std_dev']:.2f}, CF={api_d['average_contamination_factor']:.2f}, Igeo={api_d['mean_geoaccumulation_index_Igeo']:.2f}")
