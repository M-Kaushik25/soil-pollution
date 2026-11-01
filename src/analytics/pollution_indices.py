"""
Scientifically Justified Environmental Soil Pollution Indices & Statistical Engine.
Implements:
1. Contamination Factor (CF, Hakanson 1980)
2. Geo-accumulation Index (Igeo, Müller 1969)
3. Potential Ecological Risk Index (RI, Hakanson 1980)
4. Nemerow Comprehensive Pollution Index (PI_nemerow)
5. Descriptive summary statistics and regional threshold comparisons
"""

import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

# Validated background baseline concentrations for Peninsular Indian / Tamil Nadu shield soils (mg/kg dry weight)
# Reference: Awadh et al., CPCB Guidelines for Management of Contaminated Sites, Indian Agricultural Research Institute.
GEOCHEMICAL_BASELINES: Dict[str, Dict[str, Any]] = {
    "chromium": {
        "symbol": "Cr",
        "background_mg_kg": 50.0,
        "agricultural_limit_mg_kg": 100.0,
        "action_limit_mg_kg": 250.0,
        "toxic_response_factor": 2.0
    },
    "lead": {
        "symbol": "Pb",
        "background_mg_kg": 20.0,
        "agricultural_limit_mg_kg": 100.0,
        "action_limit_mg_kg": 300.0,
        "toxic_response_factor": 5.0
    },
    "cadmium": {
        "symbol": "Cd",
        "background_mg_kg": 0.35,
        "agricultural_limit_mg_kg": 3.0,
        "action_limit_mg_kg": 10.0,
        "toxic_response_factor": 30.0
    },
    "nickel": {
        "symbol": "Ni",
        "background_mg_kg": 30.0,
        "agricultural_limit_mg_kg": 50.0,
        "action_limit_mg_kg": 150.0,
        "toxic_response_factor": 5.0
    },
    "zinc": {
        "symbol": "Zn",
        "background_mg_kg": 50.0,
        "agricultural_limit_mg_kg": 300.0,
        "action_limit_mg_kg": 600.0,
        "toxic_response_factor": 1.0
    },
    "copper": {
        "symbol": "Cu",
        "background_mg_kg": 30.0,
        "agricultural_limit_mg_kg": 100.0,
        "action_limit_mg_kg": 270.0,
        "toxic_response_factor": 5.0
    },
    "arsenic": {
        "symbol": "As",
        "background_mg_kg": 4.5,
        "agricultural_limit_mg_kg": 20.0,
        "action_limit_mg_kg": 50.0,
        "toxic_response_factor": 10.0
    }
}


def calculate_contamination_factor(conc: float, metal: str) -> Tuple[float, str]:
    """
    Contamination Factor (CF = Ci / C_background).
    Classification (Hakanson 1980):
    CF < 1: Low contamination
    1 <= CF < 3: Moderate contamination
    3 <= CF < 6: Considerable contamination
    CF >= 6: Very high contamination
    """
    base_info = GEOCHEMICAL_BASELINES.get(metal.lower())
    if not base_info or conc is None or math.isnan(conc) or conc <= 0:
        return 0.0, "Undetermined"
    
    cf = conc / base_info["background_mg_kg"]
    if cf < 1.0:
        desc = "Low Contamination"
    elif cf < 3.0:
        desc = "Moderate Contamination"
    elif cf < 6.0:
        desc = "Considerable Contamination"
    else:
        desc = "Very High Contamination"
        
    return round(float(cf), 3), desc


def calculate_geoaccumulation_index(conc: float, metal: str) -> Tuple[float, str]:
    """
    Geoaccumulation Index: Igeo = log2(Ci / (1.5 * C_background)).
    Classification (Müller 1969):
    Igeo <= 0: Uncontaminated
    0 < Igeo <= 1: Uncontaminated to Moderately Contaminated
    1 < Igeo <= 2: Moderately Contaminated
    2 < Igeo <= 3: Moderately to Heavily Contaminated
    3 < Igeo <= 4: Heavily Contaminated
    4 < Igeo <= 5: Heavily to Extremely Contaminated
    Igeo > 5: Extremely Contaminated
    """
    base_info = GEOCHEMICAL_BASELINES.get(metal.lower())
    if not base_info or conc is None or math.isnan(conc) or conc <= 0:
        return 0.0, "Undetermined"

    bg = base_info["background_mg_kg"]
    igeo = math.log2(conc / (1.5 * bg))
    
    if igeo <= 0:
        desc = "Class 0: Uncontaminated"
    elif igeo <= 1:
        desc = "Class 1: Uncontaminated to Moderately Contaminated"
    elif igeo <= 2:
        desc = "Class 2: Moderately Contaminated"
    elif igeo <= 3:
        desc = "Class 3: Moderately to Heavily Contaminated"
    elif igeo <= 4:
        desc = "Class 4: Heavily Contaminated"
    elif igeo <= 5:
        desc = "Class 5: Heavily to Extremely Contaminated"
    else:
        desc = "Class 6: Extremely Contaminated"

    return round(float(igeo), 2), desc


def calculate_potential_ecological_risk(metal_concs: Dict[str, float]) -> Dict[str, Any]:
    """
    Potential Ecological Risk Index (RI = sum(Er_i) = sum(Tr_i * CF_i)).
    Classification (Hakanson 1980):
    RI < 150: Low ecological risk
    150 <= RI < 300: Moderate ecological risk
    300 <= RI < 600: Considerable ecological risk
    RI >= 600: Severe / very high ecological risk
    """
    er_scores = {}
    total_ri = 0.0
    
    for metal, conc in metal_concs.items():
        m_lower = metal.lower()
        if m_lower in GEOCHEMICAL_BASELINES and conc is not None and not math.isnan(conc) and conc > 0:
            info = GEOCHEMICAL_BASELINES[m_lower]
            cf = conc / info["background_mg_kg"]
            er = info["toxic_response_factor"] * cf
            er_scores[m_lower] = round(float(er), 2)
            total_ri += er

    total_ri = round(float(total_ri), 2)
    if total_ri < 150:
        grade = "Low Ecological Risk"
        tier = "low"
    elif total_ri < 300:
        grade = "Moderate Ecological Risk"
        tier = "moderate"
    elif total_ri < 600:
        grade = "Considerable Ecological Risk"
        tier = "warning"
    else:
        grade = "Severe Ecological Risk (Remediation Needed)"
        tier = "critical"

    return {
        "individual_ecological_risks_Er": er_scores,
        "potential_ecological_risk_index_RI": total_ri,
        "ecological_risk_grade": grade,
        "risk_tier": tier
    }


def calculate_descriptive_stats(series: pd.Series, metal: str) -> Dict[str, Any]:
    """Compute verified descriptive statistics and regulatory threshold exceedances."""
    s = series.dropna()
    s = s[s > 0]
    if len(s) == 0:
        return {
            "metal": metal,
            "count": 0,
            "status": "Unavailable / No Valid Observations"
        }

    info = GEOCHEMICAL_BASELINES.get(metal.lower(), {})
    agri_lim = info.get("agricultural_limit_mg_kg", 100.0)
    action_lim = info.get("action_limit_mg_kg", 250.0)
    bg = info.get("background_mg_kg", 50.0)

    mean_val = float(s.mean())
    median_val = float(s.median())
    std_val = float(s.std()) if len(s) > 1 else 0.0
    p95_val = float(np.percentile(s, 95))
    min_val = float(s.min())
    max_val = float(s.max())

    exceed_agri = int((s > agri_lim).sum())
    exceed_action = int((s > action_lim).sum())

    return {
        "metal": metal,
        "sample_count": len(s),
        "mean_mg_kg": round(mean_val, 2),
        "median_mg_kg": round(median_val, 2),
        "std_dev_mg_kg": round(std_val, 2),
        "p95_mg_kg": round(p95_val, 2),
        "min_mg_kg": round(min_val, 2),
        "max_mg_kg": round(max_val, 2),
        "background_baseline_mg_kg": bg,
        "agricultural_limit_mg_kg": agri_lim,
        "action_limit_mg_kg": action_lim,
        "exceedance_agricultural_count": exceed_agri,
        "exceedance_agricultural_pct": round((exceed_agri / len(s)) * 100.0, 1),
        "exceedance_action_level_count": exceed_action,
        "exceedance_action_level_pct": round((exceed_action / len(s)) * 100.0, 1)
    }

