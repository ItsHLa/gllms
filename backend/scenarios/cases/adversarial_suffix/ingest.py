"""RAG ingestion pipeline for the Adversarial Suffix scenario.

Documents are upserted into the existing Pinecone index keyed by stable ids so
ingestion is idempotent. A process-level flag avoids re-uploading per request.
"""

from backend.scenarios._rag_resilience import ensure_ingested as _ensure_ingested
from backend.scenarios.cases.adversarial_suffix.documents import build_documents

_ingested = False


def ensure_ingested(vectorstore) -> None:
    """Upsert the sample documents into the vector store once per process."""
    global _ingested
    if _ingested:
        return
    _ensure_ingested(vectorstore, build_documents())
    _ingested = True
