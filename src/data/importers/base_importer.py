"""
Base Importer & Data Validation Engine for GeoSoil Insight.
Enforces strict pedological standards, geospatial bounds checking,
matrix filtering (quarantining water/sediment/vegetation), and
zero-imputation prevention.
"""

import math
from typing import Dict, Any, List, Optional, Tuple

TAMIL_NADU_BOUNDS = {
    "min_latitude": 8.0,
    "max_latitude": 14.0,
    "min_longitude": 76.0,
    "max_longitude": 81.0
}

VALID_SOIL_MATRICES = {"soil", "topsoil", "surface_soil", "agricultural_soil", "industrial_soil"}
QUARANTINE_MATRICES = {"water", "groundwater", "surface_water", "effluent", "sediment", "river_sediment", "vegetation", "crop", "leaf"}

STANDARD_METALS = ["chromium", "lead", "cadmium", "nickel", "zinc", "copper", "arsenic"]

class ValidationResult:
    def __init__(self, is_valid: bool, qc_status: str, messages: List[str]):
        self.is_valid = is_valid
        self.qc_status = qc_status
        self.messages = messages

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "qc_status": self.qc_status,
            "messages": self.messages
        }


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, List[str]]:
    """Validate that coordinates fall strictly within Tamil Nadu terrestrial bounds."""
    errors = []
    if lat is None or lon is None or math.isnan(lat) or math.isnan(lon):
        return False, ["Coordinate values cannot be null or NaN."]
    
    if not (TAMIL_NADU_BOUNDS["min_latitude"] <= lat <= TAMIL_NADU_BOUNDS["max_latitude"]):
        errors.append(f"Latitude {lat:.4f} is outside Tamil Nadu bounds ({TAMIL_NADU_BOUNDS['min_latitude']}°N - {TAMIL_NADU_BOUNDS['max_latitude']}°N).")
    if not (TAMIL_NADU_BOUNDS["min_longitude"] <= lon <= TAMIL_NADU_BOUNDS["max_longitude"]):
        errors.append(f"Longitude {lon:.4f} is outside Tamil Nadu bounds ({TAMIL_NADU_BOUNDS['min_longitude']}°E - {TAMIL_NADU_BOUNDS['max_longitude']}°E).")
        
    return len(errors) == 0, errors


def validate_matrix(matrix_str: str) -> Tuple[bool, str, str]:
    """
    Validate sample matrix.
    Rejects or quarantines water, sediment, and vegetation from soil analysis.
    Returns: (is_soil, normalized_matrix, quarantine_reason_if_any)
    """
    norm = (matrix_str or "").strip().lower().replace(" ", "_")
    if norm in VALID_SOIL_MATRICES or "soil" in norm:
        return True, "soil", ""
    elif norm in QUARANTINE_MATRICES or any(q in norm for q in ["water", "sediment", "vegetation", "effluent", "plant"]):
        return False, norm, f"Quarantined non-soil sample matrix: '{matrix_str}'. Excluded from topsoil heavy-metal baseline calculations."
    else:
        return False, norm, f"Unrecognized sample matrix: '{matrix_str}'. Must be explicit soil matrix."


def validate_metal_concentration(val: Optional[float], metal_name: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Validates a heavy metal concentration.
    Rules:
    - Never silently impute missing values to zero.
    - Missing/NaN values return None (unmeasured).
    - True measurements must be strictly positive (> 0.0 mg/kg).
    """
    if val is None:
        return None, None
    try:
        val_float = float(val)
    except (ValueError, TypeError):
        return None, f"Invalid numeric concentration for {metal_name}: '{val}'"

    if math.isnan(val_float):
        return None, None  # Unmeasured
    if val_float <= 0.0:
        return None, f"Non-positive concentration ({val_float}) for {metal_name}. Natural soil heavy-metal baseline cannot be <= 0."
    return round(val_float, 4), None


def determine_texture_class(clay: float, silt: float, sand: float) -> str:
    """Classify soil texture according to standard USDA soil texture triangle."""
    if clay >= 40:
        if sand <= 45:
            return "Clay"
        else:
            return "Sandy Clay"
    elif clay >= 27:
        if sand >= 45:
            return "Sandy Clay Loam"
        elif sand <= 20:
            return "Silty Clay Loam"
        else:
            return "Clay Loam"
    elif clay >= 20:
        if sand >= 52:
            return "Sandy Clay Loam"
        elif silt >= 50:
            return "Silt Loam"
        else:
            return "Loam"
    elif clay >= 7:
        if silt >= 50:
            return "Silt Loam"
        elif sand >= 52:
            return "Sandy Loam"
        else:
            return "Loam"
    else:
        if silt >= 80:
            return "Silt"
        elif sand >= 85:
            return "Sand"
        elif sand >= 70:
            return "Loamy Sand"
        else:
            return "Sandy Loam"

