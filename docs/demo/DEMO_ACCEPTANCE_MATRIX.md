# Acceptance matrix — Tutor unblinded demo

| Criterion | Status | Evidence / limit |
|---|---|---|
| Separate Tutor demo, blind research and PetClinic modes | PASS — code/test | AppTest checks demo acknowledgement; PetClinic offline regression remains covered. |
| Persistent `EXPLORATORY_UNBLINDED_DEMO` warning | PASS — code/test | Warning appears at app top and mode/review screens. |
| No blind lock bypass | PASS — code/test | Default Tutor proposal path requires verified lock; demo path rejects carried lock; blind evaluator rejects demo provenance. |
| Real local qwen3:4b invocation path | PARTIAL — not live in current milestone | Unit test mocks request and verifies request path; actual invocation requires demo acknowledgement and Ollama in UI. |
| Structural citation/duplicate/ambiguity audit | PASS — implementation; live output pending | Exact source mapping and flags exist; no new live response audited yet. |
| Proposals excluded until a real review action | PASS — AppTest | Pending run has zero responsibility candidates; explicit test fixture review enables data flow. |
| Reviewed evidence/policy drives generic optimizer | PASS — test-only causal path | Test-only review creates a soft evidence-derived constraint and generic Bell(6) enumerator result; not Tutor semantic evidence. |
| Interaction and QAME generation | PASS — deterministic pipeline tests | Candidate hypotheses/profiles preserve unresolved/unmeasured state; live reviewed case pending. |
| Actual stakeholder review | BLOCKED — no user action yet | No actor/rationale/approval is fabricated. |
| Actual Human Review revision + recomputation | PASS — AppTest wiring; live revision pending | Test-only revision changes evidence pair and selected groups, and records test actor/hash/snapshot data. |
| Hard constraints satisfied | PASS — regression coverage | Unit tests check hard rules on every feasible candidate; Tutor policy catalog currently creates soft constraints only. |
| Export mode/provenance/checksum | PASS — unit tests | Manifest contains execution mode and research eligibility; no live case export yet. |
| Regression tests | PASS — local | `.\.venv\Scripts\python.exe -m pytest -q`: 138 passed; `compileall -q app.py eqcr tests scripts` and `git diff --check` passed. |
| Browser walkthrough against live model | NOT RUN | Do not infer from AppTest or local Ollama availability. |
| GitHub CI | PASS | Run [44476894324](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44476894324) completed `success` on implementation commit `f981e55125ddee3f3c10a34d4adb8c4319b3fa04`. |
| Scientific P2 metrics | BLOCKED / NOT MEASURED | No eligible independent annotation lock/adjudication/gold labels. |

No semantic precision/recall/F1 or quality PASS is reported by this matrix.
