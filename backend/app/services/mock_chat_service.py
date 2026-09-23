from app.models.schemas import ChatResponse

class MockChatService:
    @staticmethod
    def process_message(user_message: str) -> ChatResponse:
        import re
        msg = user_message.lower().strip()

        # 1. Greetings & Introductions
        if any(re.search(r'\b' + re.escape(w) + r'\b', msg) for w in ["hi", "hello", "hey", "greetings"]) or any(k in msg for k in ["who are you", "what can you do", "help me", "introduce"]):
            content = (
                "Hello Captain! 👋 I am **MARINEX AI**, your marine intelligence and coastal decision assistant.\n\n"
                "I'm here to support your voyages with live oceanographic data, voyage risk checks, and fishing zone forecasts:\n\n"
                "• 🐟 **Potential Fishing Zones (PFZ)**: Upwelling thermal fronts and chlorophyll-a aggregations\n"
                "• 🌊 **Wave & Swell Conditions**: Wave height, sea state, and rough water warnings\n"
                "• 🌤️ **Marine Weather**: Wind speed, squall alerts, and rain probability\n"
                "• 🛡️ **Safety & Navigation**: Maritime regulations, port fairways, and safety limits\n\n"
                "How can I assist your voyage today? You can ask me questions in plain English!"
            )
            actions = ["Find Nearest PFZ", "Check Sea Safety", "View Active Alerts"]
            zones = ["Zone Alpha - Chennai Offshore"]

        # 2. Explanations of Concepts (PFZ)
        elif any(k in msg for k in ["what is pfz", "explain pfz", "how pfz works"]):
            content = (
                "### 🐟 What is a Potential Fishing Zone (PFZ)?\n\n"
                "A **Potential Fishing Zone (PFZ)** is an offshore ocean sector identified via satellite earth observation "
                "where pelagic fish (Sardines, Mackerel, Tuna) congregate.\n\n"
                "• **Thermal Fronts (SST)**: Infrared sensors detect convergence zones where cool nutrient upwelling meets warm surface waters.\n"
                "• **Chlorophyll-a**: Ocean color sensors detect phytoplankton blooms—the food source for baitfish.\n"
                "• **Operational Benefit**: Fishers reduce search time by up to **70%** and cut fuel expenditure significantly."
            )
            actions = ["Show Zone Alpha on Map", "Check Sea Safety", "Find Nearest PFZ"]
            zones = ["Zone Alpha - Chennai Offshore"]

        elif any(keyword in msg for keyword in ["nearest", "fishing zone", "pfz", "fish"]):
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
