"""Live runner for the Indirect Prompt Injection scenario.

Real implementation: it uses the exact same components as main.py
(LLMFactory, RAGVectorStore, Agent with InMemorySaver) to demonstrate the
attack against a real LLM, then returns a structured result for the UI.

Flow:
    user_query -> embed -> vector db -> retrieve -> trust boundary
    -> prompt construction -> LLM agent -> security validation -> response
"""

from langgraph.checkpoint.memory import InMemorySaver

from backend.scenarios.cases.indirect_prompt_injection import detection, documents, ingest, prompts
from src.agent import Agent
from src.llm import LLMFactory
from src.vector_store import RAGVectorStore

MODEL_NAME = "gemini-3.1-flash-lite-preview"
MODEL_PROVIDER = "genai"
TOP_K = 5

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
    retriever = vectorstore.vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    docs = retriever.invoke(user_query)
    seen = set()
    unique = []
    for d in docs:
        title = d.metadata.get("title") or "Untitled"
        if title in seen:
            continue
        seen.add(title)
        unique.append(d)
    return [
        {
            "title": d.metadata.get("title", "Untitled"),
            "category": d.metadata.get("category", "unknown"),
            "content": d.page_content,
            "malicious": False,
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


def run(user_query: str | None = None, mode: str = "protected", session_id: str = "s1") -> dict:
    user_query = (user_query or "").strip() or documents.DEFAULT_USER_QUERY
    mode = mode if mode in ("vulnerable", "protected") else "protected"

    vectorstore = _get_vectorstore()
    ingest.ensure_ingested(vectorstore)

    retrieved = _retrieve(vectorstore, user_query)

    injection_alerts = detection.scan(retrieved)
    sensitive = detection.scan_sensitive(retrieved)
    attack_detected = len(injection_alerts) > 0

    for doc in retrieved:
        if any(a["document"] == doc["title"] for a in injection_alerts):
            doc["malicious"] = True

    system_prompt, user_prompt = prompts.build_prompts(user_query, retrieved, mode)

    agent = _build_agent(system_prompt)
    trace = agent.call_with_trace(user_prompt, session_id)

    return {
        "user_query": user_query,
        "mode": mode,
        "retrieved_docs": retrieved,
        "detections": injection_alerts,
        "sensitive_data": sensitive,
        "attack_detected": attack_detected,
        "final_response": _extract_text(trace["response"]),
        "tool_calls": trace["tool_calls"],
    }
