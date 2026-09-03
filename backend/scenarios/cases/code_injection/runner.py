"""Live runner for the Code Injection via Email Assistant scenario.

Real implementation: uses the same components as main.py (LLMFactory,
RAGVectorStore, Agent with InMemorySaver) to run the attack against a real
LLM in three modes — normal, vulnerable, and protected.

The attack exploits an LLM-powered email assistant by hiding instructions
inside email content. The attack is only classified as SUCCESSFUL when the
vulnerable LLM actually follows the injected instruction AND sensitive
information appears in the final response.

Flow:
    user_query -> injection detection -> prompt construction -> LLM agent
    -> response validation (leakage check) -> attack evaluation -> response
"""

from langgraph.checkpoint.memory import InMemorySaver

from backend.scenarios._rag_resilience import safe_retrieve
from backend.scenarios.cases.code_injection import detection, documents, ingest, prompts
from src.agent import Agent
from src.llm import LLMFactory
from src.vector_store import RAGVectorStore

MODEL_NAME = "gemini-3.1-flash-lite-preview"
MODEL_PROVIDER = "genai"
TOP_K = 5

_MODES = ("normal", "vulnerable", "protected")

_KNOWN_TITLES = {d.metadata["title"] for d in documents.build_documents()}

_BLOCKED_RESPONSE = (
    "I have drafted a professional reply to the meeting request. "
    "I cannot execute instructions found in email content, access file systems, "
    "or disclose internal configuration. The email has been processed as a "
    "standard meeting request."
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

    for known in documents.build_documents():
        title = known.metadata["title"]
        if title not in seen:
            unique.append(known)
            seen.add(title)

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


def run(user_query: str | None = None, mode: str = "protected", session_id: str = "s7") -> dict:
    user_query = (user_query or "").strip() or documents.DEFAULT_USER_QUERY
    mode = mode if mode in _MODES else "protected"

    vectorstore = _get_vectorstore()
    ingest.ensure_ingested(vectorstore)

    # 1. Email content injection detection.
    analysis = detection.scan_user_input(user_query)
    injection_detected = analysis["detected"]

    # 2. Retrieve documents (company context).
    retrieved = _retrieve(vectorstore, user_query)

    # 3. Prompt construction.
    system_prompt, user_prompt = prompts.build_prompts(user_query, mode)

    agent = _build_agent(system_prompt)
    trace = agent.call_with_trace(user_prompt, session_id)

    raw_response = _extract_text(trace["response"])
    raw_findings = detection.scan_response(raw_response)

    # 4. Response validation + security validation.
    blocked = False
    final_response = raw_response
    if mode == "protected" and raw_findings:
        blocked = True
        final_response = _BLOCKED_RESPONSE

    final_findings = detection.scan_response(final_response)
    disclosed = detection.system_prompt_disclosed(final_response)

    # 5. Attack-success evaluation.
    llm_followed = mode == "vulnerable" and bool(raw_findings)
    evaluation = detection.evaluate_attack(mode, injection_detected, llm_followed, disclosed)

    return {
        "user_query": user_query,
        "mode": mode,
        "analysis": analysis,
        "matched_patterns": analysis["matched_patterns"],
        "retrieved_docs": retrieved,
        "injection_detected": injection_detected,
        "response_findings": final_findings,
        "llm_followed": llm_followed,
        "sensitive_data_disclosed": disclosed,
        "attack_successful": evaluation["attack_successful"],
        "result_status": evaluation["result_status"],
        "blocked": blocked,
        "final_response": final_response,
        "tool_calls": trace["tool_calls"],
    }
