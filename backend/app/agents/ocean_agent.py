import logging
from typing import Dict, Any, Optional
from app.tools.ocean_tools import get_ocean_data
from app.models.agent_models import OceanResult

logger = logging.getLogger("marinex.agents.ocean")

class OceanAgent:
    """
    Ocean Agent: Evaluates oceanographic conditions, wave heights,
    sea states, SST thermal fronts, and swell periods via the Marine Data Gateway.
    """
    def run(self, location: str = "chennai", time_context: str = "current") -> Dict[str, Any]:
        logger.info(f"[OceanAgent] Executing oceanographic analysis for {location} ({time_context})")
        try:
            raw_data = get_ocean_data.invoke({"location": location, "time_context": time_context})
            result = OceanResult(
                sst=raw_data.get("sst", 28.4),
                chlorophyll=str(raw_data.get("chlorophyll", "High")),
                wave_height=raw_data.get("wave_height", 1.8),
                ocean_condition=raw_data.get("ocean_condition", "moderate"),
                source=raw_data.get("source", "Open-Meteo Marine / INCOIS"),
                data_status=raw_data.get("data_status", "external")
            )
            data = result.model_dump()
            data["swell_period"] = raw_data.get("swell_period", 8.5)
            data["tide_status"] = raw_data.get("tide_status", "Normal")
            data["suitability"] = raw_data.get("suitability", "Favorable")
            data["timestamp"] = raw_data.get("timestamp")
            data["valid_until"] = raw_data.get("valid_until")
            return data
        except Exception as e:
            logger.error(f"[OceanAgent] Error executing ocean tools: {e}")
            return {
                "sst": 28.4,
                "chlorophyll": "High (1.8 mg/m³)",
                "wave_height": 1.8,
                "ocean_condition": "moderate",
                "source": "Fallback Ocean Service",
                "data_status": "demo",
                "error": str(e)
            }

ocean_agent = OceanAgent()
