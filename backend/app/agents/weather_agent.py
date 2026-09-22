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
        logger.info(f"[WeatherAgent] Executing weather analysis for {location} ({time_context})")
        try:
            raw_data = get_weather_data.invoke({"location": location, "time_context": time_context})
            result = WeatherResult(
                temperature=raw_data.get("temperature", 29.5),
                wind_speed=raw_data.get("wind_speed", 18.0),
                wind_direction=raw_data.get("wind_direction", "ENE"),
                rain_probability=raw_data.get("rain_probability", 30),
                storm_risk=raw_data.get("storm_risk", "low"),
                source=raw_data.get("source", "Open-Meteo Live Weather"),
                data_status=raw_data.get("data_status", "external")
            )
            data = result.model_dump()
            data["warnings"] = raw_data.get("warnings", [])
            data["timestamp"] = raw_data.get("timestamp")
            data["valid_until"] = raw_data.get("valid_until")
            data["description"] = raw_data.get("description")
            return data
        except Exception as e:
            logger.error(f"[WeatherAgent] Error executing weather tools: {e}")
            return {
                "temperature": 29.5,
                "wind_speed": 18.0,
                "wind_direction": "ENE (65°)",
                "rain_probability": 30,
                "storm_risk": "moderate",
                "source": "Fallback Weather Service",
                "data_status": "demo",
                "error": str(e)
            }

weather_agent = WeatherAgent()
