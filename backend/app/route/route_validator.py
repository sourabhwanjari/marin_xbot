import logging
from typing import Dict, Any, List, Optional, Tuple
from app.route.route_models import RouteRequest, RouteConditions

logger = logging.getLogger("marinex.route.validator")

class RouteValidator:
    """
    Validates route inputs, spatial feasibility, and marine telemetry freshness.
    Enforces the safety-first principle: Never claims absolute safety and flags missing/stale telemetry.
    """

    @staticmethod
    def validate_request(request: RouteRequest) -> Tuple[bool, Optional[str]]:
        """Validates coordinates and parameters of RouteRequest."""
        o_lat, o_lon = request.origin.latitude, request.origin.longitude
        d_lat, d_lon = request.destination.latitude, request.destination.longitude

        if not (-90.0 <= o_lat <= 90.0) or not (-180.0 <= o_lon <= 180.0):
            return False, f"Origin coordinates ({o_lat}, {o_lon}) out of geographic bounds"

        if not (-90.0 <= d_lat <= 90.0) or not (-180.0 <= d_lon <= 180.0):
            return False, f"Destination coordinates ({d_lat}, {d_lon}) out of geographic bounds"

        # Check minimal separation
        if abs(o_lat - d_lat) < 0.0001 and abs(o_lon - d_lon) < 0.0001:
            return False, "Origin and destination must be distinct points"

        return True, None

    @staticmethod
    def evaluate_data_adequacy(conditions: RouteConditions) -> Tuple[bool, List[str]]:
        """
        Verifies whether adequate meteorological and oceanographic data is available
        to formulate a responsible route safety assessment.
        Returns (is_adequate, missing_parameters).
        """
        missing = []
        if conditions.avg_wind_speed_knots is None:
            missing.append("wind telemetry")
        if conditions.max_wave_height_m is None:
            missing.append("wave height telemetry")

        is_adequate = len(missing) < 2
        return is_adequate, missing

    @staticmethod
    def format_safety_disclaimer(
        risk_level: str,
        missing_data: List[str],
        is_stale: bool = False
    ) -> str:
        """
        Generates truthful safety wording conforming to maritime advisory standards.
        """
        if missing_data:
            missing_str = ", ".join(missing_data)
            return (
                f"Route safety assessment is limited because {missing_str} is currently unavailable. "
                "Mariners must exercise heightened visual watch and monitor VHF weather channels."
            )

        if is_stale:
            return (
                "Marine telemetry may be outdated (>24h). Safety assessment is provisional. "
                "Consult the latest port state bulletin before departure."
            )

        if risk_level == "LOW":
            return (
                "Lower-risk navigational corridor based on currently available weather, wave, and geospatial boundaries. "
                "Maintain standard watch and navigation lights."
            )
        elif risk_level == "MODERATE":
            return (
                "Moderate navigational risk detected. Recommended path avoids critical obstacles, "
                "but small craft (<9m) should maintain close proximity to sheltered coastal waters."
            )
        else:
            return (
                "High marine risk or active warnings detected along this sector. "
                "Non-essential voyages should be deferred."
            )

route_validator = RouteValidator()
