"""
Feature Ablation Experiment Module
Systematically assesses incremental predictive value of environmental covariate tiers:
Model A: Soil only
Model B: Soil + Terrain
Model C: Soil + Terrain + Climate
Model D: Soil + Terrain + Climate + Satellite
Model E: All Features (Soil + Terrain + Climate + Satellite + Anthropogenic)
Generates results/metrics/ablation_results.csv and ablation plots.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

def run_ablation(master_parquet_path: str, results_dir: str, figures_dir: str):
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    df = pd.read_parquet(master_parquet_path)
    
    # Feature group definitions
    soil_feats = ["soil_ph", "soil_ec_dSm", "soc_pct", "clay_pct", "silt_pct", "sand_pct",
                  "sg_clay_5_15cm", "sg_sand_5_15cm", "sg_soc_5_15cm", "sg_cec_topsoil", "sg_bulk_density_g_cm3"]
    terrain_feats = ["elevation_m", "slope_deg", "aspect_sin", "aspect_cos", "twi", "mrvbf"]
    climate_feats = ["bio1_annual_mean_temp_c", "bio4_temp_seasonality", "bio12_annual_precip_mm", "bio15_precip_seasonality", "aridity_index"]
    satellite_feats = ["s2_ndvi", "s2_evi", "s2_bsi", "s2_clay_index", "s2_iron_oxide_index"]
    anthropogenic_feats = ["dist_to_industrial_km", "dist_to_major_road_km", "dist_to_river_km", "pop_density_sqkm", "urban_builtup_fraction"]
    
    ablation_suites = [
        ("Model A: Soil Only", soil_feats),
        ("Model B: Soil + Terrain", soil_feats + terrain_feats),
        ("Model C: Soil + Terr + Clim", soil_feats + terrain_feats + climate_feats),
        ("Model D: Soil + Terr + Clim + Sat", soil_feats + terrain_feats + climate_feats + satellite_feats),
        ("Model E: All Features (Full Master)", soil_feats + terrain_feats + climate_feats + satellite_feats + anthropogenic_feats)
    ]
    
    targets = [
        ("chromium_mg_kg", "Chromium (Cr)"),
        ("lead_mg_kg", "Lead (Pb)"),
        ("cadmium_mg_kg", "Cadmium (Cd)"),
        ("nickel_mg_kg", "Nickel (Ni)")
    ]
    
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    splits = list(cv.split(df))
    
    ablation_records = []
    print("Running Feature Ablation Experiments...")
    
    for target_col, target_name in targets:
        y = df[target_col]
        for suite_name, feat_cols in ablation_suites:
            X = df[feat_cols]
            r2_list, mae_list, rmse_list = [], [], []
            
            for train_idx, val_idx in splits:
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                model = XGBRegressor(n_estimators=100, learning_rate=0.08, max_depth=4, random_state=42, n_jobs=-1)
                model.fit(X_train, np.log1p(y_train))
                preds = np.expm1(model.predict(X_val))
                preds = np.clip(preds, 0.0, None)
                
                r2_list.append(r2_score(y_val, preds))
                mae_list.append(mean_absolute_error(y_val, preds))
                rmse_list.append(np.sqrt(mean_squared_error(y_val, preds)))
                
            ablation_records.append({
                "target": target_name,
                "target_column": target_col,
                "ablation_tier": suite_name,
                "num_features": len(feat_cols),
                "R2_mean": round(float(np.mean(r2_list)), 4),
                "R2_std": round(float(np.std(r2_list)), 4),
                "MAE_mean": round(float(np.mean(mae_list)), 3),
                "RMSE_mean": round(float(np.mean(rmse_list)), 3)
            })
            print(f"[{target_name:14s}] {suite_name:32s} (d={len(feat_cols):2d}) -> R2: {np.mean(r2_list):.3f}, RMSE: {np.mean(rmse_list):.2f}")
            
    df_abl = pd.DataFrame(ablation_records)
    out_csv = os.path.join(results_dir, "ablation_results.csv")
    df_abl.to_csv(out_csv, index=False)
    print(f"\nSaved Ablation Results to: {out_csv}")
    
    # Generate Publication Ablation Figure
    plt.figure(figsize=(14, 7), dpi=300)
    sns.barplot(data=df_abl, x="ablation_tier", y="R2_mean", hue="target", palette="muted")
    plt.title("Environmental Feature Ablation: Incremental Model Performance ($R^2$ Score)")
    plt.xlabel("Predictor Feature Tier")
    plt.ylabel("5-Fold Cross Validation $R^2$ Score")
    plt.xticks(rotation=20, ha='right')
    plt.ylim(0, 1.0)
    plt.legend(title="Target Heavy Metal", loc="upper left")
    plt.tight_layout()
    fig_path = os.path.join(figures_dir, "05_feature_ablation_comparison.png")
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved Ablation Figure to: {fig_path}")
    return df_abl

if __name__ == "__main__":
    run_ablation(
        master_parquet_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.parquet",
        results_dir="soil-pollution-ml/results/metrics",
        figures_dir="soil-pollution-ml/results/figures"
    )
