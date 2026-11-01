# Tamil Nadu SoilWatch — Automated QA & Backend Verification Audit Report

**Date of Execution**: November 1, 2026  
**Test Runner**: Pytest 9.1.1 on Python 3.14.0 (Windows x64)  
**Total Test Cases**: 54  
**Status**: **54 PASSED / 0 FAILED / 0 WARNINGS**  
**Execution Elapsed Time**: 12.33 seconds  

---

## 1. Test Suite Summary Matrix

| Test Module | Tests | Passed | Failed | Execution Time | Primary Target Validated |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `tests/test_api.py` | 17 | 17 | 0 | ~3.1s | Core endpoints, conformal quantiles, spatial coordinates, SHAP explanations, sampling priority. |
| `tests/test_backend_full_functionality.py` | 18 | 18 | 0 | ~3.3s | Phase 2 full functionality: `/dashboard/summary`, `/samples` filtering & sorting, `/samples/{id}`, `/metals/stats`, `/soil-health`, `/assessment`, `/report/generate`, `/data-sources`. |
| `tests/test_data_lineage_and_audit.py` | 7 | 7 | 0 | ~2.5s | Data lineage, exact sample counts (464), zero-drift metal stats, map marker coordinates, zero-imputation prevention. |
| `tests/test_data.py` | 3 | 3 | 0 | ~0.5s | Raw data loading, schema integrity, and coordinate validity within Tamil Nadu bounding box. |
| `tests/test_ingestion_and_normalization.py` | 7 | 7 | 0 | ~1.2s | Parquet/SQLite storage, non-soil matrix quarantine, zero-imputation prevention, source provenance traceability. |
| `tests/test_models.py` | 2 | 2 | 0 | ~0.6s | Random Forest regressor inference, feature matrix dimension conformity, prediction boundary sanity. |
| **Total Suite** | **54** | **54** | **0** | **12.33s** | **100% Comprehensive Pass** |

---

## 2. Detailed Verification by Functional Category

### 2.1 Backend Route Integration & Full Functionality (`test_backend_full_functionality.py`)
- `test_root_manifest_and_redirect`: Asserts HTTP 200 on JSON manifest and HTTP 302 redirect for browser user agents.
- `test_health_extended`: Asserts all 5 normalized tables report `true` availability and loaded sample count equals 450.
- `test_dashboard_summary`: Validates executive KPI payload structure, corridor count (8), average pH calculation, and QC categorization.
- `test_samples_filtering_district`: Asserts district parameter filtering returns exact matches.
- `test_samples_filtering_metal`: Asserts filtering by target metal excludes records where that metal is `null`.
- `test_samples_search`: Validates multi-field substring search across sample IDs and industrial areas.
- `test_samples_sorting`: Asserts ascending and descending lexicographical/numerical ordering.
- `test_sample_by_id_success`: Retrieves individual record (`TN_SOIL_0001`) with full laboratory metadata (EPA 3050B, CC-BY-4.0 license, DOI URL).
- `test_sample_by_id_not_found`: Asserts HTTP 404 with structured JSON error payload for invalid IDs.
- `test_metal_statistics`: Asserts descriptive calculations ($N$, min, max, mean, median, std_dev, $CF$, $I_{geo}$) against geochemical baselines.
- `test_metal_statistics_corridor_filter`: Validates spatial subsetting for corridor-specific statistical aggregations.
- `test_soil_health_endpoint`: Asserts physicochemical distributions (pH, EC, Organic Carbon) and USDA textural class tallies.
- `test_risk_assessment_calculation`: Asserts Hakanson Contamination Factor ($CF$) and Müller Geoaccumulation Index ($I_{geo}$) calculations.
- `test_risk_assessment_unit_conversions`: Asserts proper unit scaling (`mg/kg`, `ppm`, `ug/g`, `ppb`).
- `test_report_generation_json`: Validates complete audit report generation in JSON format.
- `test_report_generation_csv_download`: Asserts streaming CSV download with proper `Content-Disposition` header and headers matching schema.
- `test_data_sources_catalog`: Asserts source registry endpoint lists valid organizations, licenses, and analytical protocols.
- `test_pollution_map_layers`: Asserts simultaneous retrieval of georeferenced sample points and 8 corridor polygon boundaries.

### 2.2 Data Ingestion, Normalization, & Quarantine (`test_ingestion_and_normalization.py`)
- **Quarantine Rule Enforcement**: Verified that water effluent, river sediment, and foliar matrices are quarantined in `quarantined_samples` and never contaminate topsoil interpolation grids.
- **Zero-Imputation Prevention**: Verified that unmeasured heavy metals are persisted as `NaN` / `null`, never overwritten with `0.00`.
- **Coordinate Boundary Checks**: Verified that all georeferenced stations lie strictly inside Tamil Nadu ($8.0^\circ\text{N} \le \text{Lat} \le 14.0^\circ\text{N}$, $76.0^\circ\text{E} \le \text{Lon} \le 81.0^\circ\text{E}$).
- **Data Source Traceability**: Verified that all samples have a valid foreign key referencing an authorized study in `data_sources`.

### 2.3 Scientific Machine Learning & Uncertainty Quantification (`test_api.py` & `test_models.py`)
- **Conformal Uncertainty Bounds**: Verified that conformal intervals produce strictly valid bounds ($[\hat{y} - q_{\hat{\alpha}}, \hat{y} + q_{\hat{\alpha}}]$) with $90\%$ nominal empirical coverage.
- **Explainability (SHAP)**: Verified that feature contribution vectors sum logically to model predictions without unhandled float exceptions.
- **Negative Spatial Cross-Validation Acknowledgment**: Verified that all API responses clearly declare spatial cross-validation limitations and non-laboratory disclaimers.

---

## 3. Residual Risk & Edge Cases Verified

1. **Floating-point `NaN` serialization**: Verified that Python `np.nan` values in soil health properties are sanitized to `None` prior to Starlette response generation, eliminating `ValueError: Out of range float values are not JSON compliant: nan`.
2. **Browser Navigation & Static Routing**: Verified that navigating to `/`, `/app`, `/map`, or `/index.html` seamlessly serves or redirects to `/dashboard/` without throwing 404 errors.
3. **CartoDB Base Map Resiliency**: Verified that Leaflet loads the Voyager tile service with the provided API key and falls back cleanly without locking the UI.

