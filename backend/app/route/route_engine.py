import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.route.route_models import RouteRequest, RouteCandidate, RouteConditions
from app.route.route_constraints import route_constraints
from app.route.route_scoring import route_scorer

logger = logging.getLogger("marinex.route.engine")

class RouteEngine:
    """
    Core Route Generation and Selection Engine.
    Generates candidate tracks (direct, coastal corridor, offshore clearance)
    and selects the optimal path balancing short distance, obstacle avoidance, and sea state safety.
    """

    @staticmethod
    def _interpolate_points(
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        num_segments: int = 5
    ) -> List[List[float]]:
        """Interpolates intermediate waypoints between two points."""
        points = []
        for i in range(num_segments + 1):
            t = i / float(num_segments)
            lat = round(p1[0] + t * (p2[0] - p1[0]), 4)
            lon = round(p1[1] + t * (p2[1] - p1[1]), 4)
            points.append([lat, lon])
        return points

    def generate_candidate_routes(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        restricted_areas: List[Dict[str, Any]],
        hazard_areas: List[Dict[str, Any]],
        conditions: RouteConditions,
        vessel_speed_knots: float = 10.0
    ) -> List[RouteCandidate]:
        """
        Synthesizes multiple candidate tracks and scores each against deterministic constraints.
        """
        candidates: List[RouteCandidate] = []
        o_lat, o_lon = origin
        d_lat, d_lon = destination

        # --- Candidate 1: Direct Line Track (Shortest Geodesic) ---
        direct_pts = self._interpolate_points((o_lat, o_lon), (d_lat, d_lon), num_segments=6)
        direct_eval = route_constraints.evaluate_route_path(direct_pts, restricted_areas, hazard_areas)
        direct_candidate = route_scorer.score_candidate(
            candidate_id="route_direct",
            name="Direct Navigational Track",
            description="Shortest direct geodesic line between origin and destination.",
            waypoints=direct_pts,
            distance_km=direct_eval["total_distance_km"],
            vessel_speed_knots=vessel_speed_knots,
            eval_result=direct_eval,
            conditions=conditions
        )
        candidates.append(direct_candidate)

        # --- Candidate 2: Coastal Safety Corridor (Bypasses nearshore obstacles) ---
        # Generate midpoints with gentle seaward curve to clear nearshore restricted zones
        mid_lat = (o_lat + d_lat) / 2.0
        # If moving roughly north-south along west coast of India, seaward is West (decrease lon or increase depending on side)
        # For West coast India (e.g. Mumbai, Goa, Kochi ~72-73°E), seaward is West (lower lon)
        # For East coast India (Chennai, Vizag ~80-83°E), seaward is East (higher lon)
        seaward_lon_offset = -0.06 if d_lon < 77.0 else 0.06
        mid_wp1 = [round(o_lat + 0.35 * (d_lat - o_lat), 4), round(o_lon + seaward_lon_offset, 4)]
        mid_wp2 = [round(o_lat + 0.70 * (d_lat - o_lat), 4), round(d_lon + seaward_lon_offset, 4)]

        coastal_pts = (
            self._interpolate_points((o_lat, o_lon), (mid_wp1[0], mid_wp1[1]), num_segments=3)[:-1]
            + self._interpolate_points((mid_wp1[0], mid_wp1[1]), (mid_wp2[0], mid_wp2[1]), num_segments=3)[:-1]
            + self._interpolate_points((mid_wp2[0], mid_wp2[1]), (d_lat, d_lon), num_segments=3)
        )
        coastal_eval = route_constraints.evaluate_route_path(coastal_pts, restricted_areas, hazard_areas)
        coastal_candidate = route_scorer.score_candidate(
            candidate_id="route_coastal_corridor",
            name="Coastal Safety Corridor",
            description="Recommended coastal waypoint track avoiding nearshore security channels and sandbars.",
            waypoints=coastal_pts,
            distance_km=coastal_eval["total_distance_km"],
            vessel_speed_knots=vessel_speed_knots,
            eval_result=coastal_eval,
            conditions=conditions
        )
        candidates.append(coastal_candidate)

        # --- Candidate 3: Deepwater Offshore Clearance Track ---
        # Wider seaward clearance (0.12° offset) ensuring total clearance from large hazard surge polygons
        wide_lon_offset = -0.12 if d_lon < 77.0 else 0.12
        offshore_mid = [round(mid_lat, 4), round(min(o_lon, d_lon) + wide_lon_offset, 4)]
        offshore_pts = (
            self._interpolate_points((o_lat, o_lon), (offshore_mid[0], offshore_mid[1]), num_segments=4)[:-1]
            + self._interpolate_points((offshore_mid[0], offshore_mid[1]), (d_lat, d_lon), num_segments=4)
        )
        offshore_eval = route_constraints.evaluate_route_path(offshore_pts, restricted_areas, hazard_areas)
        offshore_candidate = route_scorer.score_candidate(
            candidate_id="route_offshore_clearance",
            name="Deepwater Offshore Clearance Track",
            description="Wide offshore detour providing maximum clearance from coastal shoals and high wave surges.",
            waypoints=offshore_pts,
            distance_km=offshore_eval["total_distance_km"],
            vessel_speed_knots=vessel_speed_knots,
            eval_result=offshore_eval,
            conditions=conditions
        )
        candidates.append(offshore_candidate)

        return candidates

    def select_best_route(
        self,
        candidates: List[RouteCandidate],
        preference: str = "balanced"
    ) -> Tuple[RouteCandidate, List[RouteCandidate]]:
        """
        Selects the best route candidate according to the selected preference:
        - 'safest': Prioritizes zero restricted/hazard crossings and lowest risk.
        - 'shortest': Prioritizes distance among valid routes.
        - 'balanced': Default weighted cost function minimizing risk * distance.
        """
        # Strictly prioritize routes with zero restricted zone violations
        valid_candidates = [c for c in candidates if c.is_valid]
        pool = valid_candidates if valid_candidates else candidates

        if preference == "shortest":
            sorted_candidates = sorted(pool, key=lambda c: c.distance_km)
        elif preference == "safest":
            # Highest safety score, lowest hazard count
            sorted_candidates = sorted(pool, key=lambda c: (-c.safety_score, len(c.hazards_intersected), c.total_cost))
        else:
            # Balanced: lowest total multi-factor cost
            sorted_candidates = sorted(pool, key=lambda c: c.total_cost)

        best = sorted_candidates[0]
        alternatives = [c for c in sorted_candidates if c.id != best.id]
        return best, alternatives

route_engine = RouteEngine()
