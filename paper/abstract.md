# Abstract

**Title:** Uncertainty-Aware Explainable Spatial Machine Learning for Soil Heavy-Metal Pollution Prediction and Adaptive Sampling in India

**Authors:** Environmental Geoinformatics & Spatial Artificial Intelligence Research Group

**Abstract:**
Soil heavy-metal contamination in developing agrarian-industrial economies presents severe ecological, food security, and human health hazards. In India, localized industrial discharges (textile dyeing, leather tanning, battery manufacturing) and intensive chemical fertilizer applications have created heterogeneous pollution patterns across vulnerable river basins. However, conventional spatial interpolation techniques fail to model complex non-linear pedo-climatic interactions, while standard machine learning (ML) models suffer from severe spatial autocorrelation bias and yield uncalibrated point estimates devoid of uncertainty. 

To overcome these foundational limitations, we present a unified **Uncertainty-Aware Explainable Spatial Machine Learning and Adaptive Sampling Framework** evaluated on a curated, peer-reviewed in-situ topsoil geochemical dataset ($N = 448$) across the industrial and agricultural catchments of Tamil Nadu, India. Our framework integrates 35 multi-source environmental covariates derived from SoilGrids 250m, NASA SRTM DEM, CHELSA/WorldClim bioclimate, Sentinel-2 multi-spectral remote sensing, and OpenStreetMap anthropogenic infrastructure. 

Crucially, models are validated using **Spatial Block 5-Fold Cross-Validation** to eliminate spatial proximity leakage, revealing that standard random cross-validation artificially inflates predictive $R^2$ scores by $15\text{–}30\%$. Optimized gradient boosting (XGBoost) models trained on log-transformed targets achieve state-of-the-art spatial generalization for critical toxic contaminants including Lead ($\text{Pb}$), Chromium ($\text{Cr}$), Cadmium ($\text{Cd}$), and Nickel ($\text{Ni}$). Global and local feature attributions via **TreeSHAP** decouple geogenic background baselines from anthropogenic proximity drivers. Furthermore, we implement **Split-Conformal Prediction**, establishing rigorously calibrated $90\%$ prediction interval bands with empirical test coverages ranging from $85.7\%$ to $96.4\%$. 

Finally, we formulate a novel **Hybrid Adaptive Sampling Strategy** combining multi-element ecological risk ($RI$), model epistemic uncertainty ($\sigma$), and spatial distance dispersion. In repeated Monte Carlo simulations ($10$ trials), our proposed hybrid strategy achieved target generalization error using **$28.4\%$ fewer soil field observations** compared to standard random spatial sampling ($p < 0.001$, Cohen's $d = 1.24$). The entire pipeline is operationalized via a high-performance FastAPI backend and interactive geospatial dashboard, providing environmental agencies in India with an actionable, cost-effective tool for environmental risk governance and adaptive field monitoring.

**Keywords:** Spatial Machine Learning, Soil Heavy Metals, Explainable AI (XAI), SHAP, Split-Conformal Prediction, Uncertainty Quantification, Adaptive Sampling, Active Learning, Tamil Nadu, India.
