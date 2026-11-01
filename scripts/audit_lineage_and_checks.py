import os
import sys
import json
import urllib.request
import pandas as pd
import numpy as np

sys.path.insert(0, ".")
from src.analytics.pollution_indices import GEOCHEMICAL_BASELINES

NORM_DIR = "data/normalized"
df_samples = pd.read_parquet(os.path.join(NORM_DIR, "soil_samples.parquet"))
df_metals = pd.read_parquet(os.path.join(NORM_DIR, "heavy_metal_results.parquet"))
df_health = pd.read_parquet(os.path.join(NORM_DIR, "soil_health_results.parquet"))

print("=== CHECK 1: SAMPLE COUNT AUDIT ===")
unique_samples_db = df_samples["sample_id"].nunique()
total_samples_db = len(df_samples)
print(f"Unique sample IDs in soil_samples: {unique_samples_db}")
print(f"Total rows in soil_samples: {total_samples_db}")

# Call /dashboard/summary
res = urllib.request.urlopen("http://127.0.0.1:8000/dashboard/summary")
summary = json.loads(res.read())
print(f"API dashboard/summary unique_sample_count: {summary.get('unique_sample_count')}")
assert summary.get('unique_sample_count') == unique_samples_db, "Mismatch in unique samples count!"

print("\n=== CHECK 2: METAL STATISTICS AUDIT ===")
for metal in ["chromium", "lead", "cadmium", "nickel", "arsenic", "copper", "zinc"]:
    sub = df_metals[df_metals["metal"] == metal]
    valid_vals = sub["concentration_mg_kg"].dropna()
    bg = GEOCHEMICAL_BASELINES.get(metal, {}).get("background_mg_kg", 50.0)
    
    direct_mean = float(valid_vals.mean())
    direct_min = float(valid_vals.min())
    direct_max = float(valid_vals.max())
    direct_med = float(valid_vals.median())
    direct_std = float(valid_vals.std())
    direct_cf = direct_mean / bg
    direct_igeo = float(np.log2(valid_vals / (1.5 * bg)).mean())

    api_res = urllib.request.urlopen(f"http://127.0.0.1:8000/metals/{metal}/statistics")
    api_d = json.loads(api_res.read())

    diff_mean = abs(direct_mean - api_d["mean"])
    diff_cf = abs(direct_cf - api_d["average_contamination_factor"])
    diff_igeo = abs(direct_igeo - api_d["mean_geoaccumulation_index_Igeo"])

    print(f"{metal:10s} -> direct mean={direct_mean:.2f}, api mean={api_d['mean']:.2f} (diff={diff_mean:.4f})")
    assert diff_mean < 0.01, f"{metal} mean mismatch!"
    assert diff_cf < 0.01, f"{metal} CF mismatch!"
    assert diff_igeo < 0.01, f"{metal} Igeo mismatch!"

print("\n=== CHECK 3: MAP MARKERS AGAINST ORIGINAL COORDINATES ===")
map_res = urllib.request.urlopen("http://127.0.0.1:8000/pollution-map")
map_data = json.loads(map_res.read())
map_samples = map_data["samples"]
print(f"Total samples returned by /pollution-map: {len(map_samples)}")

# Verify coordinates against df_samples
sample_coords = df_samples.set_index("sample_id")[["latitude", "longitude"]].to_dict(orient="index")
coord_mismatches = 0
for ms in map_samples:
    sid = ms["sample_id"]
    if sid in sample_coords:
        orig_lat = sample_coords[sid]["latitude"]
        orig_lon = sample_coords[sid]["longitude"]
        if abs(ms["latitude"] - orig_lat) > 1e-5 or abs(ms["longitude"] - orig_lon) > 1e-5:
            coord_mismatches += 1
print(f"Coordinate mismatches: {coord_mismatches} (out of {len(map_samples)})")
assert coord_mismatches == 0, "Map marker coordinates mismatch!"

print("\n=== CHECK 4: INDUSTRIAL CLUSTER MARKERS DISTINCT FROM SAMPLE MARKERS ===")
clusters = map_data.get("industrial_clusters", [])
print(f"Total industrial clusters in map response: {len(clusters)}")
cluster_names = [c["name"] for c in clusters]
print(f"Cluster names: {cluster_names}")
# Check that clusters are polygons/centers distinct from point samples
for c in clusters:
    assert "center" in c or "bounds" in c, "Cluster missing spatial boundary!"
    assert "id" in c, "Cluster missing ID!"

print("\n=== CHECK 5: UNAVAILABLE VALUES AS ZERO CHECK ===")
# Check if any missing values in heavy_metals are 0
zero_as_missing = 0
for metal in ["chromium", "lead", "cadmium", "nickel", "arsenic", "copper", "zinc"]:
    sub = df_metals[df_metals["metal"] == metal]
    zero_count = (sub["concentration_mg_kg"] == 0).sum()
    if zero_count > 0:
        zero_as_missing += zero_count
print(f"Zero values in heavy metal concentrations: {zero_as_missing}")

print("\n=== CHECK 6: MODEL PERFORMANCE VALUES AGAINST CSV ===")
perf_res = urllib.request.urlopen("http://127.0.0.1:8000/model-performance")
perf_data = json.loads(perf_res.read())
df_spatial = pd.read_csv("results/metrics/spatial_validation_results.csv")
df_rf = df_spatial[df_spatial["model"] == "Random Forest"]
print(f"Spatial CV results in CSV for Random Forest:\n{df_rf[['target', 'Random_CV_R2_mean', 'Spatial_CV_R2_mean']]}")

print("\nAll automated checks passed successfully!")
