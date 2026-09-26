import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.models.agent_models import PlannerOutput, QueryIntent

logger = logging.getLogger("marinex.agents.planner")

COASTAL_LOCATIONS = [
    "mumbai", "chennai", "pulicat", "kochi", "cochin",
    "visakhapatnam", "vizag", "kasimedu", "goa", "kanyakumari",
    "mangalore", "paradip", "kolkata", "gujarat"
]

INDIC_PORT_MAP = {
    "चेन्नई": "Chennai",
    "पुलिकट": "Pulicat",
    "पुलिकत": "Pulicat",
    "मुंबई": "Mumbai",
    "गोवा": "Goa",
    "कोच्चि": "Kochi",
    "कोची": "Kochi",
    "विशाखापट्टनम": "Visakhapatnam",
    "वाइजाग": "Visakhapatnam",
    "मंगलोर": "Mangalore",
    "कन्याकुमारी": "Kanyakumari",
    "पारादीप": "Paradip",
    "कोलकाता": "Kolkata",
    "गुजरात": "Gujarat",
}


TEMPORAL_PATTERNS = [
    ("tomorrow morning", "tomorrow morning"),
    ("tomorrow afternoon", "tomorrow afternoon"),
    ("tomorrow evening", "tomorrow evening"),
    ("tomorrow night", "tomorrow night"),
    ("tomorrow", "tomorrow"),
    ("this morning", "today morning"),
    ("this afternoon", "today afternoon"),
    ("this evening", "today evening"),
    ("tonight", "tonight"),
    ("today", "today"),
    ("now", "current"),
    ("next 4 hours", "next 4 hours"),
    ("next 24 hours", "next 24 hours"),
    ("weekend", "upcoming weekend")
]

class PlannerAgent:
    """
    Planner Agent: Analyzes user query, classifies intent, extracts location
    and temporal constraints, decomposes the query into tasks, and selects
    the specialized agents required for execution.
    Does NOT answer the user's question.
    """

    def _extract_route_endpoints(self, query: str, default_origin: str = "Chennai") -> Tuple[str, str]:
        q = query.strip()
        q_lower = q.lower()

        # Check Indic patterns first
        # Hindi: <orig> से <dest>
        m_hi = re.search(r'([\u0900-\u097Fa-zA-Z]+)\s+से\s+([\u0900-\u097Fa-zA-Z]+)', q)
        if m_hi:
            orig = m_hi.group(1).strip()
            dest = m_hi.group(2).strip()
            orig = INDIC_PORT_MAP.get(orig, orig).title()
            dest = INDIC_PORT_MAP.get(dest, dest).title()
            return orig, dest

        # Marathi: <orig> ते <dest> OR <orig>हून <dest>
        m_mr1 = re.search(r'([\u0900-\u097Fa-zA-Z]+)\s+ते\s+([\u0900-\u097Fa-zA-Z]+)', q)
        if m_mr1:
            orig = m_mr1.group(1).strip()
            dest = m_mr1.group(2).strip()
            orig = INDIC_PORT_MAP.get(orig, orig).title()
            dest = INDIC_PORT_MAP.get(dest, dest).title()
            return orig, dest

        m_mr2 = re.search(r'([\u0900-\u097Fa-zA-Z]+)हून\s+([\u0900-\u097Fa-zA-Z]+)', q)
        if m_mr2:
            orig = m_mr2.group(1).strip()
            dest = m_mr2.group(2).strip()
            orig = INDIC_PORT_MAP.get(orig, orig).title()
            dest = INDIC_PORT_MAP.get(dest, dest).title()
            return orig, dest

        # English patterns
        m = re.search(r'(?:from|between)\s+([a-zA-Z]+)\s+(?:to|and)\s+([a-zA-Z]+)', q_lower)
        if m:
            return m.group(1).title(), m.group(2).title()

        m2 = re.search(r'(?:to)\s+([a-zA-Z]+)\s+(?:from)\s+([a-zA-Z]+)', q_lower)
        if m2:
            return m2.group(2).title(), m2.group(1).title()

        # Check known coastal locations
        found_locs = []
        for loc in COASTAL_LOCATIONS:
            if re.search(r'\b' + re.escape(loc) + r'\b', q_lower):
                found_locs.append(loc.title())

        # Also check indic names
        for indic_name, eng_name in INDIC_PORT_MAP.items():
            if indic_name in q and eng_name not in found_locs:
                found_locs.append(eng_name)

        if len(found_locs) >= 2:
            return found_locs[0], found_locs[1]
        elif len(found_locs) == 1:
            if found_locs[0].lower() != default_origin.lower():
                return default_origin.title(), found_locs[0]
            else:
                return found_locs[0], "Pulicat"

        return default_origin.title(), "Pulicat"

    def plan(
        self,
        query: str,
        default_location: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> PlannerOutput:
        logger.info(f"[Planner] Analyzing query: '{query}'")
        q_lower = query.lower().strip()

        # 1. Extract location
        extracted_loc = None
        for indic_name, eng_name in INDIC_PORT_MAP.items():
            if indic_name in query:
                extracted_loc = eng_name
                break

        if not extracted_loc:
            for loc in COASTAL_LOCATIONS:
                if re.search(r'\b' + re.escape(loc) + r'\b', q_lower):
                    extracted_loc = loc.title()
                    break

        # If not explicitly mentioned in query, inspect recent chat history backwards
        if not extracted_loc and chat_history:
            for item in reversed(chat_history):
                content = (item.get("content") or "").lower()
                for loc in COASTAL_LOCATIONS:
                    if re.search(r'\b' + re.escape(loc) + r'\b', content):
                        extracted_loc = loc.title()
                        break
                if extracted_loc:
                    break

        if not extracted_loc:
            extracted_loc = default_location or "Chennai"  # Default coastal sector

        # 2. Extract temporal context
        extracted_time = "current"
        for pattern, normalized in TEMPORAL_PATTERNS:
            if pattern in q_lower:
                extracted_time = normalized
                break

        def _finish_plan(plan: PlannerOutput) -> PlannerOutput:
            logger.info(f"[LOCATION] location = {plan.location or 'None'}")
            logger.info(f"[ROUTER] intent = {plan.intent.value.upper()}")
            logger.info(f"[ROUTER] selected_agents = {plan.required_agents}")
            return plan

        # 3. Intent Classification & Agent Selection
        # A. Greetings, Introductions & Conversational Chit-Chat
        greeting_words = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy"]
        is_greeting = any(re.search(r'\b' + re.escape(w) + r'\b', q_lower) for w in greeting_words)
        is_identity = any(kw in q_lower for kw in ["who are you", "what can you do", "what is your name", "how can you help", "help me", "introduce yourself", "thanks", "thank you"])
        
        if is_greeting or is_identity:
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.GREETING,
                location=None,
                time=None,
                required_agents=[],
                tasks=["Provide a warm conversational welcome and outline marine intelligence capabilities"]
            ))

        # B. Explanations of Marine Concepts (PFZ, SST, Chlorophyll, Swell)
        if any(kw in q_lower for kw in ["what is pfz", "explain pfz", "how pfz works", "what is sst", "why chlorophyll", "what is swell", "what does swell mean"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.EXPLAIN_CONCEPT,
                location=None,
                time=None,
                required_agents=[],
                tasks=["Provide an educational, plain-language explanation of marine oceanography concept"]
            ))

        # C. Out of scope
        if any(kw in q_lower for kw in ["joke", "poem", "capital of", "recipe", "song", "movie", "cricket", "football"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.OUT_OF_SCOPE,
                location=None,
                time=None,
                required_agents=[],
                tasks=["Inform user that query is outside marine intelligence scope"]
            ))

        # D. Safe Route Recommendation (English, Hindi, Marathi)
        route_keywords = [
            "route", "safe route", "shortest route", "recommend route",
            "navigation route", "sailing course", "navigational track", "path from",
            "मार्ग", "रास्ता", "सुरक्षित मार्ग", "रूट", "मार्ग बताओ", "दिशा", "मार्ग दाखवा", "जाण्याचा मार्ग"
        ]
        is_route = any(kw in q_lower for kw in route_keywords) or ("safe" in q_lower and any(w in q_lower for w in ["route", "path", "corridor", "track"]))
        
        if is_route:
            orig_name, dest_name = self._extract_route_endpoints(query, default_origin=extracted_loc)
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.SAFE_ROUTE,
                location=orig_name,
                origin=orig_name,
                destination=dest_name,
                time=extracted_time,
                required_agents=["route", "weather", "ocean", "geospatial"],
                tasks=[
                    f"Calculate deterministic multi-candidate safe route from {orig_name} to {dest_name}",
                    f"Retrieve weather and wind conditions along the corridor",
                    f"Evaluate wave height and swell risk along track",
                    f"Verify clearance from restricted naval fairways and marine reserves"
                ]
            ))

        # E. Fishing / Voyage Safety (Complex multi-factor inquiry)
        safety_keywords = [
            "safe to go fishing", "is it safe", "it is safe", "safety", "can i go to sea",
            "can we go to sea", "should i go fishing", "venture into sea", "safe to sail",
            "can i sail", "can we sail", "should i sail", "is it safe to sail", "safe to travel",
            "safe for boating", "safe tomorrow", "safe today", "sailing condition",
            "small boat", "small boats", "small craft", "artisanal", "canoe", "dinghy",
            "mechanized boat", "mechanized vessel", "trawler", "can we venture", "can i venture"
        ]
        is_safety = any(kw in q_lower for kw in safety_keywords) or (("safe" in q_lower or "safety" in q_lower) and any(w in q_lower for w in ["sail", "sea", "fish", "boat", "craft", "go", "venture", "tomorrow", "today", "now"]))


        # Follow-up context inheritance: if query is brief/follow-up, check recent user history
        is_followup = any(q_lower.startswith(p) for p in ["what about", "how about", "and what about", "and for", "and "]) or len(q_lower.split()) <= 4
        if is_followup and chat_history and not is_safety:
            prev_user_queries = [h.get("content", "").lower() for h in chat_history if h.get("role") == "user"]
            last_query = prev_user_queries[-1] if prev_user_queries else ""
            if any(kw in last_query for kw in safety_keywords) or "safe" in last_query or "fishing" in last_query:
                is_safety = True

        if is_safety and not any(r in q_lower for r in ["guideline", "rule", "regulation", "law", "sop"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.FISHING_SAFETY,
                location=extracted_loc,
                time=extracted_time,
                required_agents=["weather", "ocean", "geospatial", "marine_knowledge", "risk"],
                tasks=[
                    f"Retrieve weather and wind forecast for {extracted_loc} ({extracted_time})",
                    f"Evaluate significant wave height and sea state for {extracted_loc}",
                    f"Check restricted naval fairways and marine reserves near {extracted_loc}",
                    "Search marine safety knowledge base for wave/wind operating limits",
                    "Synthesize multi-factor risk assessment (LOW/MEDIUM/HIGH)"
                ]
            ))

        # C. Potential Fishing Zone (PFZ) / Fish productivity discovery
        if any(kw in q_lower for kw in ["pfz", "fishing zone", "fishing area", "find areas with high fish", "fish productivity", "where to catch fish", "where is the nearest fishing"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.PFZ_DISCOVERY,
                location=extracted_loc,
                time=extracted_time,
                required_agents=["ocean", "geospatial"],
                tasks=[
                    f"Identify SST thermal fronts and chlorophyll convergence zones near {extracted_loc}",
                    f"Calculate distances to nearest favorable fishing zones from {extracted_loc} port"
                ]
            ))

        # D. Satellite Earth Observation (MOSDAC / Remote Sensing)
        if any(kw in q_lower for kw in ["satellite", "mosdac", "insat", "oceansat", "remote sensing", "earth observation"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.SATELLITE_DATA,
                location=extracted_loc,
                time=extracted_time,
                required_agents=["satellite"],
                tasks=[
                    f"Retrieve satellite earth observation and remote sensing telemetry for {extracted_loc}"
                ]
            ))

        # E. Restricted Zones / Boundaries
        if any(kw in q_lower for kw in ["restricted", "prohibited", "boundary", "naval channel", "anchorage", "sanctuary", "marine protected"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.RESTRICTED_ZONES,
                location=extracted_loc,
                time=extracted_time,
                required_agents=["geospatial"],
                tasks=[
                    f"Query spatial boundaries for restricted fairways and marine reserves near {extracted_loc}"
                ]
            ))

        # F. Marine Knowledge / Regulations / Guidelines
        if any(kw in q_lower for kw in ["guideline", "rule", "regulation", "law", "moratorium", "monsoon ban", "mesh size", "penalty", "sop", "document"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.MARINE_KNOWLEDGE,
                location=extracted_loc,
                time=extracted_time,
                required_agents=["marine_knowledge"],
                tasks=[
                    "Search verified marine document knowledge base for regulatory rules and guidelines"
                ]
            ))

        # G. Ocean Conditions (Waves, SST, Chlorophyll)
        if any(kw in q_lower for kw in ["ocean condition", "wave height", "swell", "sea state", "water temperature", "sst", "chlorophyll", "wave", "waves"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.OCEAN_CONDITIONS,
                location=extracted_loc,
                time=extracted_time,
                required_agents=["ocean"],
                tasks=[
                    f"Retrieve hydrodynamic wave and SST telemetry for {extracted_loc} ({extracted_time})"
                ]
            ))

        # H. Weather Inquiry (Wind, Rain, Storms)
        if any(kw in q_lower for kw in ["weather", "wind speed", "wind direction", "wind", "rain", "storm", "cyclone", "lightning", "squall", "visibility"]):
            return _finish_plan(PlannerOutput(
                intent=QueryIntent.WEATHER_INQUIRY,
                location=extracted_loc,
                time=extracted_time,
                required_agents=["weather"],
                tasks=[
                    f"Retrieve meteorological wind, rain, and storm advisories for {extracted_loc} ({extracted_time})"
                ]
            ))

        # Default fallback: General Marine assessment
        return _finish_plan(PlannerOutput(
            intent=QueryIntent.GENERAL_MARINE,
            location=extracted_loc,
            time=extracted_time,
            required_agents=["weather", "ocean", "marine_knowledge"],
            tasks=[
                f"Gather comprehensive marine conditions and guidelines for {extracted_loc}"
            ]
        ))

planner_agent = PlannerAgent()
