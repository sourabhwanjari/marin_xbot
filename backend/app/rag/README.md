# Marine RAG (Retrieval-Augmented Generation) Architecture

## Overview
MARINEX AI utilizes a domain-specific Marine RAG pipeline to ground conversational responses in authoritative oceanographic, meteorological, and regulatory literature.

```
┌─────────────────────────────────────────────────────────────┐
│                      Document Corpus                        │
│  - Marine Advisories & Navigational Warnings                │
│  - Fishing Guidelines (ICAR-CMFRI, Dept of Fisheries)       │
│  - Satellite Telemetry Manuals (MOSDAC/ISRO, Oceansat)      │
│  - Oceanographic Ocean State Guides (INCOIS)                │
│  - Marine Safety & Disaster SOPs (Coast Guard / NDMA)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Ingestion Stage                       │
│  1. Document Loader (PDF, HTML, CAP-XML, NetCDF metadata)   │
│  2. Text Cleaning & Normalization                           │
│  3. Semantic & Spatial Chunking (with Lat/Lon metadata)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Embedding Stage                       │
│  - Embedding Model (e.g., text-embedding-3-large / BAAI)    │
│  - Storage in PostgreSQL + pgvector Extension               │
│  - Hybrid Index: HNSW (dense vector) + BM25 (sparse keyword)│
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Retrieval Stage                       │
│  - User Query Embedding                                     │
│  - Spatial Filtering (Bounding box / Coastal sector)        │
│  - Reciprocal Rank Fusion (Dense Vector + BM25 Keywords)    │
│  - Re-ranking (Cross-Encoder / Cohere Rerank)               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Generation & Audit                      │
│  - Prompt Synthesis with Retrieved Passages                 │
│  - LLM Inference with Strict Marine System Instructions     │
│  - Grounded Citation & Source Verification                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Target Document Collections
1. **Marine Advisories**: INCOIS daily bulletins, port warnings, tsunami bulletins.
2. **Fisheries Guidelines**: Seasonal fishing bans, permissible mesh sizes, endangered marine fauna regulations.
3. **Earth Observation Guides**: MOSDAC SST interpretation, chlorophyll-a front mechanics, upwelling indicator guides.
4. **Safety & Emergency SOPs**: Cyclone survival protocols, man-overboard rescue routines, distress channel frequencies (VHF Ch 16).

---

## Phase 1 Status
In Phase 1, no live vector database is connected. API contracts and mock services simulate evidence-backed responses with source provenance.
