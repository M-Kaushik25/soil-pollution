# GeoSoil Insight — Data Quality & Integrity Audit Report

**Generated:** 2026-11-01 09:10:01 UTC  
**Geographic Scope:** Tamil Nadu, India (8.0°N – 14.0°N, 76.0°E – 81.0°E)  
**Target Industrial Zones:** Ranipet SIPCOT, Cuddalore SIPCOT, Manali, Coimbatore SIDCO Kurichi, Tiruppur, Mettur, Erode, Thoothukudi SIPCOT  

## 1. Executive Quality Summary

| Metric | Value | Verification Status |
| :--- | :--- | :--- |
| Total Candidate Records Processed | 467 | Audited |
| Accepted Topsoil Samples (0–15 cm) | 464 | **PASSED** |
| Quarantined Non-Soil Matrix Records | 3 | **QUARANTINED** |
| Heavy Metal Results Normalized | 3194 | **PASSED** |
| Standardized Measurement Unit | `mg/kg dry weight` | **100% Invariant** |
| Silent Zero-Imputation Violations | **0** | **STRICT COMPLIANCE** |
| Terrestrial Coordinate Violations | **0** | **STRICT COMPLIANCE** |

## 2. Sample Matrix Segregation & Quarantine Log

In compliance with environmental geochemical guidelines, water, river sediment, industrial effluent, and foliar tissue samples are strictly quarantined from the topsoil dataset.

| Sample ID | Original ID | Matrix | Area | Quarantine Reason | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TN_RAW_QRN_001` | `RNP-DISCHARGE-W01` | **effluent** | Ranipet SIPCOT | Quarantined non-soil sample matrix: 'effluent'. Excluded from topsoil heavy-metal baseline calculations. | `QUARANTINED` |
| `TN_RAW_QRN_002` | `NOYYAL-SED-01` | **sediment** | Tiruppur | Quarantined non-soil sample matrix: 'sediment'. Excluded from topsoil heavy-metal baseline calculations. | `QUARANTINED` |
| `TN_RAW_QRN_003` | `CDL-VEG-LEAF-01` | **vegetation** | Cuddalore SIPCOT | Quarantined non-soil sample matrix: 'vegetation'. Excluded from topsoil heavy-metal baseline calculations. | `QUARANTINED` |

## 3. Metal Availability & Missing Value Audit

Missing metal values are **never** filled with zeros or unvalidated averages. Only authentic observations are recorded:

| Metal | Element | Total Valid Tests | Missing Tests | Min (mg/kg) | Median (mg/kg) | Mean (mg/kg) | Max (mg/kg) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Chromium | Ch | 464 | 0 | 9.98 | 87.87 | 116.92 | 896.82 |
| Lead | Le | 464 | 0 | 4.78 | 30.30 | 38.67 | 185.00 |
| Cadmium | Ca | 464 | 0 | 0.07 | 0.58 | 0.73 | 4.43 |
| Nickel | Ni | 464 | 0 | 10.86 | 36.31 | 47.32 | 255.27 |
| Zinc | Zi | 451 | 13 | 14.07 | 70.60 | 87.08 | 492.45 |
| Copper | Co | 452 | 12 | 9.12 | 41.67 | 47.78 | 340.00 |
| Arsenic | Ar | 435 | 29 | 1.03 | 4.36 | 5.07 | 18.50 |

## 4. Soil Health Properties Audit

| Property | Unit | Valid Observations | Min | Median | Mean | Max |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Soil pH | pH units | 464 | 4.80 | 7.21 | 7.17 | 9.20 |
| Electrical Conductivity | dS/m | 464 | 0.105 | 0.631 | 0.716 | 4.500 |
| Soil Organic Carbon | % | 464 | 0.150 | 0.573 | 0.687 | 2.800 |
| Clay Fraction | % | 464 | 5.0 | 27.9 | 27.5 | 54.9 |
| Sand Fraction | % | 464 | 19.8 | 52.2 | 51.9 | 79.2 |
| Silt Fraction | % | 464 | 3.9 | 20.2 | 20.6 | 58.9 |
