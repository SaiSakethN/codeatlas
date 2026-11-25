# Verification report — November 25, 2026

## Observed results

| Check | Actual result |
| --- | --- |
| Original baseline | 42 pytest tests passed; Ruff passed |
| Final Python suite | 62 passed in 3.51 seconds |
| Final Ruff lint | Passed |
| Final Ruff format check | 61 files already formatted |
| Frontend ESLint | Passed, no warnings |
| Production Next.js build | Passed, including TypeScript and route generation |
| Production dependency audit | npm reported zero vulnerabilities |
| Production-mode browser suite | 4 passed in 16.8 seconds, local Chrome |
| CPU embedding integration | 384-dimensional vectors; 3 indexed fixture chunks; expected `retry_delay` symbol ranked first |

These are individual local observations, not performance guarantees. The final Python run followed the engine/API/security changes. Subsequent additions were documentation, the opt-in CPU verification script, browser tests, and CI configuration.

## Real browser flow

Ran the built frontend with `next start` and a production-mode FastAPI server, using disposable local test credentials without modifying private `.env` values. The checks verified:

1. Anonymous workspace requests fail and cross-origin login mutations fail.
2. The landing page renders on desktop and a 390 × 844 mobile viewport without horizontal overflow.
3. Public Requests import completes through the background job API; overview, React Flow architecture, onboarding, shallow-history impact messaging, source browsing, and mobile navigation work.
4. RAG and autonomous agent requests return answers with inspectable source evidence. Citations open source files and completed tool traces are displayed.

The Requests import reused its existing local clone and 1,077-chunk index. It is not a fresh-clone/index throughput benchmark. GitHub availability was checked through the import preflight. The controlled CPU fixture was indexed and queried with actual FastEmbed ONNX inference; no hosted chat was used for that fixture.

The live RAG response used full-width citation brackets, exposing a typography mismatch. Normalization now preserves the IDs while converting those brackets to the supported form. The regression test verifies that an unknown ID still fails. Identifier validation does not establish factual accuracy. No labeled factual-correctness or retrieval-quality benchmark was performed.

## Evidence and scope

- [Landing screenshot](screenshots/landing.png)
- [Workspace screenshot](screenshots/workspace.png)
- [Live investigation screenshot](screenshots/investigation.png)
- API/security tests: `tests/test_api.py`
- Static analysis tests: `tests/test_analysis.py`
- Browser tests: `frontend/tests/workspace.spec.ts`
- Reproducible CPU smoke script: `scripts/verify_cpu_embeddings.py`

Existing retrieval, provider composition, agent-tool execution, citation membership, and hosted rate-limit regressions remain in the passing suite. New checks cover URL validation, source traversal rejection, body limits, production authentication, busy-operation handling, background-job outcomes, repository admission size, and static relative-import analysis.

## Not yet verified

- Full production deployment and external deployment smoke tests: Render is not connected.
- Actual free-host memory capacity, cold-start duration, and restart behavior.
- Docker image execution on a production host.
- Rotation of the previously exposed Groq credential.
- Distributed throttling, durable jobs, or multi-user isolation; these are not implemented.

No paid hosting feature was enabled and no branch was merged into `main`.
