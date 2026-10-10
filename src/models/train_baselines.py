"""
Baseline Machine Learning Evaluation Module
Trains Mean Baseline, Ridge Regression, Random Forest, XGBoost, LightGBM, and SVR
across all target heavy metals using 5-Fold Cross Validation.
Generates results/metrics/baseline_results.csv.
"""

import os
import time
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import KFold

def evaluate_model_cv(model_cls, model_kwargs, X, y, cv_splitter, scale=True):
    r2_scores, mae_scores, rmse_scores = [], [], []
    train_times, inf_times = [], []
    
    for train_idx, val_idx in cv_splitter:
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Log-transform target for modeling stability
        y_train_log = np.log1p(y_train)
        y_val_log = np.log1p(y_val)
        
        if scale:
            pipe = Pipeline([
                ('scaler', StandardScaler()),
                ('model', model_cls(**model_kwargs))
            ])
        else:
            pipe = Pipeline([
                ('model', model_cls(**model_kwargs))
            ])
            
        t0 = time.time()
        pipe.fit(X_train, y_train_log)
        t_fit = time.time() - t0
        
        t0 = time.time()
        preds_log = pipe.predict(X_val)
        t_inf = time.time() - t0
        
        # Inverse transform predictions back to original concentration (mg/kg)
        preds = np.expm1(preds_log)
        preds = np.clip(preds, 0.0, None)
        
        r2 = r2_score(y_val, preds)
        mae = mean_absolute_error(y_val, preds)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        
        r2_scores.append(r2)
        mae_scores.append(mae)
        rmse_scores.append(rmse)
        train_times.append(t_fit)
        inf_times.append(t_inf)
        
    return {
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores)),
        "rmse_mean": float(np.mean(rmse_scores)),
        "rmse_std": float(np.std(rmse_scores)),
        "train_time_sec": float(np.sum(train_times)),
        "inference_time_sec": float(np.sum(inf_times))
    }

def run_baselines(master_parquet_path: str, results_dir: str):
    os.makedirs(results_dir, exist_ok=True)
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
        ("Mean Baseline", DummyRegressor, {"strategy": "mean"}, False),
        ("Ridge Regression", Ridge, {"alpha": 10.0, "random_state": 42}, True),
        ("Random Forest", RandomForestRegressor, {"n_estimators": 100, "random_state": 42, "n_jobs": -1}, False),
        ("XGBoost", XGBRegressor, {"n_estimators": 100, "learning_rate": 0.08, "max_depth": 4, "random_state": 42, "n_jobs": -1}, False),
        ("LightGBM", LGBMRegressor, {"n_estimators": 100, "learning_rate": 0.08, "max_depth": 4, "random_state": 42, "verbose": -1, "n_jobs": -1}, False),
        ("SVR (RBF)", SVR, {"C": 5.0, "epsilon": 0.1}, True)
    ]
    
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    splits = list(cv.split(X))
    
    all_results = []
    print(f"Training Baseline ML Models across {len(targets)} targets & {len(models)} algorithms...")
    
    for target_col, target_name in targets:
        y = df[target_col]
        for model_name, model_cls, kwargs, scale_flag in models:
            res = evaluate_model_cv(model_cls, kwargs, X, y, splits, scale=scale_flag)
            all_results.append({
                "target": target_name,
                "target_column": target_col,
                "model": model_name,
                "R2_mean": round(res["r2_mean"], 4),
                "R2_std": round(res["r2_std"], 4),
                "MAE_mean": round(res["mae_mean"], 3),
                "MAE_std": round(res["mae_std"], 3),
                "RMSE_mean": round(res["rmse_mean"], 3),
                "RMSE_std": round(res["rmse_std"], 3),
                "training_time_sec": round(res["train_time_sec"], 4),
                "inference_time_sec": round(res["inference_time_sec"], 4)
            })
            print(f"[{target_name}] {model_name:18s} -> R2: {res['r2_mean']:.3f} +/- {res['r2_std']:.3f}, RMSE: {res['rmse_mean']:.2f}")
            
    df_res = pd.DataFrame(all_results)
    out_csv = os.path.join(results_dir, "baseline_results.csv")
    df_res.to_csv(out_csv, index=False)
    print(f"\nSaved Baseline ML Results to: {out_csv}")
    return df_res

if __name__ == "__main__":
    run_baselines(
        master_parquet_path="soil-pollution-ml/data/processed/master_soil_pollution_dataset.parquet",
        results_dir="soil-pollution-ml/results/metrics"
    )
