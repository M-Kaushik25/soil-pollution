# V. Limitations & Future Research Directions

While this study establishes an empirical, leak-free spatial machine learning framework for Indian soil heavy-metal assessment, several scientific and practical limitations must be acknowledged:

1. **Temporal & Seasonal Variations:** Soil heavy metal measurements represent static snapshots. Monsoonal flooding, groundwater fluctuation, and seasonal irrigation alter soil redox potential and heavy metal bioavailability over time. Future studies should ingest multi-temporal geochemical time series.
2. **Speciation vs Total Concentration:** Our models predict total elemental concentrations ($\text{mg/kg}$). However, human bioavailability and phytotoxicity depend on chemical speciation (e.g., highly toxic hexavalent $\text{Cr(VI)}$ vs trivalent $\text{Cr(III)}$). Integrating sequential extraction protocols will enhance toxicological precision.
3. **Subsurface Depth Profiling:** The primary focus was on the biologically active topsoil horizon ($0\text{–}15\text{ cm}$). Modeling vertical leaching through the vadose zone into groundwater aquifers warrants dedicated 3D spatial modeling.
4. **Resolution of Covariates:** While Sentinel-2 provides $10\text{–}20\text{ m}$ multi-spectral bands, global soil datasets (SoilGrids) and climate grids (CHELSA) operate at $250\text{ m}$ to $1\text{ km}$ resolutions. Downscaling algorithms will improve hyper-local field predictions.
