from app.models.schemas import ChatResponse

class MockChatService:
    @staticmethod
    def process_message(user_message: str) -> ChatResponse:
        msg = user_message.lower().strip()

        if any(keyword in msg for keyword in ["nearest", "fishing zone", "pfz", "fish"]):
            content = (
                "Based on the currently available marine data, the nearest favorable fishing zone is "
                "approximately 24 km from your selected location (Zone Alpha - Chennai Offshore).\n\n"
                "• Sea Surface Temperature: 28.4°C\n"
                "• Chlorophyll: High (Thermal gradient detected)\n"
                "• Sea condition: Moderate (Wave height 1.8m)\n"
                "• Estimated fishing suitability: Favorable 🟢\n"
                "• Target pelagic species: Sardine, Mackerel, Tuna\n\n"
                "View the location on the map for more details."
            )
            actions = ["Show Zone Alpha on Map", "Check Weather along Route", "Get Navigation Coordinates"]
            zones = ["Zone Alpha - Chennai Offshore", "Zone Bravo - Pulicat Shoals"]

        elif any(keyword in msg for keyword in ["safe", "tomorrow", "weather", "wind", "condition", "sea"]):
            content = (
                "Marine Weather & Safety Evaluation:\n\n"
                "• Sea State: Moderate with significant wave height of 1.8 m\n"
                "• Wind: 18 knots gusting to 25 knots from ENE\n"
                "• Air Temperature: 29.5°C | Sea Surface Temp: 28.4°C\n"
                "• Active Notice: High Wave Warning in offshore waters beyond 15 nautical miles.\n\n"
                "Recommendation: Small artisanal craft should operate nearshore. Mechanized boats may operate "
                "with standard safety precautions and life vests on board."
            )
            actions = ["View Wave Forecast", "Check Active Warnings", "Find Sheltered Anchorage"]
            zones = ["Zone Alpha - Chennai Offshore"]

        elif any(keyword in msg for keyword in ["cyclone", "lightning", "alert", "warning", "hazard"]):
            content = (
                "Active Marine Safety Alerts for your coastal sector:\n\n"
                "1. 🔴 High Wave Warning: Valid until 18:00 IST today (North Tamil Nadu offshore sector).\n"
                "2. 🟡 Lightning Alert: Valid for next 4 hours near Pulicat Lagoon & coastal waters.\n"
                "3. 🟡 Strong Wind Advisory: Gusty conditions up to 30 knots in squall patches.\n"
                "4. ℹ️ Cyclone Status: No tropical cyclone formation detected over Southwest Bay of Bengal.\n\n"
                "Please observe geofenced safety perimeters on the map."
            )
            actions = ["Inspect Hazard Zones on Map", "View Port Control Notices", "Share Safety Advisory"]
            zones = ["Restricted Zone - Chennai Port", "Hazard Zone - Deep Pelagic"]

        else:
            content = (
                f"Marine Intelligence Query Received: \"{user_message}\"\n\n"
                "In Phase 1 (Simulated Marine Intelligence), I can synthesize information regarding:\n"
                "• Potential Fishing Zones (PFZs) derived from SST & Chlorophyll thermal fronts\n"
                "• Oceanographic conditions (Wave height, Sea state, Currents, Water temp)\n"
                "• Meteorological advisories & Coastal hazard warnings\n"
                "• Geofenced port anchorages & Restricted security zones\n\n"
                "Try asking: 'Where is the nearest Potential Fishing Zone?' or 'Is it safe to go fishing tomorrow morning?'"
            )
            actions = ["Find Nearest PFZ", "Check Sea Safety", "View Active Alerts"]
            zones = ["Zone Alpha - Chennai Offshore"]

        return ChatResponse(
            message=content,
            source="mock-data",
            is_demo=True,
            suggested_actions=actions,
            related_zones=zones
        )

mock_chat_service = MockChatService()
