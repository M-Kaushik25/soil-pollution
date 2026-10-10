"""
Exploratory Data Analysis (EDA) & Publication Figures Generator
Produces target distribution histograms, boxplots, correlation heatmaps,
and spatial concentration maps saved to results/figures/.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium

def generate_eda_figures(clean_parquet_path: str, figures_dir: str):
    os.makedirs(figures_dir, exist_ok=True)
    df = pd.read_parquet(clean_parquet_path)
    
    # Set publication aesthetic styling
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 15,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'figure.titlesize': 16,
        'figure.dpi': 300
    })
    
    targets = ["lead_mg_kg", "cadmium_mg_kg", "chromium_mg_kg", "nickel_mg_kg"]
    target_labels = ["Lead (Pb)", "Cadmium (Cd)", "Chromium (Cr)", "Nickel (Ni)"]
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    
    # 1. Target Distributions (Raw vs Log-Transformed)
    fig, axes = plt.subplots(2, 4, figsize=(20, 9))
    for i, (col, label, color) in enumerate(zip(targets, target_labels, palette)):
        # Raw distribution
        sns.histplot(df[col], kde=True, ax=axes[0, i], color=color, bins=25)
        axes[0, i].set_title(f"Raw {label}")
        axes[0, i].set_xlabel("Concentration (mg/kg)")
        axes[0, i].set_ylabel("Frequency")
        
        # Log-transformed distribution
        log_vals = np.log1p(df[col])
        sns.histplot(log_vals, kde=True, ax=axes[1, i], color=color, bins=25)
        axes[1, i].set_title(f"Log(1+y) {label}")
        axes[1, i].set_xlabel("log(1 + mg/kg)")
        axes[1, i].set_ylabel("Frequency")
        
    plt.tight_layout()
    dist_path = os.path.join(figures_dir, "01_target_distributions.png")
    plt.savefig(dist_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {dist_path}")
    
    # 2. Boxplots by Land Use Category
    fig, axes = plt.subplots(1, 4, figsize=(22, 6))
    for i, (col, label, color) in enumerate(zip(targets, target_labels, palette)):
        sns.boxplot(x="land_use", y=col, data=df, ax=axes[i], palette="Set2")
        axes[i].set_title(f"{label} by Land Use")
        axes[i].set_xlabel("Land Use Class")
        axes[i].set_ylabel("mg/kg")
        axes[i].tick_params(axis='x', rotation=30)
    plt.tight_layout()
    box_path = os.path.join(figures_dir, "02_target_boxplots_by_landuse.png")
    plt.savefig(box_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {box_path}")
    
    # 3. Correlation Matrix Heatmap
    numeric_cols = [
        "soil_ph", "soil_ec_dSm", "soc_pct", "clay_pct", "silt_pct", "sand_pct",
        "lead_mg_kg", "cadmium_mg_kg", "chromium_mg_kg", "nickel_mg_kg", "zinc_mg_kg", "copper_mg_kg"
    ]
    corr = df[numeric_cols].corr()
    
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(corr, mask=mask, cmap=cmap, vmax=1.0, vmin=-1.0, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .8}, annot=True, fmt=".2f")
    plt.title("Geochemical & Soil Property Correlation Matrix (Tamil Nadu)")
    plt.tight_layout()
    corr_path = os.path.join(figures_dir, "03_correlation_matrix.png")
    plt.savefig(corr_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {corr_path}")
    
    # 4. Spatial Concentration Scatter Maps
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    axes = axes.flatten()
    for i, (col, label) in enumerate(zip(targets, target_labels)):
        sc = axes[i].scatter(
            df["longitude"], df["latitude"],
            c=df[col], cmap="viridis", s=45, edgecolor="black", linewidth=0.5, alpha=0.85
        )
        axes[i].set_title(f"Spatial Distribution: {label} (mg/kg)")
        axes[i].set_xlabel("Longitude (°E)")
        axes[i].set_ylabel("Latitude (°N)")
        plt.colorbar(sc, ax=axes[i], label="mg/kg")
        
    plt.tight_layout()
    spatial_path = os.path.join(figures_dir, "04_target_spatial_maps.png")
    plt.savefig(spatial_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {spatial_path}")
    
    # 5. Interactive Folium Map for Spatial Visualization
    m = folium.Map(location=[11.5, 78.5], zoom_start=7, tiles="CartoDB positron")
    for _, row in df.iterrows():
        popup_text = f"ID: {row['sample_id']}<br>Cluster: {row['region_cluster']}<br>Cr: {row['chromium_mg_kg']:.1f} mg/kg<br>Pb: {row['lead_mg_kg']:.1f} mg/kg<br>Cd: {row['cadmium_mg_kg']:.2f} mg/kg<br>Ni: {row['nickel_mg_kg']:.1f} mg/kg"
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=4,
            color="#2b5c8f",
            fill=True,
            fill_color="#e74c3c" if row["chromium_mg_kg"] > 100 else "#2ecc71",
            fill_opacity=0.75,
            popup=popup_text
        ).add_to(m)
        
    map_html = os.path.join(figures_dir, "sample_locations_interactive.html")
    m.save(map_html)
    print(f"Saved: {map_html}")

if __name__ == "__main__":
    generate_eda_figures(
        clean_parquet_path="soil-pollution-ml/data/processed/clean_soil_data.parquet",
        figures_dir="soil-pollution-ml/results/figures"
    )
