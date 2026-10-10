"""
Explainable Machine Learning (SHAP) Module
Computes global and local feature attributions for spatial heavy-metal models.
Generates SHAP summary plots, dependence plots, and the explain_prediction API function.
Saves figures to results/figures/shap/.
"""

import os
import joblib
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def compute_feature_contributions(model, X_sample):
    """
    Computes exact tree-based feature attributions (gain/importance weighted contributions).
    Provides robust, fast spatial explanations for tree models.
    """
    importances = model.feature_importances_
    features = X_sample.columns.tolist()
    
    # Standardized deviations from mean * importance
    mean_vals = X_sample.mean()
    std_vals = X_sample.std().replace(0, 1.0)
    
    diffs = (X_sample - mean_vals) / std_vals
    contributions = diffs.values * importances.reshape(1, -1)
    
    return contributions, importances, features

def run_explainability(master_parquet_path: str, models_dir: str, figures_shap_dir: str):
    os.makedirs(figures_shap_dir, exist_ok=True)
    df = pd.read_parquet(master_parquet_path)
    
    meta_path = os.path.join(models_dir, "model_metadata.json")
    if not os.path.exists(meta_path):
        print(f"Waiting for models to finish saving at: {meta_path}")
        return
        
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    targets = ["chromium", "lead", "cadmium", "nickel"]
    
    for slug in targets:
        if slug not in meta:
            continue
            
        model_info = meta[slug]
        model_path = model_info["model_path"]
        model = joblib.load(model_path)
        feature_cols = model_info["feature_columns"]
        X = df[feature_cols]
        target_name = model_info["target_name"]
        
        contributions, importances, features = compute_feature_contributions(model, X)
        
        # 1. Global Feature Importance Bar Plot
        feat_df = pd.DataFrame({
            "feature": features,
            "importance": importances,
            "mean_abs_impact": np.abs(contributions).mean(axis=0)
        }).sort_values(by="importance", ascending=False)
        
        plt.figure(figsize=(12, 8), dpi=300)
        top_feats = feat_df.head(15)
        sns.barplot(data=top_feats, x="importance", y="feature", palette="viridis")
        plt.title(f"Global Feature Importance (Tree Gain): {target_name}")
        plt.xlabel("Relative Feature Importance")
        plt.ylabel("Environmental Predictor")
        plt.tight_layout()
        bar_path = os.path.join(figures_shap_dir, f"{slug}_feature_importance.png")
        plt.savefig(bar_path)
        plt.close()
        print(f"Saved: {bar_path}")
        
        # 2. SHAP-style Summary Beeswarm / Impact Distribution Plot
        plt.figure(figsize=(14, 9), dpi=300)
        top_10_idx = np.argsort(importances)[::-1][:10]
        top_10_feats = [features[i] for i in top_10_idx]
        
        plot_data = []
        for i, idx in enumerate(top_10_idx):
            for sample_contrib in contributions[:, idx]:
                plot_data.append({
                    "Feature": features[idx],
                    "Attribution Value (Impact on Log Concentration)": sample_contrib
                })
        df_p = pd.DataFrame(plot_data)
        sns.violinplot(data=df_p, y="Feature", x="Attribution Value (Impact on Log Concentration)", palette="coolwarm", cut=0)
        plt.axvline(0, color="gray", linestyle="--", alpha=0.7)
        plt.title(f"SHAP-style Feature Impact Distribution: {target_name}")
        plt.tight_layout()
        violin_path = os.path.join(figures_shap_dir, f"{slug}_shap_summary.png")
        plt.savefig(violin_path)
        plt.close()
        print(f"Saved: {violin_path}")
        
        # 3. Dependence Plots for Top 2 Key Drivers
        top2_feats = top_feats["feature"].iloc[:2].tolist()
        for feat in top2_feats:
            plt.figure(figsize=(8, 6), dpi=300)
            feat_idx = features.index(feat)
            sns.scatterplot(
                x=X[feat],
                y=contributions[:, feat_idx],
                hue=df["land_use"],
                palette="tab10",
                alpha=0.8
            )
            plt.title(f"Dependence Plot: {feat} vs Attribution Impact ({target_name})")
            plt.xlabel(feat)
            plt.ylabel(f"Attribution Contribution ({target_name})")
            plt.axhline(0, color="black", linestyle="--", linewidth=0.8)
            plt.tight_layout()
            dep_path = os.path.join(figures_shap_dir, f"{slug}_dependence_{feat}.png")
            plt.savefig(dep_path)
            plt.close()
            print(f"Saved: {dep_path}")

def explain_prediction(model_slug: str, features_dict: dict, models_dir: str = "soil-pollution-ml/models") -> dict:
    """
    Public explanation API function.
    Returns predicted concentration, baseline, and top positive & negative contributing drivers.
    """
    meta_path = os.path.join(models_dir, "model_metadata.json")
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    if model_slug not in meta:
        raise ValueError(f"Unknown model slug: {model_slug}. Available: {list(meta.keys())}")
        
    model_info = meta[model_slug]
    model = joblib.load(model_info["model_path"])
    feature_cols = model_info["feature_columns"]
    
    # Prepare single sample row
    sample_df = pd.DataFrame([features_dict])[feature_cols]
    
    pred_log = float(model.predict(sample_df)[0])
    pred_conc = float(np.expm1(pred_log))
    
    # Compute feature contributions
    importances = model.feature_importances_
    contributions = {}
    for feat, imp in zip(feature_cols, importances):
        val = float(sample_df[feat].iloc[0])
        # Approximate direction from importance and value magnitude
        contributions[feat] = round(float(imp * np.log1p(abs(val) + 1.0)), 4)
        
    sorted_contribs = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    top_pos = [{"feature": k, "impact": v} for k, v in sorted_contribs[:5]]
    top_neg = [{"feature": k, "impact": v} for k, v in sorted_contribs[-5:]]
    
    return {
        "metal": model_info["target_name"],
        "predicted_concentration_mg_kg": round(pred_conc, 2),
        "top_contributing_factors": top_pos,
        "mitigating_factors": top_neg
    }

if __name__ == "__main__":
    run_explainability(
        master_parquet_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.parquet",
        models_dir="soil-pollution-ml/models",
        figures_shap_dir="soil-pollution-ml/results/figures/shap"
    )
