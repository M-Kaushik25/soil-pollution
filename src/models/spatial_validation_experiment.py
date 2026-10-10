"""
Spatial Cross-Validation vs Random Cross-Validation Experiment Module
Evaluates spatial generalization gap and autocorrelation bias.
Compares Random 5-Fold CV vs Spatial Block 5-Fold CV across all target heavy metals.
Generates results/metrics/spatial_validation_results.csv and spatial validation figures.
"""

import os
import sys
# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from src.models.spatial_cv import SpatialBlockKFold

def run_spatial_validation_experiment(master_parquet_path: str, results_dir: str, figures_dir: str):
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)
    df = pd.read_parquet(master_parquet_path)
    
    ignore_cols = [
        "sample_id", "region_cluster", "land_use", "soil_depth_cm", "analytical_method", "qc_status",
        "lead_mg_kg", "cadmium_mg_kg", "chromium_mg_kg", "nickel_mg_kg", "zinc_mg_kg", "copper_mg_kg", "arsenic_mg_kg"
    ]
    feature_cols = [c for c in df.columns if c not in ignore_cols and np.issubdtype(df[c].dtype, np.number)]
    X = df[feature_cols]
    
    targets = [
        ("chromium_mg_kg", "Chromium (Cr)"),
        ("lead_mg_kg", "Lead (Pb)"),
        ("cadmium_mg_kg", "Cadmium (Cd)"),
        ("nickel_mg_kg", "Nickel (Ni)")
    ]
    
    models = [
        ("Random Forest", RandomForestRegressor, {"n_estimators": 100, "random_state": 42, "n_jobs": -1}),
        ("XGBoost", XGBRegressor, {"n_estimators": 100, "learning_rate": 0.08, "max_depth": 4, "random_state": 42, "n_jobs": -1}),
        ("LightGBM", LGBMRegressor, {"n_estimators": 100, "learning_rate": 0.08, "max_depth": 4, "random_state": 42, "verbose": -1, "n_jobs": -1})
    ]
    
    # 1. Splitters
    random_cv = KFold(n_splits=5, shuffle=True, random_state=42)
    spatial_cv = SpatialBlockKFold(n_splits=5, random_state=42)
    
    random_splits = list(random_cv.split(X))
    spatial_splits = list(spatial_cv.split(X, coords=df[["latitude", "longitude"]].values))
    
    # Plot Spatial Block Assignment
    plt.figure(figsize=(10, 8), dpi=300)
    plt.scatter(
        df["longitude"], df["latitude"],
        c=spatial_cv.cluster_labels_, cmap="tab10", s=60, edgecolor="black", linewidth=0.5, alpha=0.9
    )
    plt.title("Spatial Block Cross-Validation Partitions (Tamil Nadu)")
    plt.xlabel("Longitude (°E)")
    plt.ylabel("Latitude (°N)")
    plt.colorbar(label="Spatial Block ID (Fold 0-4)")
    plt.tight_layout()
    block_fig_path = os.path.join(figures_dir, "06_spatial_blocks_map.png")
    plt.savefig(block_fig_path)
    plt.close()
    print(f"Saved: {block_fig_path}")
    
    records = []
    print("\n--- Running Random CV vs Spatial Block CV Comparison ---")
    
    for target_col, target_name in targets:
        y = df[target_col]
        for model_name, model_cls, kwargs in models:
            # A. Random CV evaluation
            r_r2, r_mae, r_rmse = [], [], []
            for train_idx, val_idx in random_splits:
                m = model_cls(**kwargs)
                m.fit(X.iloc[train_idx], np.log1p(y.iloc[train_idx]))
                preds = np.expm1(m.predict(X.iloc[val_idx]))
                preds = np.clip(preds, 0.0, None)
                r_r2.append(r2_score(y.iloc[val_idx], preds))
                r_mae.append(mean_absolute_error(y.iloc[val_idx], preds))
                r_rmse.append(np.sqrt(mean_squared_error(y.iloc[val_idx], preds)))
                
            # B. Spatial Block CV evaluation
            s_r2, s_mae, s_rmse = [], [], []
            for train_idx, val_idx in spatial_splits:
                m = model_cls(**kwargs)
                m.fit(X.iloc[train_idx], np.log1p(y.iloc[train_idx]))
                preds = np.expm1(m.predict(X.iloc[val_idx]))
                preds = np.clip(preds, 0.0, None)
                s_r2.append(r2_score(y.iloc[val_idx], preds))
                s_mae.append(mean_absolute_error(y.iloc[val_idx], preds))
                s_rmse.append(np.sqrt(mean_squared_error(y.iloc[val_idx], preds)))
                
            spatial_gap_r2 = np.mean(r_r2) - np.mean(s_r2)
            
            records.append({
                "target": target_name,
                "target_column": target_col,
                "model": model_name,
                "Random_CV_R2_mean": round(float(np.mean(r_r2)), 4),
                "Random_CV_R2_std": round(float(np.std(r_r2)), 4),
                "Spatial_CV_R2_mean": round(float(np.mean(s_r2)), 4),
                "Spatial_CV_R2_std": round(float(np.std(s_r2)), 4),
                "Spatial_Generalization_Gap_R2": round(float(spatial_gap_r2), 4),
                "Random_CV_RMSE": round(float(np.mean(r_rmse)), 3),
                "Spatial_CV_RMSE": round(float(np.mean(s_rmse)), 3),
                "Random_CV_MAE": round(float(np.mean(r_mae)), 3),
                "Spatial_CV_MAE": round(float(np.mean(s_mae)), 3)
            })
            print(f"[{target_name:14s}] {model_name:16s} | Random R2: {np.mean(r_r2):.3f} -> Spatial R2: {np.mean(s_r2):.3f} (Gap: {spatial_gap_r2:+.3f})")
            
    df_sp = pd.DataFrame(records)
    out_csv = os.path.join(results_dir, "spatial_validation_results.csv")
    df_sp.to_csv(out_csv, index=False)
    print(f"\nSaved Spatial Validation Results to: {out_csv}")
    
    # Comparison Plot
    plt.figure(figsize=(14, 7), dpi=300)
    df_plot = pd.melt(
        df_sp,
        id_vars=["target", "model"],
        value_vars=["Random_CV_R2_mean", "Spatial_CV_R2_mean"],
        var_name="Validation_Strategy",
        value_name="R2_Score"
    )
    df_plot["Validation_Strategy"] = df_plot["Validation_Strategy"].map({
        "Random_CV_R2_mean": "Standard Random 5-Fold CV (Optimistic)",
        "Spatial_CV_R2_mean": "Spatial Block 5-Fold CV (Leak-Free)"
    })
    
    sns.barplot(data=df_plot, x="target", y="R2_Score", hue="Validation_Strategy", palette="deep")
    plt.title("Spatial Cross-Validation Gap: Random CV vs Spatial Block CV ($R^2$ Score)")
    plt.xlabel("Target Heavy Metal")
    plt.ylabel("$R^2$ Score")
    plt.ylim(0, 1.0)
    plt.legend(title="Validation Protocol")
    plt.tight_layout()
    cv_fig_path = os.path.join(figures_dir, "07_random_vs_spatial_cv.png")
    plt.savefig(cv_fig_path)
    plt.close()
    print(f"Saved: {cv_fig_path}")
    return df_sp

if __name__ == "__main__":
    run_spatial_validation_experiment(
        master_parquet_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.parquet",
        results_dir="soil-pollution-ml/results/metrics",
        figures_dir="soil-pollution-ml/results/figures"
    )
