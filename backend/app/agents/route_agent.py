import logging
from typing import Dict, Any, Optional, List, Tuple
from app.route.route_models import RouteRequest, RoutePoint, RouteResponse
from app.route.route_service import route_service
from app.data_sources.geospatial.service import geospatial_service

logger = logging.getLogger("marinex.agents.route")

class RouteAgent:
    """
    Route Agent: Specializes in recommending short and safe marine routes.
    Orchestrates the deterministic route engine, Marine Data Gateway weather/ocean
    conditions, GIS obstacle geofences, and safety scoring.
    """

    def resolve_point(self, point_input: Any, default_name: str = "Coastal Port") -> RoutePoint:
        """
        Resolves a string name, dict, or RoutePoint into a valid RoutePoint with latitude and longitude.
        """
        if isinstance(point_input, RoutePoint):
            return point_input

        if isinstance(point_input, dict):
            lat = point_input.get("lat") or point_input.get("latitude")
            lon = point_input.get("lon") or point_input.get("lng") or point_input.get("longitude")
            name = point_input.get("name") or point_input.get("port") or default_name
            if lat is not None and lon is not None:
                return RoutePoint(latitude=float(lat), longitude=float(lon), name=str(name))

        if isinstance(point_input, str):
            loc_data = geospatial_service.get_coordinates_by_name(point_input)
            if loc_data and "lat" in loc_data and "lon" in loc_data:
                return RoutePoint(
                    latitude=float(loc_data["lat"]),
                    longitude=float(loc_data["lon"]),
                    name=loc_data.get("name", point_input.title()),
                    port=loc_data.get("port")
                )

        # Fallback to Chennai coordinates if unresolvable
        return RoutePoint(latitude=13.125, longitude=80.298, name=default_name)

    def run(
        self,
        origin: Any,
        destination: Any,
        departure_time: str = "current",
        vessel_type: str = "fishing_boat",
        vessel_speed_knots: float = 10.0,
        route_preference: str = "balanced",
        avoid_zones: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes the Route Engine to determine the safest and shortest route.
        """
        logger.info(f"[LANGGRAPH] RouteAgent computing safe track from {origin} to {destination}")

        orig_pt = self.resolve_point(origin, default_name="Origin Port")
        dest_pt = self.resolve_point(destination, default_name="Destination Port")

        req = RouteRequest(
            origin=orig_pt,
            destination=dest_pt,
            departure_time=departure_time,
            vessel_type=vessel_type,
            vessel_speed_knots=vessel_speed_knots,
            route_preference=route_preference,
            avoid_zones=avoid_zones or []
        )

        resp: RouteResponse = route_service.recommend_route(req)
        return resp.model_dump()

route_agent = RouteAgent()
