from typing import Dict, Any, List
from langchain_core.tools import tool
from app.rag.chain import marine_rag_chain
from app.rag.retriever import marine_retriever

@tool
def search_marine_knowledge(query: str) -> Dict[str, Any]:
    """
    Searches the verified marine document knowledge base (Chroma vector store)
    for safety guidelines, regulatory policies, fishing bans, and standard operating procedures.
    Returns synthesized answer and exact document citations.
    """
    rag_result = marine_rag_chain.query(query)
    return {
        "answer": rag_result.get("answer", ""),
        "sources": rag_result.get("sources", []),
        "retrieved_chunks": rag_result.get("retrieved_chunks", 0),
        "is_rag": True
    }
