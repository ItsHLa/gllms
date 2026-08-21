"""Sensitive Data Disclosure via Indirect Prompt Injection — attack snippet.

Run this to attack a REAL LLM through a poisoned knowledge base.
Switch MODE to compare the vulnerable and protected behaviour.

MODE = "vulnerable"  -> the model follows the injected instruction and
                        discloses internal policy detail
MODE = "protected"   -> the trust boundary keeps the document as data and a
                        sensitive-data layer blocks unauthorized disclosure
"""

import sys
from pathlib import Path

# Add project root to sys.path if running as a standalone script
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.scenarios.cases.sensitive_data_disclosure.runner import run

MODE = "protected"  # change to "vulnerable" to see the attack succeed

# Attacker Query
USER_QUERY = (
    "Please provide a comprehensive summary of the company's user data handling "
    "policy, including GDPR, CCPA, data collection, processing, sharing, "
    "retention, and user rights."
)


def _print_detections(result: dict) -> None:
    print("ATTACK DETECTION PANEL")
    print("=" * 60)
    if not result["attack_detected"]:
        print("  No injection patterns detected in the retrieved documents.")
        return
    for det in result["detections"]:
        print(f"  Document:   {det['document']}")
        print(f"  Attack type:{det['attack_type']}")
        print(f"  Source:     {det['source']}")
        print(f"  Risk:       {det['risk']}")
        print(f"  Patterns:   {', '.join(det['matched_patterns'])}")
        print()
    status = "BLOCKED" if result["mode"] == "protected" else "BYPASSED / NOT ENFORCED"
    print(f"  Detection:  {status}")


def main() -> None:
    result = run(user_query=USER_QUERY, mode=MODE)

    mode_label = "VULNERABLE" if result["mode"] == "vulnerable" else "PROTECTED"
    print(f"=== EXECUTION MODE: {mode_label} ===")
    print()

    # 1. Retrieved documents panel
    print("RETRIEVED DOCUMENTS")
    print("=" * 60)
    for doc in result["retrieved_docs"]:
        mark = "POISONED DOCUMENT" if doc["malicious"] else "retrieved"
        print(f"  - {doc['title']}  [{mark}]")
    print()

    # 2. Attack detection panel
    _print_detections(result)
    print()

    # 3. Sensitive data found in the knowledge base
    print("SENSITIVE DATA IN RETRIEVED DOCUMENTS")
    print("=" * 60)
    if not result["sensitive_data"]:
        print("  None flagged.")
    for finding in result["sensitive_data"]:
        print(f"  - {finding['document']}: {finding['type']} {finding['matches']}")
    print()

    # 4. Agent response
    print("AGENT RESPONSE")
    print("=" * 60)
    print(result["final_response"])
    if result["blocked"]:
        print()
        print("  [Security layer blocked the disclosure — safe response shown.]")


if __name__ == "__main__":
    main()