import os
import logging
from typing import Dict, Any, List
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.rag.config import rag_settings
from app.rag.retriever import marine_retriever
from app.rag.prompts import get_rag_prompt_template, format_docs_for_prompt

logger = logging.getLogger("marinex.rag.chain")

def get_llm():
    """
    Returns configured LLM (Google Gemini or OpenAI).
    If no API key is available, returns None so the chain uses
    the deterministic grounded synthesizer.
    """
    api_key = rag_settings.LLM_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    provider = rag_settings.LLM_PROVIDER.lower()

    if provider in ["google", "gemini"] or (provider == "auto" and os.getenv("GOOGLE_API_KEY")):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=api_key,
                temperature=0.2
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatGoogleGenerativeAI: {e}")

    if provider == "openai" or (provider == "auto" and os.getenv("OPENAI_API_KEY")):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                openai_api_key=api_key,
                temperature=0.2
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatOpenAI: {e}")

    return None

def synthesize_grounded_fallback(question: str, docs: list) -> str:
    """
    Synthesizes a clear, grounded response directly from the top retrieved chunks
    when an external LLM API key is not configured.
    Ensures 100% offline functionality without hallucinations.
    """
    if not docs:
        return (
            "The current marine knowledge base does not contain sufficient information to answer this inquiry. "
            "Please ensure relevant marine safety or regulatory documents (.pdf, .docx, .txt) are uploaded and indexed."
        )

    # Extract relevant excerpts
    excerpts = []
    for doc in docs[:3]:
        content = doc.page_content.strip()
        # Grab first 2-3 sentences or clean paragraph
        lines = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("DEMO DOCUMENT")]
        snippet = " ".join(lines[:3]) if lines else content[:300]
        excerpts.append(f"• {snippet}")

    answer = (
        f"Based on the marine documents in the knowledge base regarding \"{question}\":\n\n"
        + "\n\n".join(excerpts) +
        "\n\n(Retrieved from verified marine documentation. Consult port authorities for real-time navigation notices.)"
    )
    return answer

class MarineRagChain:
    """
    Executes the Question -> Retrieval -> Synthesis -> Citation pipeline.
    """
    def __init__(self):
        self.retriever = marine_retriever
        self.prompt = get_rag_prompt_template()

    def query(self, question: str, top_k: int = None) -> Dict[str, Any]:
        logger.info(f"[RAG] Executing RAG query: '{question}'")

        # 1. Retrieve relevant chunks
        docs = self.retriever.retrieve(question, top_k=top_k)
        sources = self.retriever.format_sources(docs)

        # 2. Check if LLM is available
        llm = get_llm()
        if llm is not None and docs:
            try:
                # LCEL pipeline
                context_str = format_docs_for_prompt(docs)
                messages = self.prompt.format_messages(context=context_str, question=question)
                response = llm.invoke(messages)
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                logger.error(f"[RAG ERROR] LLM generation failed: {e}. Falling back to grounded synthesizer.")
                answer = synthesize_grounded_fallback(question, docs)
        else:
            # Deterministic grounded synthesizer
            answer = synthesize_grounded_fallback(question, docs)

        logger.info(f"[RAG] Response generated with {len(sources)} sources.")

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(docs),
            "is_rag": True,
            "knowledge_base": "Chroma Vector Store (MarineX)"
        }

marine_rag_chain = MarineRagChain()
