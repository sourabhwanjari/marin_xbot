# MarineX AI — Document Knowledge Base Directory

## Purpose
This directory stores unstructured and semi-structured documents for the **MARINEX AI** RAG (Retrieval-Augmented Generation) pipeline.

---

## Supported File Formats
- **PDF** (`.pdf`): Marine advisories, research reports, government gazettes, weather summaries.
- **TXT** (`.txt`): Plain text bulletins, incident reports, navigation notices.
- **DOCX** (`.docx`): Microsoft Word regulatory drafts, guidelines, and manuals.

---

## How to Add Documents
1. Place `.pdf`, `.docx`, or `.txt` files directly inside this `data/documents/` folder.
2. Ingest documents into the vector store using:
   - **UI**: Click the **Knowledge Base** button in the top navigation bar of the MARINEX AI dashboard and click **Run Ingestion** (or upload files directly through the modal).
   - **API**: Send a `POST` request to `http://localhost:8000/api/rag/ingest`.
   - **CLI**: Run `python -m app.rag.ingestion` from the `backend` directory.

---

## Guidelines for Hackathon Demonstration
> [!IMPORTANT]
> - Do not commit confidential or copyrighted government documents.
> - Clearly label test documents as **DEMO DOCUMENT — NOT OFFICIAL MARINE ADVISORY** to avoid presenting simulated knowledge as official legal guidance.
