from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.marine_models.base import (
    MarineDataResponse, MarineEvidence, Location, TimeWindow, DataStatus
)
from app.marine_models.domains import (
    WeatherData, OceanData, PFZData, PFZFeature, SatelliteData, HazardData
)
from app.data_ingestion.common.scraper_status import calculate_freshness, FreshnessStatus

class MarineNormalizer:
    """
    Standardizes raw parsed records from official government public portals into typed
    MARINEX domain models, ensuring provenance evidence and freshness guarantees.
    """

    @staticmethod
    def normalize_weather_record(record: Dict[str, Any], location: Optional[Location] = None) -> MarineDataResponse:
        """Normalizes parsed weather data dict into MarineDataResponse with WeatherData."""
        retrieved_at = record.get("retrieved_at") or datetime.now(timezone.utc).isoformat()
        observed_at = record.get("observed_at")
        valid_until = record.get("valid_until")

        lat = float(record.get("latitude", location.latitude if location else 18.922))
        lon = float(record.get("longitude", location.longitude if location else 72.834))
        loc_name = record.get("location_name") or (location.name if location else "Coastal Sector")

        freshness_status, freshness_desc = calculate_freshness(observed_at, valid_until, category="weather")

        warnings = []
        if record.get("cyclone_warning"):
            warnings.append(f"CYCLONE WARNING: {record['cyclone_warning']}")
        if record.get("squall_warning"):
            warnings.append(f"SQUALL ADVISORY: {record['squall_warning']}")

        weather_data = WeatherData(
            temperature=record.get("temperature_c"),
            apparent_temperature=record.get("apparent_temp_c") or record.get("temperature_c"),
            wind_speed=record.get("wind_speed_knots"),
            wind_speed_knots=record.get("wind_speed_knots"),
            wind_direction=record.get("wind_direction_text"),
            wind_direction_deg=record.get("wind_direction_deg"),
            humidity=record.get("relative_humidity"),
            pressure_hpa=record.get("pressure_hpa"),
            rain_probability=record.get("rain_probability_pct"),
            precipitation_mm=record.get("precipitation_mm"),
            visibility_km=record.get("visibility_km"),
            weather_condition=record.get("weather_condition") or "Coastal Marine Observation",
            storm_risk=record.get("storm_risk", "low"),
            warnings=warnings
        )

        evidence = MarineEvidence(
            source=record.get("source", "India Meteorological Department"),
            provider="IMDCoastalScraper",
            dataset=record.get("dataset", "IMD-Coastal-AWS-Observations"),
            parameter="weather_conditions",
            observed_at=observed_at,
            valid_from=record.get("valid_from"),
            valid_until=valid_until,
            retrieved_at=retrieved_at,
            quality=record.get("quality", "OPERATIONAL"),
            confidence_score=1.0 if freshness_status in (FreshnessStatus.FRESH, FreshnessStatus.RECENT) else 0.7,
            status=DataStatus.EXTERNAL,
            evidence_url=record.get("source_url", "https://mausam.imd.gov.in"),
            metadata={
                "freshness_status": freshness_status.value,
                "freshness_description": freshness_desc,
                "location_name": loc_name,
                "station_observed": record.get("location_name")
            }
        )

        return MarineDataResponse(
            status=DataStatus.EXTERNAL,
            provider="IMD",
            dataset=record.get("dataset", "IMD-Coastal-AWS-Observations"),
            parameter="weather_conditions",
            latitude=lat,
            longitude=lon,
            observed_at=observed_at or "UNAVAILABLE",
            valid_from=record.get("valid_from"),
            valid_until=valid_until,
            retrieved_at=retrieved_at,
            quality=record.get("quality", "OPERATIONAL"),
            evidence_url=record.get("source_url"),
            location=location.to_dict() if location else {"latitude": lat, "longitude": lon, "name": loc_name},
            data=weather_data.model_dump(),
            evidence=[evidence],
            metadata={
                "freshness": freshness_status.value,
                "freshness_description": freshness_desc,
                "source": record.get("source", "IMD")
            }
        )

    @staticmethod
    def normalize_ocean_record(record: Dict[str, Any], location: Optional[Location] = None) -> MarineDataResponse:
        """Normalizes parsed ocean observation dict into MarineDataResponse with OceanData."""
        retrieved_at = record.get("retrieved_at") or datetime.now(timezone.utc).isoformat()
        observed_at = record.get("observed_at")
        valid_until = record.get("valid_until")

        lat = float(record.get("latitude", location.latitude if location else 18.922))
        lon = float(record.get("longitude", location.longitude if location else 72.834))
        sector = record.get("sector_name") or (location.name if location else "Coastal Sector")

        freshness_status, freshness_desc = calculate_freshness(observed_at, valid_until, category="ocean")

        ocean_data = OceanData(
            sst=record.get("sea_surface_temp_c"),
            chlorophyll="Moderate",
            wave_height=record.get("significant_wave_height_m"),
            swell_period=record.get("swell_period_s") or record.get("wave_period_s"),
            swell_direction=record.get("swell_direction_text"),
            ocean_condition=record.get("sea_state") or "Moderate",
            tide_status=record.get("tide_status") or "Normal",
            suitability=record.get("suitability", "Favorable")
        )

        evidence = MarineEvidence(
            source=record.get("source", "INCOIS Hyderabad"),
            provider="INCOISOceanScraper",
            dataset=record.get("dataset", "INCOIS-Ocean-State-Forecast"),
            parameter="ocean_state",
            observed_at=observed_at,
            valid_from=record.get("valid_from"),
            valid_until=valid_until,
            retrieved_at=retrieved_at,
            quality=record.get("quality", "OPERATIONAL"),
            confidence_score=1.0 if freshness_status in (FreshnessStatus.FRESH, FreshnessStatus.RECENT) else 0.7,
            status=DataStatus.EXTERNAL,
            evidence_url=record.get("source_url", "https://incois.gov.in/portal/osf/osf.jsp"),
            metadata={
                "freshness_status": freshness_status.value,
                "freshness_description": freshness_desc,
                "sector_name": sector,
                "high_wave_alert": record.get("high_wave_alert")
            }
        )

        return MarineDataResponse(
            status=DataStatus.EXTERNAL,
            provider="INCOIS-Ocean",
            dataset=record.get("dataset", "INCOIS-Ocean-State-Forecast"),
            parameter="ocean_state",
            latitude=lat,
            longitude=lon,
            observed_at=observed_at or "UNAVAILABLE",
            valid_from=record.get("valid_from"),
            valid_until=valid_until,
            retrieved_at=retrieved_at,
            quality=record.get("quality", "OPERATIONAL"),
            evidence_url=record.get("source_url"),
            location=location.to_dict() if location else {"latitude": lat, "longitude": lon, "name": sector},
            data=ocean_data.model_dump(),
            evidence=[evidence],
            metadata={
                "freshness": freshness_status.value,
                "freshness_description": freshness_desc,
                "source": record.get("source", "INCOIS")
            }
        )

    @staticmethod
    def normalize_pfz_records(records: List[Dict[str, Any]], location: Optional[Location] = None) -> MarineDataResponse:
        """Normalizes multiple PFZ advisory records into MarineDataResponse with PFZData."""
        retrieved_at = datetime.now(timezone.utc).isoformat()
        lat = location.latitude if location else 18.922
        lon = location.longitude if location else 72.834

        features: List[PFZFeature] = []
        observed_time = None
        valid_until = None

        for r in records:
            if not observed_time and r.get("observed_at"):
                observed_time = r.get("observed_at")
            if not valid_until and r.get("valid_until"):
                valid_until = r.get("valid_until")

            features.append(
                PFZFeature(
                    zone_id=r["zone_id"],
                    name=r.get("zone_name", "Fishing Zone"),
                    latitude=float(r["latitude"]),
                    longitude=float(r["longitude"]),
                    sector=r.get("sector", "Coastal Sector"),
                    distance_km=float(r.get("distance_km", 0.0)),
                    direction=r.get("direction", "NE"),
                    sst=float(r.get("sst_c", 28.0)),
                    chlorophyll=str(r.get("chlorophyll", "High")),
                    suitability=r.get("suitability", "Favorable"),
                    status="Favorable" if r.get("suitability") == "Favorable" else "Moderate",
                    dominant_species=r.get("dominant_species") or ["Pelagic", "Tuna", "Mackerel"],
                    depth_meters=int(r.get("depth_meters", 40)),
                    advisory_date=r.get("observed_at"),
                    valid_until=r.get("valid_until")
                )
            )

        freshness_status, freshness_desc = calculate_freshness(observed_time, valid_until, category="pfz")

        pfz_data = PFZData(
            zones=features,
            nearest_zone=features[0] if features else None,
            total_active_zones=len(features),
            advisory_date=observed_time
        )

        evidence = MarineEvidence(
            source="Indian National Centre for Ocean Information Services (INCOIS)",
            provider="INCOISPFZScraper",
            dataset="INCOIS-PFZ-Advisory",
            parameter="potential_fishing_zones",
            observed_at=observed_time,
            valid_until=valid_until,
            retrieved_at=retrieved_at,
            quality="HIGH",
            status=DataStatus.EXTERNAL,
            evidence_url="https://incois.gov.in/portal/pfz/pfz.jsp",
            metadata={
                "freshness_status": freshness_status.value,
                "freshness_description": freshness_desc,
                "total_zones_delineated": len(features)
            }
        )

        return MarineDataResponse(
            status=DataStatus.EXTERNAL,
            provider="INCOIS-PFZ",
            dataset="INCOIS-PFZ-Advisory",
            parameter="potential_fishing_zones",
            latitude=lat,
            longitude=lon,
            observed_at=observed_time or "UNAVAILABLE",
            valid_until=valid_until,
            retrieved_at=retrieved_at,
            quality="HIGH",
            evidence_url="https://incois.gov.in/portal/pfz/pfz.jsp",
            location=location.to_dict() if location else {"latitude": lat, "longitude": lon},
            data=pfz_data.model_dump(),
            evidence=[evidence],
            metadata={
                "freshness": freshness_status.value,
                "freshness_description": freshness_desc,
                "source": "INCOIS"
            }
        )

    @staticmethod
    def normalize_satellite_record(record: Dict[str, Any], location: Optional[Location] = None) -> MarineDataResponse:
        """Normalizes satellite record into MarineDataResponse with SatelliteData."""
        retrieved_at = record.get("retrieved_at") or datetime.now(timezone.utc).isoformat()
        pass_time = record.get("pass_timestamp") or record.get("observed_at")
        lat = float(record.get("latitude", location.latitude if location else 18.922))
        lon = float(record.get("longitude", location.longitude if location else 72.834))

        freshness_status, freshness_desc = calculate_freshness(pass_time, category="satellite")

        sat_data = SatelliteData(
            product_name=record.get("product_name", "SST"),
            satellite_mission=record.get("satellite_mission", "ISRO Oceansat-3"),
            sensor=record.get("sensor", "OCM-3 / SSTM"),
            spatial_resolution_km=float(record.get("spatial_resolution_km", 1.0)),
            pass_time=pass_time,
            granule_id=record.get("granule_id"),
            cloud_cover_percent=record.get("cloud_cover_percent"),
            status=DataStatus.EXTERNAL,
            message=f"Satellite pass {record.get('granule_id')} from {record.get('satellite_mission', 'Oceansat-3')}."
        )

        evidence = MarineEvidence(
            source="ISRO Meteorological & Oceanographic Satellite Data Archival Centre",
            provider="MOSDACSatelliteScraper",
            dataset=record.get("dataset_id", "OS3_SST_L3"),
            parameter=record.get("product_name", "sst"),
            observed_at=pass_time,
            retrieved_at=retrieved_at,
            quality="OPERATIONAL",
            status=DataStatus.EXTERNAL,
            evidence_url=record.get("download_url", "https://www.mosdac.gov.in"),
            metadata={
                "freshness_status": freshness_status.value,
                "freshness_description": freshness_desc,
                "granule_id": record.get("granule_id"),
                "cloud_cover_percent": record.get("cloud_cover_percent")
            }
        )

        return MarineDataResponse(
            status=DataStatus.EXTERNAL,
            provider="MOSDAC",
            dataset=record.get("dataset_id", "OS3_SST_L3"),
            parameter=record.get("product_name", "sst"),
            latitude=lat,
            longitude=lon,
            observed_at=pass_time or "UNAVAILABLE",
            retrieved_at=retrieved_at,
            quality="OPERATIONAL",
            evidence_url=record.get("download_url"),
            location=location.to_dict() if location else {"latitude": lat, "longitude": lon},
            data=sat_data.model_dump(),
            evidence=[evidence],
            metadata={
                "freshness": freshness_status.value,
                "freshness_description": freshness_desc,
                "source": "ISRO MOSDAC"
            }
        )
