"""RAG ingestion pipeline for the sample knowledge base.

Documents are upserted into the existing Pinecone index (the same one the
agent's knowledge-base tool uses), keyed by stable ids so ingestion is
idempotent. A process-level flag avoids re-uploading on every request.

Ingestion is resilient: ids already stored in the index are never re-embedded,
and the embedding endpoint is bounded by a hard timeout so a slow cold start
cannot freeze a scenario run.
"""

from backend.scenarios._rag_resilience import ensure_ingested as _ensure_ingested
from backend.scenarios.cases.indirect_prompt_injection.documents import build_documents

_ingested = False


def ensure_ingested(vectorstore) -> None:
    """Upsert the sample documents into the vector store once per process."""
    global _ingested
    if _ingested:
        return
    _ensure_ingested(vectorstore, build_documents())
    _ingested = True
