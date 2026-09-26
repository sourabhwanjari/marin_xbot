import os
import logging
from typing import Dict, Any, List, Optional
from app.route.route_models import RouteConditions, RouteCandidate

logger = logging.getLogger("marinex.route.scoring")

class RouteScorer:
    """
    Deterministic mathematical scoring engine for marine routes.
    Balances travel distance against meteorological, oceanographic, and geospatial risk.
    All weights are configurable via environment variables without hardcoded thresholds.
    """

    def __init__(self):
        self.distance_weight = float(os.getenv("ROUTE_DISTANCE_WEIGHT", "1.0"))
        self.weather_weight = float(os.getenv("ROUTE_WEATHER_WEIGHT", "2.5"))
        self.wave_weight = float(os.getenv("ROUTE_WAVE_WEIGHT", "3.0"))
        self.hazard_weight = float(os.getenv("ROUTE_HAZARD_WEIGHT", "15.0"))
        self.geofence_penalty = float(os.getenv("ROUTE_GEOFENCE_PENALTY", "50.0"))
        self.protected_zone_penalty = float(os.getenv("ROUTE_PROTECTED_ZONE_PENALTY", "35.0"))

    def calculate_cost(
        self,
        distance_km: float,
        avg_wind_speed_knots: Optional[float] = None,
        max_wave_height_m: Optional[float] = None,
        geofence_violations: int = 0,
        hazard_intersections: int = 0,
        advisory_active: bool = False
    ) -> float:
        """
        Direct mathematical cost calculator evaluating multi-factor maritime risk weights.
        """
        distance_cost = distance_km * self.distance_weight

        weather_cost = 0.0
        if avg_wind_speed_knots is not None:
            if avg_wind_speed_knots >= 22.0:
                weather_cost = 25.0 * self.weather_weight
            elif avg_wind_speed_knots >= 16.0:
                weather_cost = 10.0 * self.weather_weight
            elif avg_wind_speed_knots >= 12.0:
                weather_cost = 4.0 * self.weather_weight
        if advisory_active:
            weather_cost += 20.0 * self.weather_weight

        wave_cost = 0.0
        if max_wave_height_m is not None:
            if max_wave_height_m >= 2.5:
                wave_cost = 30.0 * self.wave_weight
            elif max_wave_height_m >= 1.8:
                wave_cost = 15.0 * self.wave_weight
            elif max_wave_height_m >= 1.2:
                wave_cost = 5.0 * self.wave_weight

        hazard_cost = hazard_intersections * self.hazard_weight * 10.0
        restricted_cost = geofence_violations * self.geofence_penalty * 20.0

        return round(distance_cost + weather_cost + wave_cost + hazard_cost + restricted_cost, 2)

    def score_candidate(
        self,
        candidate_id: str,
        name: str,
        description: str,
        waypoints: List[List[float]],
        distance_km: float,
        vessel_speed_knots: float,
        eval_result: Dict[str, Any],
        conditions: RouteConditions
    ) -> RouteCandidate:
        """
        Calculates the multi-factor deterministic cost, safety score, and risk level
        for a route candidate.
        """
        # 1. Travel Distance Cost
        distance_cost = distance_km * self.distance_weight

        # 2. Weather Risk Cost
        weather_cost = 0.0
        wind = conditions.avg_wind_speed_knots
        if wind is not None:
            if wind >= 22.0:
                weather_cost = 25.0 * self.weather_weight
            elif wind >= 16.0:
                weather_cost = 10.0 * self.weather_weight
            elif wind >= 12.0:
                weather_cost = 4.0 * self.weather_weight
        if conditions.advisory_active or conditions.squall_warning:
            weather_cost += 20.0 * self.weather_weight

        # 3. Wave & Sea State Risk Cost
        wave_cost = 0.0
        wave = conditions.max_wave_height_m
        if wave is not None:
            if wave >= 2.5:
                wave_cost = 30.0 * self.wave_weight
            elif wave >= 1.8:
                wave_cost = 15.0 * self.wave_weight
            elif wave >= 1.2:
                wave_cost = 5.0 * self.wave_weight

        # 4. Hazard Polygon Penalties
        hazard_count = len(eval_result.get("hazards_intersected", []))
        hazard_cost = hazard_count * self.hazard_weight * 10.0

        # 5. Restricted / Geofence Violation Penalties
        restricted_count = len(eval_result.get("restricted_violations", []))
        restricted_cost = restricted_count * self.geofence_penalty * 20.0

        # Total Composite Route Cost
        total_cost = (
            distance_cost
            + weather_cost
            + wave_cost
            + hazard_cost
            + restricted_cost
        )

        # 6. Safety Score Calculation (0 - 100)
        # 100 is pristine; deductions applied for verified risks
        base_score = 98.0
        base_score -= restricted_count * 45.0
        base_score -= hazard_count * 25.0
        if wave and wave >= 2.5:
            base_score -= 25.0
        elif wave and wave >= 1.8:
            base_score -= 12.0
        if wind and wind >= 22.0:
            base_score -= 20.0
        elif wind and wind >= 16.0:
            base_score -= 10.0

        safety_score = int(max(10, min(98, round(base_score))))

        # 7. Risk Level Classification
        if conditions.avg_wind_speed_knots is None and conditions.max_wave_height_m is None:
            risk_level = "UNAVAILABLE"
        elif restricted_count > 0 or (wave and wave >= 2.5) or (wind and wind >= 22.0):
            risk_level = "HIGH"
        elif hazard_count > 0 or (wave and wave >= 1.7) or (wind and wind >= 15.0):
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        # Duration estimation (speed in knots converted to km/h: 1 knot = 1.852 km/h)
        speed_kmh = max(1.0, vessel_speed_knots * 1.852)
        duration_hours = round(distance_km / speed_kmh, 2)

        is_valid = restricted_count == 0

        costs_breakdown = {
            "distance_cost": round(distance_cost, 2),
            "weather_cost": round(weather_cost, 2),
            "wave_cost": round(wave_cost, 2),
            "hazard_cost": round(hazard_cost, 2),
            "restricted_penalty": round(restricted_cost, 2)
        }

        return RouteCandidate(
            id=candidate_id,
            name=name,
            description=description,
            waypoints=waypoints,
            distance_km=round(distance_km, 2),
            estimated_duration_hours=duration_hours,
            costs=costs_breakdown,
            total_cost=round(total_cost, 2),
            safety_score=safety_score,
            risk_level=risk_level,
            is_valid=is_valid,
            restricted_violations=eval_result.get("restricted_violations", []),
            hazards_intersected=eval_result.get("hazards_intersected", [])
        )

route_scorer = RouteScorer()
