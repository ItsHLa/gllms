"""Live runner for the Adversarial Suffix scenario.

Real implementation: uses the same components as main.py (LLMFactory,
RAGVectorStore, Agent with InMemorySaver) to run the attack against a real
LLM in three modes — normal, vulnerable, and protected.

The malicious instruction is an adversarial suffix appended to a legitimate
query. The attack is only classified as SUCCESSFUL when the vulnerable LLM
actually follows the suffix instruction AND system information appears in
the final response.

Flow:
    user_query -> suffix detection -> prompt construction -> LLM agent
    -> response validation (leakage check) -> attack evaluation -> response
"""

from langgraph.checkpoint.memory import InMemorySaver

from backend.scenarios._rag_resilience import safe_retrieve
from backend.scenarios.cases.adversarial_suffix import detection, documents, ingest, prompts
from src.agent import Agent
from src.llm import LLMFactory
from src.vector_store import RAGVectorStore

MODEL_NAME = "gemini-3.1-flash-lite-preview"
MODEL_PROVIDER = "genai"
TOP_K = 5

_MODES = ("normal", "vulnerable", "protected")

_KNOWN_TITLES = {d.metadata["title"] for d in documents.build_documents()}

_BLOCKED_RESPONSE = (
    "I cannot comply with that request. I am designed to answer questions about "
    "our product pricing plans only. If you have a legitimate question about our "
    "products, please ask and I will be happy to help."
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


def run(user_query: str | None = None, mode: str = "protected", session_id: str = "s6") -> dict:
    user_query = (user_query or "").strip() or documents.DEFAULT_USER_QUERY
    mode = mode if mode in _MODES else "protected"

    vectorstore = _get_vectorstore()
    ingest.ensure_ingested(vectorstore)

    # 1. Adversarial suffix detection on user input.
    analysis = detection.scan_user_input(user_query)
    suffix_detected = analysis["detected"]

    # 2. Retrieve documents (for context, not the attack vector).
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
    evaluation = detection.evaluate_attack(mode, suffix_detected, llm_followed, disclosed)

    return {
        "user_query": user_query,
        "mode": mode,
        "analysis": analysis,
        "matched_patterns": analysis["matched_patterns"],
        "retrieved_docs": retrieved,
        "suffix_detected": suffix_detected,
        "response_findings": final_findings,
        "llm_followed": llm_followed,
        "system_prompt_disclosed": disclosed,
        "attack_successful": evaluation["attack_successful"],
        "result_status": evaluation["result_status"],
        "blocked": blocked,
        "final_response": final_response,
        "tool_calls": trace["tool_calls"],
    }
