import json
import logging
from typing import Dict, Any, List, Optional
from app.data_ingestion.common.exceptions import ScraperParsingError

logger = logging.getLogger("marinex.ingestion.parsers.json")

class JSONFeedParser:
    """
    Safely parses JSON/GeoJSON feeds from public government APIs and portal endpoints.
    Handles malformed responses, nested dictionaries, and GeoJSON features.
    """

    @staticmethod
    def parse_json(raw_text: str) -> Any:
        """Parses raw text into JSON object."""
        try:
            return json.loads(raw_text)
        except Exception as e:
            logger.error(f"[JSONFeedParser] JSON parsing error: {e}")
            raise ScraperParsingError("JSON-Feed", str(e))

    @staticmethod
    def extract_geojson_features(geojson_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts Feature list from standard FeatureCollection."""
        if not isinstance(geojson_data, dict):
            return []
        if geojson_data.get("type") == "FeatureCollection":
            return geojson_data.get("features", [])
        elif geojson_data.get("type") == "Feature":
            return [geojson_data]
        return []

    @staticmethod
    def extract_first_matching(data: Dict[str, Any], keys: List[str]) -> Optional[Any]:
        """Tries multiple candidate keys in dictionary for schema flexibility."""
        for k in keys:
            if k in data and data[k] is not None:
                return data[k]
            # Case-insensitive check
            for actual_k, val in data.items():
                if actual_k.lower() == k.lower() and val is not None:
                    return val
        return None
