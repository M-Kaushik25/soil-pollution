# Related Work

## A. Spatial Machine Learning in Soil Geochemistry
Traditional digital soil mapping relied on deterministic and geostatistical interpolations such as Inverse Distance Weighting (IDW) and Ordinary Kriging [1], [2]. While mathematically tractable, spatial interpolations assume stationary semivariogram models and fail to ingest multi-source remote sensing or pedo-climatic drivers. Recent advancements demonstrated the superiority of non-linear tree ensembles (Random Forests, Gradient Boosted Trees) in predicting soil properties and trace metal burdens [3], [4]. However, widespread reliance on random cross-validation has masked severe overfitting caused by spatial proximity autocorrelation [5].

## B. Explainability and Attribution in Environmental AI
The adoption of ML in environmental governance demands transparent causal reasoning. Lundberg et al. introduced TreeSHAP, rooted in game-theoretic Shapley values, enabling exact, polynomial-time local and global attribution for tree-based architectures [8]. While SHAP has been utilized in climate modeling and air quality assessment, its deployment in tropical soil heavy-metal assessment in India remains scarce, particularly in decoupling geogenic mineral weathering from industrial effluents.

## C. Conformal Prediction for Distribution-Free Spatial Uncertainty
Quantifying predictive uncertainty is crucial for environmental decision-making. Standard approaches such as Quantile Regression Forests or Bayesian Neural Networks often suffer from heuristic miscalibration or untenable Gaussian priors. Split-conformal prediction provides rigorous, distribution-free, finite-sample marginal coverage guarantees [7], making it uniquely suited for high-stakes soil pollution risk assessment.

## D. Adaptive Sampling and Active Learning in Field Surveys
Traditional spatial sampling designs rely on regular grids or random stratified layouts [9]. When soil collection and spectrometry (ICP-MS/AAS) are costly, sequential active learning strategies select high-utility candidate coordinates. Prior active learning methods often prioritize either pure uncertainty (exploration) or high predicted concentrations (exploitation). Our work bridges this divide by introducing a multi-criteria hybrid formulation integrating composite ecological risk, conformal uncertainty, and spatial dispersion.
