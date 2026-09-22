import logging
from enum import Enum
from typing import Dict, Any
from app.rag.chain import marine_rag_chain
from app.services.mock_chat_service import mock_chat_service
from app.services.mock_marine_service import mock_marine_service
from app.models.schemas import ChatResponse

logger = logging.getLogger("marinex.services.query_router")

class QueryIntent(str, Enum):
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"
    LIVE_MARINE_DATA = "LIVE_MARINE_DATA"
    MIXED = "MIXED"

KNOWLEDGE_KEYWORDS = [
    "guideline", "guidelines", "rule", "rules", "regulation", "regulations",
    "law", "laws", "say about", "manual", "moratorium", "ban", "mesh",
    "penalty", "sop", "document", "documents", "protocol", "protocols",
    "epirb", "channel 16", "vhf", "policy", "what conditions should fishermen avoid",
    "what does", "according to", "monsoon ban", "prohibited", "permit", "permissible"
]

LIVE_KEYWORDS = [
    "current", "now", "today", "tomorrow", "nearest", "live", "weather status",
    "present", "forecast", "right now", "temperature", "sst", "chlorophyll",
    "where is the nearest", "wave height", "wind speed", "tide"
]

class QueryRouter:
    """
    Deterministic query router classifying queries into:
    - KNOWLEDGE_BASE (routes to RAG)
    - LIVE_MARINE_DATA (routes to Phase 1 mock marine service)
    - MIXED (combines RAG knowledge with current marine conditions)
    """
    @staticmethod
    def classify_intent(message: str) -> QueryIntent:
        msg = message.lower().strip()

        has_knowledge = any(kw in msg for kw in KNOWLEDGE_KEYWORDS)
        has_live = any(kw in msg for kw in LIVE_KEYWORDS)

        if has_knowledge and has_live:
            return QueryIntent.MIXED
        elif has_knowledge:
            return QueryIntent.KNOWLEDGE_BASE
        else:
            return QueryIntent.LIVE_MARINE_DATA

    @classmethod
    def route_and_execute(cls, message: str) -> ChatResponse:
        intent = cls.classify_intent(message)
        logger.info(f"[QUERY ROUTER] Query: '{message[:50]}...' -> Intent: {intent.value}")

        if intent == QueryIntent.KNOWLEDGE_BASE:
            # Route to RAG pipeline
            rag_result = marine_rag_chain.query(message)
            return ChatResponse(
                message=rag_result["answer"],
                source="rag-knowledge-base",
                is_demo=True,
                suggested_actions=["View Safety Guidelines", "Check Current Sea State", "Ask another policy question"],
                related_zones=[],
                sources=rag_result["sources"],
                is_rag=True,
                retrieved_chunks=rag_result["retrieved_chunks"]
            )

        elif intent == QueryIntent.MIXED:
            # Combined: Retrieve knowledge context + Inject current marine conditions
            rag_result = marine_rag_chain.query(message)
            conditions = mock_marine_service.get_conditions()

            combined_message = (
                f"{rag_result['answer']}\n\n"
                f"── Current Observed Sea State Correlation ──\n"
                f"• Significant Wave Height: {conditions.waveHeight} m ({conditions.seaState})\n"
                f"• Sustained Wind: {conditions.windSpeed} kts from {conditions.windDirection}\n"
                f"• Sea Surface Temperature: {conditions.seaSurfaceTemperature}°C\n"
                f"• Operational Note: Current 1.8m swell approaches the 2.0m artisanal advisory threshold."
            )

            return ChatResponse(
                message=combined_message,
                source="rag-knowledge-base + live-simulation",
                is_demo=True,
                suggested_actions=["Inspect Swell on Map", "View Active Alerts", "Read Safety Document"],
                related_zones=["Zone Alpha - Chennai Offshore"],
                sources=rag_result["sources"],
                is_rag=True,
                retrieved_chunks=rag_result["retrieved_chunks"]
            )

        else:
            # Live marine telemetry query (Phase 1 mock service)
            phase1_res = mock_chat_service.process_message(message)
            return ChatResponse(
                message=phase1_res.message,
                source=phase1_res.source,
                is_demo=phase1_res.is_demo,
                suggested_actions=phase1_res.suggested_actions,
                related_zones=phase1_res.related_zones,
                sources=[],
                is_rag=False,
                retrieved_chunks=0
            )

query_router = QueryRouter()
