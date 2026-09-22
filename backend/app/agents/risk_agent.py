import logging
from typing import Dict, Any, List, Optional
from app.models.agent_models import RiskResult

logger = logging.getLogger("marinex.agents.risk")

class RiskAgent:
    """
    Risk Assessment Agent: Performs multi-factor probabilistic reasoning over
    meteorological, oceanographic, geospatial, and regulatory evidence.
    Prototype assessment based on available data.
    """
    def run(
        self,
        weather: Optional[Dict[str, Any]] = None,
        ocean: Optional[Dict[str, Any]] = None,
        geospatial: Optional[Dict[str, Any]] = None,
        rag: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        logger.info("[RiskAgent] Synthesizing multi-factor marine risk assessment")

        risk_factors: List[str] = []
        recommendation_basis: List[str] = [
            "MARINEX AI Risk Assessment — Prototype assessment based on available data"
        ]
        score = 0.0

        # 1. Weather risk evaluation
        if weather and weather.get("data_status") != "unavailable":
            w_src = weather.get("source", "Weather Service")
            recommendation_basis.append(f"Meteorological conditions ({w_src})")
            wind_spd = weather.get("wind_speed")
            storm_risk = str(weather.get("storm_risk", "")).lower()

            if wind_spd is not None:
                if wind_spd >= 22.0:
                    score += 3.5
                    risk_factors.append(f"Gale/squall winds exceeding {wind_spd} knots")
                elif wind_spd >= 16.0:
                    score += 2.0
                    risk_factors.append(f"Breezy winds of {wind_spd} knots (moderate coastal chop)")

            if storm_risk in ["moderate", "high"]:
                score += 2.0
                risk_factors.append("Active convective squall/lightning risk in sector")

        # 2. Oceanographic risk evaluation
        if ocean and ocean.get("data_status") != "unavailable":
            o_src = ocean.get("source", "Ocean Service")
            recommendation_basis.append(f"Hydrodynamic sea-state conditions ({o_src})")
            wave_h = ocean.get("wave_height")

            if wave_h is not None:
                if wave_h >= 2.5:
                    score += 4.0
                    risk_factors.append(f"High swell waves of {wave_h}m (Rough sea state)")
                elif wave_h >= 1.7:
                    score += 2.0
                    risk_factors.append(f"Moderate swell waves of {wave_h}m approaching artisanal limits")

        # 3. Geospatial risk evaluation
        if geospatial and geospatial.get("data_status") != "unavailable":
            recommendation_basis.append("Geospatial navigation and boundary analysis")
            if geospatial.get("restricted_zone"):
                score += 2.5
                restr_name = geospatial.get("nearest_hazard") or "Naval Fairway"
                risk_factors.append(f"Proximity to restricted maritime fairway ({restr_name})")
            if geospatial.get("protected_zone"):
                recommendation_basis.append("Marine Protected Area / Sanctuary constraints")
                risk_factors.append("Marine Protected Area: mechanized bottom-trawling prohibited")

        # 4. Regulatory RAG guidance
        if rag and rag.get("answer"):
            recommendation_basis.append("Marine Safety & Fisheries guidelines (Verified RAG)")

        # Determine overall risk category
        wave_val = ocean.get("wave_height") if ocean else None
        if score >= 5.0 or (wave_val and wave_val >= 3.0):
            risk_level = "HIGH"
        elif score >= 2.5 or (wave_val and wave_val >= 1.6):
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if not risk_factors:
            risk_factors.append("Benign coastal conditions with calm to slight sea state")

        result = RiskResult(
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommendation_basis=recommendation_basis,
            confidence=0.88
        )
        logger.info(f"[RiskAgent] Assessed Risk Level: {risk_level} (Score: {score})")
        return result.model_dump()

risk_agent = RiskAgent()
