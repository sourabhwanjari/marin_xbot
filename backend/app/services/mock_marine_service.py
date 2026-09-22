from typing import List
from datetime import datetime
from app.models.schemas import MarineConditions, FishingZone, MarineAlert, AlertSeverity

class MockMarineService:
    @staticmethod
    def get_conditions() -> MarineConditions:
        return MarineConditions(
            seaSurfaceTemperature=28.4,
            chlorophyll="High",
            waveHeight=1.8,
            windSpeed=18.0,
            windDirection="ENE (65°)",
            seaState="Moderate",
            visibility=8.0,
            airTemperature=29.5,
            tide="Flood Tide (+0.8m, Peak at 14:15 IST)",
            updatedAt=datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        )

    @staticmethod
    def get_fishing_zones() -> List[FishingZone]:
        return [
            FishingZone(
                id="pfz-01",
                name="Zone Alpha - Chennai Offshore",
                latitude=13.12,
                longitude=80.48,
                distanceKm=24.0,
                seaSurfaceTemperature=28.4,
                chlorophyll="High",
                suitability="Favorable",
                status="Favorable",
                dominantSpecies=["Sardine", "Mackerel", "Tuna"],
                depthMeters=52
            ),
            FishingZone(
                id="pfz-02",
                name="Zone Bravo - Pulicat Shoals",
                latitude=13.42,
                longitude=80.42,
                distanceKm=42.5,
                seaSurfaceTemperature=28.1,
                chlorophyll="High",
                suitability="Favorable",
                status="Favorable",
                dominantSpecies=["Anchovy", "Ribbon Fish", "Seer Fish"],
                depthMeters=38
            ),
            FishingZone(
                id="pfz-03",
                name="Zone Charlie - Mahabalipuram Ridge",
                latitude=12.58,
                longitude=80.35,
                distanceKm=35.2,
                seaSurfaceTemperature=27.9,
                chlorophyll="Moderate",
                suitability="Moderate",
                status="Caution",
                dominantSpecies=["Squid", "Carangids"],
                depthMeters=65
            ),
            FishingZone(
                id="pfz-04",
                name="Zone Delta - Deep Pelagic Trench",
                latitude=12.90,
                longitude=80.85,
                distanceKm=68.0,
                seaSurfaceTemperature=29.2,
                chlorophyll="Low",
                suitability="Unfavorable",
                status="Hazard",
                dominantSpecies=["Yellowfin Tuna"],
                depthMeters=180
            )
        ]

    @staticmethod
    def get_alerts() -> List[MarineAlert]:
        return [
            MarineAlert(
                id="alert-01",
                type="High Wave Warning",
                severity=AlertSeverity.HIGH,
                location="North Tamil Nadu Coast & Offshore (13.0°N - 13.5°N)",
                latitude=13.25,
                longitude=80.60,
                radius_km=30.0,
                time="Valid until 18:00 IST Today",
                short_description="High swell waves of 2.5 - 3.2 meters forecasted along the coast.",
                advisory="Small mechanized crafts and artisanal boats advised not to venture beyond 15 nautical miles."
            ),
            MarineAlert(
                id="alert-02",
                type="Lightning Alert",
                severity=AlertSeverity.MEDIUM,
                location="Pulicat Lagoon & Adjacent Waters",
                latitude=13.45,
                longitude=80.35,
                radius_km=15.0,
                time="Valid for next 4 hours",
                short_description="Isolated convective thunderstorm activity detected via INSAT-3DR.",
                advisory="Seek immediate shelter if caught offshore; disconnect tall HF antennas."
            ),
            MarineAlert(
                id="alert-03",
                type="Strong Wind Advisory",
                severity=AlertSeverity.MEDIUM,
                location="Coromandel Coast Offshore",
                latitude=12.80,
                longitude=80.50,
                radius_km=45.0,
                time="Continuous Advisory",
                short_description="Gusty winds reaching 25-30 knots likely during late afternoon squalls.",
                advisory="Maintain strict engine vigilance; ensure life vests are worn."
            ),
            MarineAlert(
                id="alert-04",
                type="Restricted Marine Zone",
                severity=AlertSeverity.LOW,
                location="Chennai Port Outer Anchorage & Naval Channel",
                latitude=13.08,
                longitude=80.32,
                radius_km=12.0,
                time="Permanent Navigation Notice",
                short_description="Commercial deep-draft vessel fairway and restricted security sector.",
                advisory="Fishing vessels must not cross security perimeter without Port Control authorization."
            )
        ]

mock_marine_service = MockMarineService()
