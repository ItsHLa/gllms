# GLLMS — LLM Attack Lab

An interactive education site for the **OWASP Top 10 risks of LLM applications**.
Each scenario pairs a written article with a runnable Python script: read the
theory, hit **Run**, and watch a real LLM get attacked live — then switch to the
hardened mode and watch the same attack get mitigated.

Built for security learners who want more than static blog posts.

## Scenarios

| Scenario | OWASP Category | Difficulty |
|---|---|---|
| Indirect Prompt Injection in RAG | LLM01: Prompt Injection | Advanced |
| Sensitive Data Disclosure via Indirect Prompt Injection | LLM01: Prompt Injection | Advanced |
| RAG Poisoning: Successful Indirect Prompt Injection | LLM01: Prompt Injection | Advanced |
| Direct Prompt Injection — Prompt Leakage | LLM01: Prompt Injection | Advanced |
| SQL Injection via Model Output | Output-Level Attack | Advanced |

Every scenario supports multiple modes:

- `vulnerable` — no defenses; observe the attack succeed against a real model
- `protected` — injection detection, trust boundaries, DLP/validation layers block it
- `normal` — a well-behaved baseline assistant (some scenarios)

## Tech stack

- **Backend:** FastAPI + pydantic-settings; scenario code runs in isolated subprocesses with timeouts
- **Frontend:** Vue 3 via CDN (no build step), served directly by FastAPI
- **AI:** LangChain + Google Gemini (`langchain-google-genai`), Pinecone vector store, Hugging Face embeddings, LangGraph

## Project structure

```
backend/
├── app.py                    # FastAPI app factory + static serving
├── config.py                 # settings via pydantic-settings
├── schemas/scenario.py       # Pydantic request/response models
├── routers/
│   ├── scenarios.py          # GET /api/scenarios, GET /api/scenarios/{id}
│   └── run.py                # POST /api/run/{id}
├── services/executor.py      # runs scripts in an isolated subprocess
└── scenarios/
    ├── metadata.py           # scenario registry (easy to edit)
    └── cases/<id>/           # each attack's runner, prompts, article
frontend/
├── index.html                # single-page UI
└── static/
    ├── styles/main.css
    └── scripts/{api.js, app.js}
src/                          # shared agent/RAG components (LLM, vector store)
```

## License

All rights reserved.
