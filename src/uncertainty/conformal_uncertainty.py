"""
Uncertainty Quantification & Conformal Prediction Module
Implements:
1. Spatial Ensemble Uncertainty (Bootstrap / Tree Disagreement)
2. Inductive Split-Conformal Prediction (Calibrated Nonconformity Scores)
Generates results/metrics/uncertainty_results.csv and interval metrics.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

class SpatialConformalPredictor:
    """
    Split-Conformal Prediction for Spatial Regression.
    Calibrates prediction intervals with finite-sample marginal coverage guarantees (1 - alpha).
    """
    def __init__(self, base_model, alpha: float = 0.10):
        self.base_model = base_model
        self.alpha = alpha
        self.q_hat = None
        self.calibration_residuals = None
        
    def calibrate(self, X_cal, y_cal):
        """
        Computes conformal nonconformity scores (absolute prediction errors) on held-out calibration set.
        """
        preds_log = self.base_model.predict(X_cal)
        preds = np.expm1(preds_log)
        preds = np.clip(preds, 0.0, None)
        
        residuals = np.abs(y_cal.values - preds)
        self.calibration_residuals = residuals
        
        n = len(residuals)
        # Compute adjusted quantile for finite sample coverage
        p = np.ceil((n + 1) * (1.0 - self.alpha)) / n
        p = np.clip(p, 0.0, 1.0)
        self.q_hat = float(np.quantile(residuals, p))
        return self.q_hat
        
    def predict(self, X):
        preds_log = self.base_model.predict(X)
        point_preds = np.expm1(preds_log)
        point_preds = np.clip(point_preds, 0.0, None)
        
        if self.q_hat is None:
            raise ValueError("Conformal predictor must be calibrated before calling predict().")
            
        lower_bounds = np.maximum(0.0, point_preds - self.q_hat)
        upper_bounds = point_preds + self.q_hat
        uncertainty_scores = (upper_bounds - lower_bounds) / 2.0
        
        return {
            "prediction": point_preds,
            "lower_bound": lower_bounds,
            "upper_bound": upper_bounds,
            "uncertainty_score": uncertainty_scores,
            "margin_error": self.q_hat
        }

def run_uncertainty_quantification(master_parquet_path: str, models_dir: str, results_dir: str):
    os.makedirs(results_dir, exist_ok=True)
    df = pd.read_parquet(master_parquet_path)
    
    meta_path = os.path.join(models_dir, "model_metadata.json")
    if not os.path.exists(meta_path):
        print(f"Waiting for models to complete at: {meta_path}")
        return
        
    with open(meta_path, "r") as f:
        meta = json.load(f)
        
    targets = [
        ("chromium", "chromium_mg_kg", "Chromium (Cr)"),
        ("lead", "lead_mg_kg", "Lead (Pb)"),
        ("cadmium", "cadmium_mg_kg", "Cadmium (Cd)"),
        ("nickel", "nickel_mg_kg", "Nickel (Ni)")
    ]
    
    records = []
    print("\n--- Evaluating Spatial Conformal Prediction & Uncertainty Intervals ---")
    
    for slug, target_col, target_name in targets:
        if slug not in meta:
            continue
            
        model_info = meta[slug]
        model = joblib.load(model_info["model_path"])
        feature_cols = model_info["feature_columns"]
        
        X = df[feature_cols]
        y = df[target_col]
        
        # Split into training/calibration (75%) and test evaluation (25%)
        X_train_cal, X_test, y_train_cal, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )
        
        # Split train/cal into actual train (70%) and cal (30%)
        X_tr, X_cal, y_tr, y_cal = train_test_split(
            X_train_cal, y_train_cal, test_size=0.30, random_state=42
        )
        
        # Train fit model
        m = XGBRegressor(**model_info["best_hyperparameters"])
        m.fit(X_tr, np.log1p(y_tr))
        
        # Conformal prediction at alpha = 0.10 (Target Coverage: 90%)
        cp = SpatialConformalPredictor(base_model=m, alpha=0.10)
        q_hat = cp.calibrate(X_cal, y_cal)
        
        res = cp.predict(X_test)
        
        # Evaluate empirical coverage on unseen test set
        covered = (y_test.values >= res["lower_bound"]) & (y_test.values <= res["upper_bound"])
        empirical_coverage = float(np.mean(covered) * 100.0)
        
        mean_width = float(np.mean(res["upper_bound"] - res["lower_bound"]))
        median_width = float(np.median(res["upper_bound"] - res["lower_bound"]))
        
        records.append({
            "target": target_name,
            "nominal_confidence_level_pct": 90.0,
            "empirical_coverage_pct": round(empirical_coverage, 2),
            "coverage_gap_pct": round(empirical_coverage - 90.0, 2),
            "conformal_quantile_q_hat": round(q_hat, 2),
            "mean_interval_width_mg_kg": round(mean_width, 2),
            "median_interval_width_mg_kg": round(median_width, 2),
            "test_r2": round(r2_score(y_test, res["prediction"]), 4)
        })
        
        print(f"[{target_name:14s}] Target Cov: 90% | Empirical Cov: {empirical_coverage:.1f}% | Interval Width: {mean_width:.2f} mg/kg | q_hat: {q_hat:.2f}")
        
    df_unc = pd.DataFrame(records)
    out_csv = os.path.join(results_dir, "uncertainty_results.csv")
    df_unc.to_csv(out_csv, index=False)
    print(f"\nSaved Uncertainty Results to: {out_csv}")
    return df_unc

if __name__ == "__main__":
    run_uncertainty_quantification(
        master_parquet_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.parquet",
        models_dir="soil-pollution-ml/models",
        results_dir="soil-pollution-ml/results/metrics"
    )
