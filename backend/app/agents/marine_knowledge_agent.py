import logging
from typing import Dict, Any, List
from app.tools.rag_tools import search_marine_knowledge

logger = logging.getLogger("marinex.agents.marine_knowledge")

class MarineKnowledgeAgent:
    """
    Marine Knowledge Agent: Interacts with the Phase 2 RAG system to retrieve
    verified marine safety guidelines, regulations, and advisories with citations.
    """
    def run(self, query: str) -> Dict[str, Any]:
        logger.info(f"[MarineKnowledgeAgent] Querying marine knowledge base for: '{query[:60]}...'")
        try:
            rag_output = search_marine_knowledge.invoke({"query": query})
            return {
                "answer": rag_output.get("answer", ""),
                "sources": rag_output.get("sources", []),
                "retrieved_chunks": rag_output.get("retrieved_chunks", 0),
                "is_rag": True,
                "data_status": "verified_knowledge_base"
            }
        except Exception as e:
            logger.error(f"[MarineKnowledgeAgent] RAG search error: {e}")
            return {
                "answer": "Marine regulatory guidance unavailable for this inquiry.",
                "sources": [],
                "retrieved_chunks": 0,
                "is_rag": False,
                "data_status": "unavailable",
                "error": str(e)
            }

marine_knowledge_agent = MarineKnowledgeAgent()
