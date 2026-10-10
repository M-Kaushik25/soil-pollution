# Data Cleaning & Quality Assurance Report

## 1. Summary of Actions

- Initial raw record count: 451
- Exact duplicate rows removed: 3
- Duplicate spatial coordinate rows removed: 2
- Invalid coordinate samples removed: 0
- Imputed columns: soil_ec_dSm (6 values imputed using cluster median), arsenic_mg_kg (14 values imputed using cluster median)
- Soil texture fractions re-normalized to 100% dry weight.
- Final clean dataset record count: 446
- Spatial CRS: WGS 84 (EPSG:4326)

## 2. Processed Dataset Schema & Statistics

| Column Name | Type | Non-Null Count | Min | Mean | Max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sample_id` | object | 446 | - | 446 unique | - |
| `region_cluster` | object | 446 | - | 5 unique | - |
| `latitude` | float64 | 446 | 10.21 | 11.76 | 13.50 |
| `longitude` | float64 | 446 | 76.51 | 78.67 | 80.30 |
| `soil_depth_cm` | object | 446 | - | 1 unique | - |
| `sampling_year` | int64 | 446 | 2021.00 | 2022.46 | 2024.00 |
| `land_use` | object | 446 | - | 4 unique | - |
| `soil_ph` | float64 | 446 | 4.80 | 7.15 | 9.20 |
| `soil_ec_dSm` | float64 | 446 | 0.10 | 0.70 | 4.50 |
| `soc_pct` | float64 | 446 | 0.15 | 0.69 | 2.80 |
| `clay_pct` | float64 | 446 | 5.00 | 27.36 | 54.93 |
| `silt_pct` | float64 | 446 | 3.94 | 20.54 | 58.93 |
| `sand_pct` | float64 | 446 | 19.84 | 52.10 | 79.20 |
| `lead_mg_kg` | float64 | 446 | 4.78 | 36.67 | 171.57 |
| `cadmium_mg_kg` | float64 | 446 | 0.07 | 0.70 | 4.43 |
| `chromium_mg_kg` | float64 | 446 | 9.98 | 115.16 | 896.82 |
| `nickel_mg_kg` | float64 | 446 | 10.86 | 46.76 | 255.27 |
| `zinc_mg_kg` | float64 | 446 | 14.07 | 86.42 | 492.45 |
| `copper_mg_kg` | float64 | 446 | 9.12 | 46.57 | 159.73 |
| `arsenic_mg_kg` | float64 | 446 | 1.05 | 5.02 | 16.53 |
| `analytical_method` | object | 446 | - | 1 unique | - |
| `qc_status` | object | 446 | - | 1 unique | - |
