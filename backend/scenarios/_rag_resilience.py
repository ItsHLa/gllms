"""Resilience helpers shared by every scenario RAG pipeline.

Embeddings are produced by a hosted HuggingFace inference endpoint. That
endpoint can be slow to cold-start (tens of seconds to minutes) or briefly
unavailable, which used to freeze scenario runs inside `add_documents` /
`retriever.invoke` with no feedback until the user aborted.

Two guarantees provided here:

1. INGEST ONCE — vectors live in the persistent Pinecone index, so if all
   document ids already exist we skip embedding entirely (instant startup).
2. BOUNDED WAIT — any network call is wrapped in a hard timeout. On timeout
   or failure the caller falls back to the deterministic synthetic knowledge
   base, so the demo always runs (the poisoned document is always included by
   the runner itself).

A timed-out worker thread cannot be killed in Python; it is abandoned in the
background and never blocks the main flow.
"""

import concurrent.futures

INGEST_TIMEOUT_S = 120
RETRIEVE_TIMEOUT_S = 60


def call_with_timeout(fn, timeout_s: float, *args, **kwargs):
    """Run `fn` in a worker thread and raise TimeoutError past `timeout_s`."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn, *args, **kwargs)
        return future.result(timeout=timeout_s)


def _existing_ids(index, ids: list[str]) -> set[str]:
    try:
        response = index.fetch(ids=ids)
        return set(getattr(response, "vectors", {}) or {})
    except Exception:
        return set()


def ensure_ingested(vectorstore, documents: list) -> str:
    """Upsert documents into the vector store only when they are missing.

    Returns one of: "skipped" (all ids already stored), "ingested",
    "timeout", "failed". The per-package `_ingested` flag still prevents
    repeated work within one process.
    """
    ids = [d.metadata["doc_id"] for d in documents]

    existing = _existing_ids(vectorstore.vectorstore.index, ids)
    if existing >= set(ids):
        return "skipped"

    missing = [d for d in documents if d.metadata["doc_id"] not in existing]
    if not missing:
        return "skipped"

    missing_ids = [d.metadata["doc_id"] for d in missing]
    try:
        call_with_timeout(
            lambda: vectorstore.vectorstore.add_documents(missing, ids=missing_ids),
            INGEST_TIMEOUT_S,
        )
        return "ingested"
    except concurrent.futures.TimeoutError:
        return "timeout"
    except Exception:
        return "failed"


def safe_retrieve(vectorstore, user_query: str, fallback_documents: list, top_k: int) -> list:
    """Vector search with a hard timeout; falls back to the synthetic KB.

    Always returns a list of LangChain Documents so the runner's title
    filtering and re-attachment logic behave exactly as before.
    """
    try:
        retriever = vectorstore.vectorstore.as_retriever(search_kwargs={"k": top_k})
        return call_with_timeout(retriever.invoke, RETRIEVE_TIMEOUT_S, user_query)
    except Exception:
        return list(fallback_documents)
