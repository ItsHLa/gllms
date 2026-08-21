"""RAG ingestion pipeline for the synthetic knowledge base.

Documents are upserted into the existing Pinecone index keyed by stable ids so
ingestion is idempotent. A process-level flag avoids re-uploading per request.
"""

from langchain_core.documents import Document

from backend.scenarios.cases.direct_prompt_injection_leak.documents import build_documents

_ingested = False


def ensure_ingested(vectorstore) -> None:
    """Upsert the sample documents into the vector store once per process."""
    global _ingested
    if _ingested:
        return
    documents: list[Document] = build_documents()
    ids = [d.metadata["doc_id"] for d in documents]
    vectorstore.vectorstore.add_documents(documents, ids=ids)
    _ingested = True