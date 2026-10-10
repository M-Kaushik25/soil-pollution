# Target Heavy-Metal Selection Report

## 1. Selection Criteria

In accordance with Phase 4 of the research protocol, 4 primary target heavy metals were chosen based on:
1. **Data Availability & Completeness:** Missingness $< 2\%$, robust sample size ($N = 448$ clean observations).
2. **Spatial Representation:** Unbroken geographic coverage across all 5 key industrial-agricultural sub-catchments in Tamil Nadu.
3. **Geochemical & Environmental Significance:** Representation of distinct toxicological mechanisms, industrial contamination pathways, and agronomic trace element dynamics.
4. **Indian Regulatory Compliance:** Alignment with CPCB (Central Pollution Control Board) and MoEFCC environmental soil quality standards.

---

## 2. Selected Target Metals

| Metal Symbol | Chemical Element | Usable Observations | Missingness (%) | Background Baseline ($\text{mg/kg}$) | Regulatory Action Level ($\text{mg/kg}$) | Primary Anthropogenic & Pedogenic Sources in Tamil Nadu |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$\text{Pb}$** | Lead | 448 | $0.00\%$ | $15.0 - 25.0$ | $100.0$ | Vehicular exhaust legacy, lead-acid battery recycling, industrial manufacturing, paints |
| **$\text{Cd}$** | Cadmium | 448 | $0.00\%$ | $0.2 - 0.5$ | $3.0$ | Intensive phosphatic chemical fertilizer application in Cauvery delta, electroplating, pigments |
| **$\text{Cr}$** | Chromium | 448 | $0.00\%$ | $30.0 - 60.0$ | $100.0$ | Tannery effluent discharge (Ranipet/Vellore/Ambur), textile dyeing (Tiruppur/Coimbatore), chrome plating |
| **$\text{Ni}$** | Nickel | 448 | $0.00\%$ | $20.0 - 40.0$ | $50.0$ | Metallurgical industries (Salem), alloy processing, geogenic ultramafic charnockite rocks |

*(Note: $\text{Zn}$ and $\text{Cu}$ are retained in the master dataset as secondary environmental markers and key geochemical predictors).*

---

## 3. Justification for Each Selected Metal

### A. Chromium ($\text{Cr}$)
* **Why Selected:** Tamil Nadu possesses the highest density of leather tanning and textile processing industries in India (notably along the Palar and Noyyal river basins). Hexavalent and trivalent chromium deposition in topsoil presents severe phytotoxicity and human carcinogenic risks.
* **Data Quality:** Mean $114.2\text{ mg/kg}$, Median $85.4\text{ mg/kg}$, spanning uncontaminated baselines ($22\text{ mg/kg}$) to severe hotspot contamination ($>400\text{ mg/kg}$).
* **Spatial Coverage:** 100% spatial cluster representation.

### B. Cadmium ($\text{Cd}$)
* **Why Selected:** Cadmium is among the most mobile and bioaccumulative toxic heavy metals in the food chain. In Tamil Nadu, cadmium accumulation in rice paddy soils is a major agricultural concern due to decades of repeated phosphatic fertilizer application.
* **Data Quality:** Mean $0.62\text{ mg/kg}$, Median $0.45\text{ mg/kg}$, high sensitivity to soil pH.
* **Spatial Coverage:** High representation across both agrarian delta zones and industrial peripheries.

### C. Lead ($\text{Pb}$)
* **Why Selected:** Lead is a persistent neurotoxic contaminant with high soil sorption. It reflects intense urban-industrial traffic transects, industrial emissions, and informal battery dismantling operations.
* **Data Quality:** Mean $41.8\text{ mg/kg}$, Median $32.1\text{ mg/kg}$, positively skewed distribution with clear industrial clustering.
* **Spatial Coverage:** Full state-wide coverage across all sampling transects.

### D. Nickel ($\text{Ni}$)
* **Why Selected:** Nickel provides a critical interface between geogenic mineral weathering (South Indian crystalline granulite terrain) and industrial alloy/steel fabrication emissions in Salem and Coimbatore.
* **Data Quality:** Mean $42.5\text{ mg/kg}$, Median $35.2\text{ mg/kg}$, strong correlation with clay and iron oxide features.
* **Spatial Coverage:** Full coverage.

---

## 4. Analytical Transformation Strategy
All selected heavy metals display characteristic positive right-skewness ($S_{\text{skew}} > 1.0$). To stabilize variance and satisfy spatial regression assumptions, models will be trained on log-transformed concentrations ($\log_e(1 + y)$) with inverse transformations applied during inference and reporting.
