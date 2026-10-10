# Indian Soil Pollution Thresholds & Ecological Risk Assessment Standards

## 1. Regulatory Context and Background Values

Soil heavy metal risk characterization requires establishing baseline geogenic concentrations and differentiating non-polluted agricultural soils from contaminated sites requiring statutory intervention. In India, guidelines are defined by the **Central Pollution Control Board (CPCB)**, **Ministry of Environment, Forest and Climate Change (MoEFCC)**, and Indian Council of Agricultural Research (ICAR), supplemented by **CCME** (Canadian Council of Ministers of the Environment) and **WHO/FAO** standards.

---

## 2. Quantitative Threshold Matrix (Topsoil $0\text{–}15\text{ cm}$)

| Heavy Metal | Symbol | Indian Peninsular Background Baseline ($B_n$, $\text{mg/kg}$) | Indian Permissible Agricultural Limit ($\text{mg/kg}$) | CPCB / MoEFCC Action Level (Industrial/Residential, $\text{mg/kg}$) | Toxicity Coefficient ($T_r^i$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Chromium** | $\text{Cr}$ | $50.0$ | $100.0$ | $250.0$ | $2.0$ |
| **Lead** | $\text{Pb}$ | $20.0$ | $100.0$ | $300.0$ | $5.0$ |
| **Cadmium** | $\text{Cd}$ | $0.35$ | $3.0$ | $10.0$ | $30.0$ |
| **Nickel** | $\text{Ni}$ | $30.0$ | $50.0$ | $150.0$ | $5.0$ |
| **Zinc** | $\text{Zn}$ | $55.0$ | $300.0$ | $600.0$ | $1.0$ |
| **Copper** | $\text{Cu}$ | $30.0$ | $100.0$ | $200.0$ | $5.0$ |
| **Arsenic** | $\text{As}$ | $5.0$ | $20.0$ | $50.0$ | $10.0$ |

---

## 3. Standard Geochemical Risk Indices Formulation

### A. Geo-accumulation Index ($I_{\text{geo}}$)
Introduced by Müller (1969) to assess metal accumulation relative to baseline lithogenic levels:
$$I_{\text{geo}} = \log_2\left(\frac{C_n}{1.5 \times B_n}\right)$$
where $C_n$ is the measured or predicted concentration ($\text{mg/kg}$), $B_n$ is the regional geogenic baseline background value, and the factor $1.5$ accounts for natural lithogenic matrix variations.

#### Classification Tiers:
- $I_{\text{geo}} \le 0$: Uncontaminated (Class 0)
- $0 < I_{\text{geo}} \le 1$: Uncontaminated to Moderately Contaminated (Class 1)
- $1 < I_{\text{geo}} \le 2$: Moderately Contaminated (Class 2)
- $2 < I_{\text{geo}} \le 3$: Moderately to Heavily Contaminated (Class 3)
- $3 < I_{\text{geo}} \le 4$: Heavily Contaminated (Class 4)
- $4 < I_{\text{geo}} \le 5$: Heavily to Extremely Contaminated (Class 5)
- $I_{\text{geo}} > 5$: Extremely Contaminated (Class 6)

---

### B. Single Contamination Factor ($C_f^i$)
$$C_f^i = \frac{C_i}{C_{0}^i}$$
where $C_i$ is the concentration of metal $i$ and $C_0^i$ is the permissible agricultural baseline.

---

### C. Potential Ecological Risk Index ($RI$)
Formulated by Hakanson (1980) to incorporate both multi-element toxicity and chemical abundance:
$$E_r^i = T_r^i \times C_f^i$$
$$RI = \sum_{i=1}^k E_r^i$$
where:
- $E_r^i$ is the single-metal potential ecological risk factor.
- $T_r^i$ is the toxic response factor ($\text{Cd}=30 > \text{As}=10 > \text{Pb}=\text{Cu}=\text{Ni}=5 > \text{Cr}=2 > \text{Zn}=1$).

#### Classification Tiers for $RI$:
- $RI < 150$: Low Ecological Risk
- $150 \le RI < 300$: Moderate Ecological Risk
- $300 \le RI < 600$: Considerable Ecological Risk
- $RI \ge 600$: Very High / Severe Ecological Risk

---

### D. Nemerow Integrated Pollution Index ($PI_{\text{Nemerow}}$)
Synthesizes the average contamination level with the extreme single-metal contaminant burden:
$$PI_{\text{Nemerow}} = \sqrt{\frac{\left(\frac{1}{k}\sum_{i=1}^k P_i\right)^2 + \max(P_i)^2}{2}}$$
where $P_i = \frac{C_i}{S_i}$ ($S_i$ is the regulatory agricultural action limit).
- $PI \le 0.7$: Clean / Background
- $0.7 < PI \le 1.0$: Warning Limit
- $1.0 < PI \le 2.0$: Slight Pollution
- $2.0 < PI \le 3.0$: Moderate Pollution
- $PI > 3.0$: Heavy Pollution

---

## 4. Implementation in Pipeline
These indices are calculated deterministically across the spatial prediction grid and adaptive sampling simulation loop to prioritize sampling in regions exhibiting high composite ecological risk ($RI \ge 300$) and high model prediction uncertainty.
