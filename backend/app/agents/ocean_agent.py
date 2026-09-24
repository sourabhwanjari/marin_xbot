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
        logger.info(f"[LANGGRAPH] OceanAgent executing oceanographic analysis for {location} ({time_context})")
        try:
            raw_data = get_ocean_data.invoke({"location": location, "time_context": time_context})
            result = OceanResult(
                sst=raw_data.get("sst"),
                chlorophyll=str(raw_data.get("chlorophyll")) if raw_data.get("chlorophyll") is not None else None,
                wave_height=raw_data.get("wave_height"),
                ocean_condition=raw_data.get("ocean_condition"),
                source=raw_data.get("source", "Ocean Service"),
                data_status=raw_data.get("data_status", "external")
            )
            data = result.model_dump()
            data["swell_period"] = raw_data.get("swell_period")
            data["tide_status"] = raw_data.get("tide_status")
            data["suitability"] = raw_data.get("suitability", "Favorable")
            data["timestamp"] = raw_data.get("timestamp")
            data["valid_until"] = raw_data.get("valid_until")
            logger.info(f"[LANGGRAPH] OceanAgent completed for {location}: status={data.get('data_status')}, wave={data.get('wave_height')}, sst={data.get('sst')}")
            return data
        except Exception as e:
            logger.error(f"[OceanAgent] Error executing ocean tools: {e}")
            return {
                "sst": None,
                "chlorophyll": None,
                "wave_height": None,
                "ocean_condition": None,
                "source": "Ocean Service",
                "data_status": "error",
                "error": str(e)
            }

ocean_agent = OceanAgent()
