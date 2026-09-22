# MARINEX AI — Phase 2 Architecture: LangChain + RAG Pipeline
### Official Problem Statement: ORCA — Marine EcOsystem Reasoning with Collaborative Agents

## 1. High-Level Flow

```
                  ┌──────────────────────┐
                  │      User Query      │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │   Next.js Chat UI    │
                  └──────────┬───────────┘
                             │ HTTP POST /api/chat
                  ┌──────────▼───────────┐
                  │   FastAPI Gateway    │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │     Query Router     │
                  └─────┬──────────┬─────┘
                        │          │
         ┌──────────────┘          └──────────────┐
         ▼ (Knowledge Base)                       ▼ (Live Telemetry)
┌─────────────────────────────────┐      ┌─────────────────────────────────┐
│          RAG Pipeline           │      │    Phase 1 Mock Marine Service  │
│  - MarineRetriever (top-k=4)    │      │    - Conditions (SST, Waves)    │
│  - Chroma Vector Store          │      │    - Potential Fishing Zones    │
│  - Marine Prompt Grounding      │      │    - Active Marine Alerts       │
│  - LLM / Grounded Synthesizer   │      └────────────────┬────────────────┘
└────────────────┬────────────────┘                       │
                 │                                        │
                 └────────────────┬───────────────────────┘
                                  ▼
                  ┌───────────────────────────────┐
                  │  Synthesized Response Payload │
                  │  - Answer Text                │
                  │  - Source Citations (p. & doc)│
                  │  - Knowledge Source Badge     │
                  └───────────────┬───────────────┘
                                  ▼
                  ┌───────────────────────────────┐
                  │      Enhanced Marine UI       │
                  └───────────────────────────────┘
```

---

## 2. RAG Ingestion & Vector Storage Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                      Document Ingestion                     │
│  data/documents/ (*.pdf, *.docx, *.txt, *.md)               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Loaders Layer (loaders.py)                  │
│  - load_pdf (pypdf: extracts pages & metadata)              │
│  - load_docx (python-docx: paragraphs & tables)             │
│  - load_txt (UTF-8 normalizer with fallback)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Text Splitter (splitter.py)                  │
│  - RecursiveCharacterTextSplitter                           │
│  - CHUNK_SIZE = 1000, CHUNK_OVERLAP = 150                   │
│  - Deterministic Chunk ID Hash generation                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Embedding Layer (embeddings.py)                │
│  - Google Gemini / OpenAI Embeddings (if API key provided)  │
│  - Deterministic Local Embeddings (384-dim offline fallback)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Vector Store (vectorstore.py)                   │
│  - Chroma (backend/storage/chroma)                          │
│  - Duplicate Prevention via indexed_chunks_registry.json    │
│  - Swappable interface for PostgreSQL + pgvector (Phase 4)  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Query Router Deterministic Logic

| Query Type | Example | Routed To | Response Details |
|---|---|---|---|
| **KNOWLEDGE_BASE** | *"What does the marine safety guideline say about high waves?"* | `MarineRagChain` | Evidence-backed answer + Source citations (`file_name` & `page`) + `🧠 RAG Knowledge Base` badge. |
| **LIVE_MARINE_DATA** | *"What is the current wave condition?"* | `MockMarineService` | Current telemetry (1.8m wave height, Moderate sea state) + `🛰️ Live Marine Data` badge. |
| **MIXED** | *"What do safety guidelines say about current wave conditions?"* | `MarineRagChain` + `MockMarineService` | Regulatory safety threshold correlated with active 1.8m observed wave height. |

---

## 4. Future Compatibility with Phase 3 (LangGraph)
In Phase 3, `marine_retriever` will become a standard LangChain Tool callable by the **Marine Advisory Agent** and **Risk Assessment Agent** within a cyclic LangGraph state machine:
```python
@tool
def query_marine_knowledge_base(query: str) -> str:
    """Searches the verified marine document knowledge base for regulatory and safety rules."""
    return marine_rag_chain.query(query)["answer"]
```
No re-architecture will be required when transitioning into Phase 3.
