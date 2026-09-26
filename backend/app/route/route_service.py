import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.marine_gateway.gateway import marine_gateway
from app.marine_models.base import Location, TimeWindow
from app.data_sources.geospatial.service import geospatial_service
from app.route.route_models import (
    RouteRequest, RouteResponse, RoutePoint, RouteConditions, RouteCandidate
)
from app.route.route_validator import route_validator
from app.route.route_engine import route_engine

logger = logging.getLogger("marinex.route.service")

class RouteService:
    """
    High-level Marine Route Recommendation Service.
    Orchestrates the Marine Data Gateway, geospatial boundary checks,
    deterministic route generation, and safety scoring.
    """

    def __init__(self):
        self.gateway = marine_gateway
        self.engine = route_engine
        self.validator = route_validator

    def _get_geospatial_obstacles(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Loads restricted maritime zones and active hazard polygons from GIS service."""
        restricted = []
        hazards = []

        all_features = list(geospatial_service.restricted) + list(geospatial_service.protected)
        for feature in all_features:
            prop = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords_raw = geom.get("coordinates", [])

            # GeoJSON coordinates are [lon, lat], convert to [lat, lon] for Leaflet / haversine
            polygon_pts = []
            if geom.get("type") == "Polygon" and coords_raw:
                ring = coords_raw[0]
                polygon_pts = [[pt[1], pt[0]] for pt in ring]

            restricted.append({
                "name": prop.get("name", "Restricted Area"),
                "type": prop.get("type", "Naval Fairway / Marine Sanctuary"),
                "coordinates": polygon_pts
            })

        for feature in geospatial_service.hazards:
            prop = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords_raw = geom.get("coordinates", [])

            polygon_pts = []
            if geom.get("type") == "Polygon" and coords_raw:
                ring = coords_raw[0]
                polygon_pts = [[pt[1], pt[0]] for pt in ring]

            hazards.append({
                "name": prop.get("name", "Hazard Area"),
                "severity": prop.get("severity", "HIGH"),
                "description": prop.get("description", "High Wave / Storm Surge Sector"),
                "coordinates": polygon_pts
            })

        return restricted, hazards

    def recommend_route(self, request: RouteRequest) -> RouteResponse:
        """
        Calculates and returns the recommended marine route.
        Adheres to safety-first principles and full evidence attribution.
        """
        logger.info(f"[RouteService] Calculating route from {request.origin.name or request.origin.to_tuple()} to {request.destination.name or request.destination.to_tuple()}")

        # 1. Input Validation
        is_valid, err_msg = self.validator.validate_request(request)
        if not is_valid:
            logger.warning(f"[RouteService] Invalid route request: {err_msg}")
            return RouteResponse(
                route_id=f"route_err_{uuid.uuid4().hex[:8]}",
                origin=request.origin,
                destination=request.destination,
                distance_km=0.0,
                estimated_duration_hours=0.0,
                estimated_duration_text="N/A",
                safety_score=0,
                risk_level="UNAVAILABLE",
                route_conditions=RouteConditions(),
                warnings=[f"Invalid request: {err_msg}"],
                explanation="Route calculation could not be performed due to invalid coordinates.",
                status="ERROR"
            )

        # 2. Retrieve Marine Conditions from Gateway (Origin & Destination)
        loc_origin = Location(latitude=request.origin.latitude, longitude=request.origin.longitude, name=request.origin.name)
        tw = TimeWindow(context=request.departure_time or "current")

        weather_resp = self.gateway.get_weather(location=loc_origin, time_window=tw)
        ocean_resp = self.gateway.get_ocean_conditions(location=loc_origin, time_window=tw)
        hazards_list = self.gateway.get_hazards(location=loc_origin)

        # Extract normalized telemetry
        wind_speed = weather_resp.wind_speed
        wave_height = ocean_resp.wave_height
        sst = ocean_resp.sst or ocean_resp.sea_surface_temperature
        sea_state = ocean_resp.ocean_condition or "Moderate"
        weather_desc = weather_resp.weather_condition or "Marine Coastal Skies"

        active_advisory = False
        squall_warning = None
        warnings = []

        if weather_resp.warnings:
            warnings.extend(weather_resp.warnings)
            active_advisory = True
            squall_warning = weather_resp.warnings[0]

        if ocean_resp.metadata.get("high_wave_alert"):
            warnings.append(f"INCOIS ALERT: {ocean_resp.metadata['high_wave_alert']}")
            active_advisory = True

        for h in hazards_list:
            if h.get("severity") in ("high", "HIGH"):
                warnings.append(f"WARNING: {h.get('short_description', 'Active coastal advisory')}")

        conditions = RouteConditions(
            avg_wind_speed_knots=wind_speed,
            max_wave_height_m=wave_height,
            sea_surface_temp_c=sst,
            sea_state=sea_state,
            weather_summary=weather_desc,
            tide_status=ocean_resp.tide_status,
            advisory_active=active_advisory,
            squall_warning=squall_warning
        )

        # 3. Load Spatial Obstacles (Restricted Fairways, Protected Areas, Hazard Zones)
        restricted_areas, hazard_polygons = self._get_geospatial_obstacles()

        # 4. Generate & Score Candidate Tracks
        origin_pt = (request.origin.latitude, request.origin.longitude)
        dest_pt = (request.destination.latitude, request.destination.longitude)

        candidates = self.engine.generate_candidate_routes(
            origin=origin_pt,
            destination=dest_pt,
            restricted_areas=restricted_areas,
            hazard_areas=hazard_polygons,
            conditions=conditions,
            vessel_speed_knots=request.vessel_speed_knots
        )

        best_candidate, alternatives = self.engine.select_best_route(
            candidates,
            preference=request.route_preference
        )

        # Format Duration Text
        hours = int(best_candidate.estimated_duration_hours)
        minutes = int(round((best_candidate.estimated_duration_hours - hours) * 60))
        duration_text = f"{hours}h {minutes}m" if hours > 0 else f"{minutes} min"

        # Evidence Attribution
        evidence = [
            {
                "source": weather_resp.provider,
                "dataset": weather_resp.dataset,
                "parameter": "Wind & Atmospheric Pressure",
                "observed_at": weather_resp.observed_at,
                "retrieved_at": weather_resp.retrieved_at,
                "quality": weather_resp.quality
            },
            {
                "source": ocean_resp.provider,
                "dataset": ocean_resp.dataset,
                "parameter": "Wave Height & Sea State",
                "observed_at": ocean_resp.observed_at,
                "retrieved_at": ocean_resp.retrieved_at,
                "quality": ocean_resp.quality
            },
            {
                "source": "Maritime GIS / PostGIS",
                "dataset": "Indian-Maritime-Boundaries-EEZ",
                "parameter": "Restricted Fairways & MPAs",
                "quality": "OPERATIONAL"
            }
        ]

        # Concise Explanation
        avoided_str = ""
        if best_candidate.costs.get("restricted_penalty", 0) == 0:
            avoided_str += "avoids all configured restricted naval/port fairways; "
        if best_candidate.costs.get("hazard_cost", 0) == 0:
            avoided_str += "maintains clear distance from detected hazard surge polygons; "

        explanation = (
            f"Recommended {best_candidate.name} balances shortest feasible distance ({best_candidate.distance_km} km) "
            f"with lower marine risk (Safety Score: {best_candidate.safety_score}/100, Risk: {best_candidate.risk_level}). "
            f"The track {avoided_str}considers current wind ({wind_speed or 'N/A'} kts) and swell conditions ({wave_height or 'N/A'}m)."
        )

        # GeoJSON LineString for Map Rendering
        # GeoJSON coordinates are [lon, lat]
        geojson_geometry = {
            "type": "LineString",
            "coordinates": [[pt[1], pt[0]] for pt in best_candidate.waypoints]
        }

        # Format Alternatives
        alt_dicts = []
        for alt in alternatives:
            alt_dicts.append({
                "id": alt.id,
                "name": alt.name,
                "distance_km": alt.distance_km,
                "duration_hours": alt.estimated_duration_hours,
                "safety_score": alt.safety_score,
                "risk_level": alt.risk_level,
                "waypoints": alt.waypoints,
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[pt[1], pt[0]] for pt in alt.waypoints]
                }
            })

        return RouteResponse(
            route_id=f"route_{uuid.uuid4().hex[:10]}",
            origin=request.origin,
            destination=request.destination,
            route_geometry=geojson_geometry,
            waypoints=best_candidate.waypoints,
            distance_km=best_candidate.distance_km,
            estimated_duration_hours=best_candidate.estimated_duration_hours,
            estimated_duration_text=duration_text,
            safety_score=best_candidate.safety_score,
            risk_level=best_candidate.risk_level,
            route_conditions=conditions,
            hazards_avoided=[h for h in ["Hazard Zone Alpha", "Nearshore Reef Sector"] if h not in best_candidate.hazards_intersected],
            avoided_zones=["Naval Channel", "Port Security Fairway"],
            warnings=warnings,
            evidence=evidence,
            explanation=explanation,
            status="SUCCESS",
            alternative_routes=alt_dicts
        )

route_service = RouteService()

def get_route_service() -> RouteService:
    return route_service
