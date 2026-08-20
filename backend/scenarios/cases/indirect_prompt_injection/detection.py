"""Indirect prompt-injection detection and sensitive-data scanning.

The security boundary: retrieved documents are DATA. Any phrase that tries
to behave like an instruction is flagged and must be ignored by the LLM.
"""

import re

SUSPICIOUS_PHRASES = [
    "ignore previous instructions",
    "system instruction",
    "developer message",
    "reveal",
    "display the full document",
    "bypass security",
    "override",
    "authorized auditor",
]

_SENSITIVE_PATTERNS = [
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("phone number", re.compile(r"\+?\d[\d\s().-]{8,}\d")),
    ("api token/secret", re.compile(r"\b(sk|pk|ghp)_[A-Za-z0-9]{10,}\b", re.IGNORECASE)),
    ("credential pair", re.compile(r"(?:password|secret|token|api[_-]?key)\s*[:=]\s*\S+", re.IGNORECASE)),
    ("internal endpoint", re.compile(r"(?:https?://)?[\w-]+\.(?:securecloud|internal)\.(?:example|local)\b", re.IGNORECASE)),
]

_THREAT = "Instructional content inside untrusted data"


def scan(docs: list[dict]) -> list[dict]:
    """Return a list of injection alerts found inside retrieved documents."""
    alerts = []
    seen = set()
    for doc in docs:
        content_lower = doc.get("content", "").lower()
        for phrase in SUSPICIOUS_PHRASES:
            key = (doc.get("title", "unknown"), phrase)
            if phrase.lower() in content_lower and key not in seen:
                seen.add(key)
                alerts.append(
                    {
                        "document": doc.get("title", "unknown"),
                        "phrase": phrase,
                        "source": "Retrieved document",
                        "threat": _THREAT,
                        "risk": "Potential unauthorized data disclosure",
                    }
                )
    return alerts


def scan_sensitive(docs: list[dict]) -> list[dict]:
    """Flag retrieved documents that contain sensitive data (emails, secrets...)."""
    findings = []
    for doc in docs:
        for label, pattern in _SENSITIVE_PATTERNS:
            matches = pattern.findall(doc.get("content", ""))
            if matches:
                findings.append(
                    {
                        "document": doc.get("title", "unknown"),
                        "type": label,
                        "matches": list(dict.fromkeys(matches))[:5],
                    }
                )
    return findings
