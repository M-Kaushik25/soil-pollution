# II. Methodology

## A. Study Area & In-Situ Geochemical Dataset
The study domain encompasses the state of Tamil Nadu, Southern India ($10.0^\circ\text{N} - 13.5^\circ\text{N}, 76.8^\circ\text{E} - 80.2^\circ\text{E}$), covering critical agricultural plains and industrial zones (Coimbatore-Tiruppur textile hub, Ranipet-Vellore tannery basin, Salem metallurgical belt, Cauvery delta, and Chennai-Ennore peri-urban industrial corridor). The in-situ dataset consists of $N = 448$ quality-assured topsoil observations ($0\text{–}15\text{ cm}$) analyzed via Inductively Coupled Plasma Mass Spectrometry (ICP-MS) and Atomic Absorption Spectroscopy (AAS) following EPA 3050B acid digestion.

## B. Environmental Covariate Extraction Pipeline
A multidimensional feature tensor ($d = 35$) was compiled for every sampling coordinate without spatial data leakage:
1. **Pedological & Subsoil Properties:** In-situ $\text{pH}$, Electrical Conductivity ($\text{EC}$), Soil Organic Carbon ($\text{SOC}$), Sand, Silt, and Clay fractions, coupled with depth-matched ISRIC SoilGrids 250m covariates.
2. **Topographic & Hydrological Covariates:** Elevation, Slope, Sin/Cos Aspect, Topographic Wetness Index ($\text{TWI}$), and Multiresolution Valley Bottom Flatness ($\text{MrVBF}$) derived from NASA SRTM 30m DEM.
3. **High-Resolution Bioclimate:** Annual Mean Temperature ($\text{BIO1}$), Temperature Seasonality ($\text{BIO4}$), Annual Precipitation ($\text{BIO12}$), and Precipitation Seasonality ($\text{BIO15}$) from CHELSA/WorldClim 2.1.
4. **Multi-Spectral Satellite Imagery:** Normalized Difference Vegetation Index ($\text{NDVI}$), Enhanced Vegetation Index ($\text{EVI}$), Bare Soil Index ($\text{BSI}$), Clay Mineral Index ($\text{CMI}$), and Iron Oxide Index ($\text{IOI}$) computed from ESA Copernicus Sentinel-2 MSI.
5. **Anthropogenic Proximity Indices:** Euclidean distances to industrial zones, major road transport arteries, drainage rivers, and ambient population densities from OpenStreetMap and GHSL.

## C. Spatial Block Cross-Validation
To eliminate spatial autocorrelation bias, spatial coordinate partitioning is enforced via $K$-Means spatial clustering into 5 discrete geographic blocks:
$$\mathcal{S} = \bigcup_{k=1}^K \mathcal{B}_k, \quad \mathcal{B}_i \cap \mathcal{B}_j = \emptyset \quad (\forall i \neq j)$$
In each fold $k$, the model is trained strictly on $\mathcal{S} \setminus \mathcal{B}_k$ and evaluated on $\mathcal{B}_k$.

## D. Split-Conformal Prediction Formulation
Let $(X_i, Y_i)_{i=1}^n$ be the calibration set. For target confidence level $1 - \alpha$ ($\alpha = 0.10$ for $90\%$ nominal coverage), the nonconformity score is the absolute residual $R_i = |Y_i - \hat{\mu}(X_i)|$. The empirical conformal quantile $\hat{q}$ is:
$$\hat{q} = \text{Quantile}\left(\{R_i\}_{i=1}^n, \frac{\lceil(n+1)(1-\alpha)\rceil}{n}\right)$$
For any test query $X_{n+1}$, the valid prediction interval is:
$$C(X_{n+1}) = \left[\max(0, \hat{\mu}(X_{n+1}) - \hat{q}), \quad \hat{\mu}(X_{n+1}) + \hat{q}\right]$$
guaranteeing marginal coverage $\mathbb{P}(Y_{n+1} \in C(X_{n+1})) \ge 1 - \alpha$.

## E. Proposed Hybrid Adaptive Sampling Algorithm
At active learning iteration $t$, given labeled set $\mathcal{L}_t$ and candidate pool $\mathcal{U}_t$, the multi-criteria acquisition score $S_{\text{hybrid}}(x)$ is computed for each candidate $x \in \mathcal{U}_t$:
$$S_{\text{hybrid}}(x) = w_r \cdot \widetilde{\text{Risk}}(x) + w_u \cdot \widetilde{\text{Unc}}(x) + w_d \cdot \widetilde{\text{Dist}}(x, \mathcal{L}_t)$$
where $\widetilde{\text{Risk}}(x) = \text{Norm}(RI(x))$ is the normalized composite potential ecological risk index, $\widetilde{\text{Unc}}(x) = \text{Norm}(\hat{\sigma}(x))$ is the model epistemic prediction uncertainty, and $\widetilde{\text{Dist}}(x, \mathcal{L}_t) = \text{Norm}(\min_{z \in \mathcal{L}_t} \|x - z\|_2)$ is the spatial dispersion factor enforcing geographic exploration ($w_r = 0.40, w_u = 0.40, w_d = 0.20$). Top $k=15$ candidate locations are queried and ingested into $\mathcal{L}_{t+1}$.
