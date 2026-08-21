"""Live runner for the Sensitive Data Disclosure scenario.

Real implementation: it uses the exact same components as main.py
(LLMFactory, RAGVectorStore, Agent with InMemorySaver) to demonstrate the
indirect prompt injection against a real LLM, then returns a structured result
for the UI.

Flow:
    user_query -> embed -> vector db -> retrieve
    -> trust boundary -> prompt construction -> LLM agent
    -> sensitive-data detector / security validation -> response
"""

from langgraph.checkpoint.memory import InMemorySaver

from backend.scenarios._rag_resilience import safe_retrieve
from backend.scenarios.cases.sensitive_data_disclosure import detection, documents, ingest, prompts
from src.agent import Agent
from src.llm import LLMFactory
from src.vector_store import RAGVectorStore

MODEL_NAME = "gemini-3.1-flash-lite-preview"
MODEL_PROVIDER = "genai"
TOP_K = 12

# Only documents from this scenario's knowledge base may be used.
_KNOWN_TITLES = {d.metadata["title"] for d in documents.build_documents()}

_BLOCKED_RESPONSE = (
    "I can provide a high-level summary of the relevant policies, but I cannot "
    "disclose complete internal policy documents, personal information, "
    "credentials, or internal security configuration.\n\n"
    "The retrieved documents contain information about data collection, "
    "processing, retention, privacy requirements, and user rights."
)

_vectorstore_cache: RAGVectorStore | None = None


def _get_vectorstore() -> RAGVectorStore:
    global _vectorstore_cache
    if _vectorstore_cache is None:
        _vectorstore_cache = RAGVectorStore()
    return _vectorstore_cache


def _build_agent(system_prompt: str) -> Agent:
    model = LLMFactory.create(provider=MODEL_PROVIDER, model=MODEL_NAME, temperature=0)
    return Agent(
        model=model,
        checkpointer=InMemorySaver(),
        system_prompt=system_prompt,
        tools=[],
    )


def _retrieve(vectorstore: RAGVectorStore, user_query: str) -> list[dict]:
    docs = safe_retrieve(vectorstore, user_query, documents.build_documents(), TOP_K)
    seen = set()
    unique = []
    for d in docs:
        title = d.metadata.get("title") or "Untitled"
        if title not in _KNOWN_TITLES or title in seen:
            continue
        seen.add(title)
        unique.append(d)

    # The poisoned document must be retrieved for the demonstration to show the
    # attack in BOTH modes. The shared index is noisy (duplicated vectors), so
    # if vector search missed it we re-attach it from the synthetic knowledge
    # base. The malicious instruction is never removed from the document.
    for poisoned in documents.build_documents():
        title = poisoned.metadata["title"]
        if title in documents.POISONED_TITLES and title not in seen:
            unique.insert(0, poisoned)
            seen.add(title)

    return [
        {
            "title": d.metadata.get("title", "Untitled"),
            "category": d.metadata.get("category", "unknown"),
            "content": d.page_content,
            "malicious": d.metadata.get("title") in documents.POISONED_TITLES,
        }
        for d in unique
    ]


def _extract_text(response: object) -> str:
    """Normalize an LLM response into plain text."""
    if isinstance(response, str):
        return response
    if isinstance(response, list):
        parts = []
        for part in response:
            if isinstance(part, dict):
                parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        return "\n".join(p for p in parts if p)
    return str(response)


def run(user_query: str | None = None, mode: str = "protected", session_id: str = "s2") -> dict:
    user_query = (user_query or "").strip() or documents.DEFAULT_USER_QUERY
    mode = mode if mode in ("vulnerable", "protected") else "protected"

    vectorstore = _get_vectorstore()
    ingest.ensure_ingested(vectorstore)

    retrieved = _retrieve(vectorstore, user_query)

    injection_alerts = detection.scan(retrieved)
    sensitive_docs = detection.scan_sensitive(retrieved)
    attack_detected = len(injection_alerts) > 0

    system_prompt, user_prompt = prompts.build_prompts(user_query, retrieved, mode)

    agent = _build_agent(system_prompt)
    trace = agent.call_with_trace(user_prompt, session_id)

    response_text = _extract_text(trace["response"])
    response_findings = detection.scan_response(response_text)

    blocked = False
    final_response = response_text
    if mode == "protected" and response_findings:
        blocked = True
        final_response = _BLOCKED_RESPONSE

    return {
        "user_query": user_query,
        "mode": mode,
        "retrieved_docs": retrieved,
        "detections": injection_alerts,
        "sensitive_data": sensitive_docs,
        "attack_detected": attack_detected,
        "response_sensitive_data": response_findings,
        "blocked": blocked,
        "final_response": final_response,
        "tool_calls": trace["tool_calls"],
    }