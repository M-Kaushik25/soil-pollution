import os
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(".")
NORM_DIR = os.path.join(BASE_DIR, "data", "normalized")

df_samples = pd.read_parquet(os.path.join(NORM_DIR, "soil_samples.parquet"))
print(f"Total samples rows: {len(df_samples)}")
print(f"Unique sample IDs: {df_samples['sample_id'].nunique()}")

df_metals = pd.read_parquet(os.path.join(NORM_DIR, "heavy_metal_results.parquet"))
print(f"\nTotal heavy metal rows: {len(df_metals)}")
print(f"Metals present in DB:\n{df_metals['metal'].value_counts()}")

from src.analytics.pollution_indices import GEOCHEMICAL_BASELINES

print("\n=== DIRECT METAL STATS ===")
for metal in ['chromium', 'lead', 'cadmium', 'nickel', 'arsenic', 'copper', 'zinc']:
    sub = df_metals[df_metals['metal'] == metal]
    valid_vals = sub['concentration_mg_kg'].dropna()
    valid_count = len(valid_vals)
    nan_count = sub['concentration_mg_kg'].isna().sum()
    zero_count = (valid_vals == 0).sum()
    
    base_info = GEOCHEMICAL_BASELINES.get(metal, {})
    bg = base_info.get("background_mg_kg", 50.0)
    
    if valid_count > 0:
        c_min = float(valid_vals.min())
        c_max = float(valid_vals.max())
        c_mean = float(valid_vals.mean())
        c_med = float(valid_vals.median())
        c_std = float(valid_vals.std())
        cf_mean = c_mean / bg
        igeo_vals = np.log2(valid_vals / (1.5 * bg))
        igeo_mean = float(igeo_vals.mean())
        print(f"{metal:10s}: N={valid_count} (NaN={nan_count}, zero={zero_count}) | min={c_min:.2f}, max={c_max:.2f}, mean={c_mean:.2f}, med={c_med:.2f}, std={c_std:.2f} | CF={cf_mean:.2f}, Igeo={igeo_mean:.2f}")
    else:
        print(f"{metal:10s}: N=0")
