"""
Benchmark Dataset Importer for GeoSoil Insight.
Normalizes the existing Tamil Nadu geochemical benchmark dataset (451 records),
assigning district/industrial cluster linkages, pedological texture classes,
and documenting its unverified provenance until independent field validation.
"""

import os
import sys
import json
import pandas as pd
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data.importers.base_importer import (
    validate_coordinates,
    validate_matrix,
    validate_metal_concentration,
    determine_texture_class
)

SOURCE_METADATA = {
    "source_id": "SRC_TN_BENCHMARK_2024",
    "source_name": "Tamil Nadu Regional Soil Geochemical Benchmark Dataset (TNAU-TNSOIL-HM-2024)",
    "source_url": "https://github.com/M-Kaushik25/soil-pollution",
    "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
    "sample_matrix": "soil",
    "analytical_protocol": "Strong Acid Digestion (EPA Method 3050B) with ICP-MS / AAS",
    "provenance_type": "Synthetic / Calibrated Benchmark (Unverified in-situ field provenance)",
    "doi_or_citation": "GeoSoil Insight Baseline Technical Report, 2024",
    "description": "Statewide 450-sample topsoil (0-15cm) geochemical benchmark dataset parameter-calibrated for peninsular Indian lithology and Tamil Nadu industrial corridors."
}

# Mapping of region clusters to primary districts and industrial areas
CLUSTER_MAPPINGS = {
    "Coimbatore_Tiruppur": {
        "primary_district": "Coimbatore / Tiruppur",
        "industrial_area": "Coimbatore SIDCO Kurichi / Tiruppur"
    },
    "Ranipet_Vellore": {
        "primary_district": "Ranipet / Vellore",
        "industrial_area": "Ranipet SIPCOT"
    },
    "Cauvery_Delta": {
        "primary_district": "Thanjavur / Tiruvarur",
        "industrial_area": "Cauvery Delta Agrarian Basin"
    },
    "Salem_Dharmapuri": {
        "primary_district": "Salem",
        "industrial_area": "Mettur Industrial Complex"
    },
    "Chennai_Ennore": {
        "primary_district": "Chennai / Tiruvallur",
        "industrial_area": "Manali Industrial Area"
    }
}

def import_benchmark_dataset(raw_csv_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Ingests and normalizes the benchmark dataset.
    Returns dictionary with normalized collections:
    'data_sources', 'soil_samples', 'heavy_metal_results', 'soil_health_results', 'quarantine_records'
    """
    if not os.path.exists(raw_csv_path):
        raise FileNotFoundError(f"Raw benchmark dataset not found at: {raw_csv_path}")

    df_raw = pd.read_csv(raw_csv_path)

    sources = [SOURCE_METADATA]
    soil_samples = []
    heavy_metal_results = []
    soil_health_results = []
    quarantine_records = []

    seen_coords = set()
    result_counter = 1

    for idx, row in df_raw.iterrows():
        sample_id = str(row["sample_id"]).strip()
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        cluster = str(row.get("region_cluster", "Unknown")).strip()

        # 1. Geographic bounds validation
        is_coord_valid, coord_msgs = validate_coordinates(lat, lon)

        # 2. Duplicate coordinate check
        coord_key = (round(lat, 5), round(lon, 5))
        is_duplicate = coord_key in seen_coords
        seen_coords.add(coord_key)

        # 3. Matrix validation (All records in benchmark are topsoil)
        matrix = "soil"
        is_soil, norm_matrix, quarantine_msg = validate_matrix(matrix)

        mapping = CLUSTER_MAPPINGS.get(cluster, {
            "primary_district": "Tamil Nadu Regional",
            "industrial_area": "Regional Cluster"
        })

        qc_status = "PASSED"
        quarantine_reason = None

        if not is_coord_valid:
            qc_status = "QUARANTINED"
            quarantine_reason = "; ".join(coord_msgs)
        elif is_duplicate:
            qc_status = "FLAGGED_DUPLICATE_COORDINATES"

        sample_record = {
            "sample_id": sample_id,
            "original_sample_id": sample_id,
            "source_id": SOURCE_METADATA["source_id"],
            "latitude": lat,
            "longitude": lon,
            "district": mapping["primary_district"],
            "industrial_area": mapping["industrial_area"],
            "sampling_year": int(row.get("sampling_year", 2023)),
            "sampling_depth_cm": str(row.get("soil_depth_cm", "0-15")),
            "sample_matrix": "soil",
            "land_use": str(row.get("land_use", "Agricultural")),
            "provenance_status": "Unverified Benchmark (Synthetic Model)",
            "qc_status": qc_status,
            "quarantine_reason": quarantine_reason
        }

        if qc_status == "QUARANTINED":
            quarantine_records.append({
                **sample_record,
                "rejection_reason": quarantine_reason
            })
            continue

        soil_samples.append(sample_record)

        # 4. Heavy metal results
        metals = [
            ("chromium", "chromium_mg_kg"),
            ("lead", "lead_mg_kg"),
            ("cadmium", "cadmium_mg_kg"),
            ("nickel", "nickel_mg_kg"),
            ("zinc", "zinc_mg_kg"),
            ("copper", "copper_mg_kg"),
            ("arsenic", "arsenic_mg_kg")
        ]

        for metal_name, col_name in metals:
            raw_val = row.get(col_name)
            conc, err = validate_metal_concentration(raw_val, metal_name)
            
            # If value is unmeasured/None, do not inject zero!
            if conc is not None:
                heavy_metal_results.append({
                    "result_id": f"HMR_{result_counter:06d}",
                    "sample_id": sample_id,
                    "metal": metal_name,
                    "concentration_mg_kg": conc,
                    "unit": "mg/kg dry weight",
                    "analytical_method": str(row.get("analytical_method", "ICP-MS / AAS (EPA 3050B)")),
                    "qc_status": "PASSED" if not err else "FLAGGED"
                })
                result_counter += 1

        # 5. Soil health results
        clay = float(row.get("clay_pct", 25.0))
        silt = float(row.get("silt_pct", 25.0))
        sand = float(row.get("sand_pct", 50.0))
        
        # Texture check & normalise
        tot = clay + silt + sand
        if tot > 0:
            clay = round(clay * 100.0 / tot, 2)
            silt = round(silt * 100.0 / tot, 2)
            sand = round(100.0 - (clay + silt), 2)
            
        tex_class = determine_texture_class(clay, silt, sand)

        soil_health_results.append({
            "sample_id": sample_id,
            "soil_ph": round(float(row.get("soil_ph", 7.0)), 2),
            "soil_ec_dSm": round(float(row.get("soil_ec_dSm", 0.5)), 3),
            "soc_pct": round(float(row.get("soc_pct", 0.5)), 3),
            "clay_pct": clay,
            "silt_pct": silt,
            "sand_pct": sand,
            "texture_class": tex_class
        })

    return {
        "data_sources": sources,
        "soil_samples": soil_samples,
        "heavy_metal_results": heavy_metal_results,
        "soil_health_results": soil_health_results,
        "quarantine_records": quarantine_records
    }
