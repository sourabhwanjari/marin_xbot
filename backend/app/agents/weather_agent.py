import logging
from typing import Dict, Any, Optional
from app.tools.weather_tools import get_weather_data
from app.models.agent_models import WeatherResult

logger = logging.getLogger("marinex.agents.weather")

class WeatherAgent:
    """
    Weather Agent: Analyzes marine meteorological parameters, wind vectors,
    rain probabilities, and convective squall/storm risks via the Marine Data Gateway.
    """
    def run(self, location: str = "chennai", time_context: str = "current") -> Dict[str, Any]:
        logger.info(f"[LANGGRAPH] WeatherAgent executing weather analysis for {location} ({time_context})")
        try:
            raw_data = get_weather_data.invoke({"location": location, "time_context": time_context})
            result = WeatherResult(
                temperature=raw_data.get("temperature"),
                wind_speed=raw_data.get("wind_speed"),
                wind_direction=raw_data.get("wind_direction"),
                rain_probability=raw_data.get("rain_probability"),
                storm_risk=raw_data.get("storm_risk"),
                source=raw_data.get("source", "Weather Service"),
                data_status=raw_data.get("data_status", "external")
            )
            data = result.model_dump()
            data["warnings"] = raw_data.get("warnings", [])
            data["timestamp"] = raw_data.get("timestamp")
            data["valid_until"] = raw_data.get("valid_until")
            data["description"] = raw_data.get("description")
            logger.info(f"[LANGGRAPH] WeatherAgent completed for {location}: status={data.get('data_status')}, temp={data.get('temperature')}, wind={data.get('wind_speed')}")
            return data
        except Exception as e:
            logger.error(f"[WeatherAgent] Error executing weather tools: {e}")
            return {
                "temperature": None,
                "wind_speed": None,
                "wind_direction": None,
                "rain_probability": None,
                "storm_risk": "unknown",
                "source": "Weather Service",
                "data_status": "error",
                "error": str(e),
                "description": f"Failed to retrieve weather data: {str(e)}"
            }

weather_agent = WeatherAgent()
