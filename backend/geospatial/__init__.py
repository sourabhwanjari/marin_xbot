"""
SONAR-AI Geospatial Package
Modules for coordinate validation, trajectory derivation, spatial uncertainty estimation,
and rigorous side scan sonar acoustic georeferencing.
"""

from .coordinates import validate_coordinates, parse_crs_identifier
from .trajectory import generate_survey_trajectory
from .uncertainty import calculate_spatial_uncertainty
from .georeferencing import SonarGeoreferencer

__all__ = [
    "validate_coordinates",
    "parse_crs_identifier",
    "generate_survey_trajectory",
    "calculate_spatial_uncertainty",
    "SonarGeoreferencer"
]
