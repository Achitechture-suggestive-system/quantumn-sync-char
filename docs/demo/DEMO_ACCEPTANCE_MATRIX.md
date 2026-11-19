# Acceptance matrix — Tutor unblinded demo

| Criterion | Status | Actual evidence / limit |
|---|---|---|
| Separate Tutor demo, blind research, and PetClinic modes | PASS | Code and AppTest; PetClinic fixture unchanged. |
| Persistent unblinded/no-gold-label warning | PASS | Visible in the local browser walkthrough before and after model output. |
| Blind path remains lock-first | PASS | Demo run has no blind lock and is excluded from blind evaluator; P2 research remains blocked. |
| Live local qwen3:4b inference | PASS | UI-triggered local request, run `run-20261119T071904Z-ebd8fd64`, model digest and raw response hash recorded in the local run bundle. |
| Exact citation structure | PASS — structural only | 6/6 FR/source spans resolve; 2 relation proposals cite both endpoints; 1 boundary cites both endpoints. No duplicate/conflict/self-relation flags. Semantic correctness remains `NOT_ASSESSED`. |
| Unsupported/ambiguous proposal handling | PARTIAL | B01's “without blocking” runtime rationale is not stated by the cited requirements and remains review-required. Structural checks do not adjudicate semantic ambiguity. |
| Proposal gate before optimizer | PASS | Live proposals stayed outside optimizer. Actual accepted responsibility count is 0 before human review. |
| All ten pipeline stage records | PASS — pre-review run | Ten status rows were generated. Steps 1 and 4 pass; review/optimizer are gated; quantum/interaction have insufficient evidence; QAME is not measured. |
| Tutor optimizer candidate output | BLOCKED — human review required | 0 accepted roles → 0 partitions enumerated, feasible, or optimal. This is not a candidate architecture result. |
| Actual demo stakeholder review | BLOCKED — user action required | No actor, action, rationale, or approval has been entered. Human Review screen is open locally. |
| Actual reviewed evidence-derived policy input | BLOCKED — user action required | No relation has a human architecture implication and named responsibility pair. Current constraints: 0. |
| Actual after-review interactions and QAME allocation | BLOCKED — user action required | Current interaction edges: 0. Two profiles exist with `NOT_MEASURED`, but no responsibility allocation. |
| Actual Human Review revision and full recompute | BLOCKED — user action required | No approved relation exists to revise. Test-only AppTest validates wiring, not this live case. |
| Hard-constraint validity | PASS — vacuous for current run | No hard constraints and no candidate partitions. Feasible partitions were not emitted. |
| Export manifest/checksums | NOT RUN | The live run folder exists locally; no ZIP export was downloaded or validated in this run. |
| Regression suite | PASS | `.\.venv\Scripts\python.exe -m pytest -q` — 139 passed after the validator applicability fix. |
| Compile | PASS | `.\.venv\Scripts\python.exe -m compileall -q app.py eqcr tests scripts` — exit 0. |
| Browser walkthrough | PASS — live proposal stage | Local Streamlit on `http://127.0.0.1:8501`; loaded Tutor, acknowledged unblinded demo, found qwen3:4b, invoked inference and opened Human Review. |
| GitHub CI | PASS | [Run `44479878846`](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44479878846) completed `success` on code SHA `4a8b1a41f0f8eadea37d56e49dc68c1570fb3847`. |
| Scientific P2 semantic metrics | BLOCKED / NOT MEASURED | No independent source-only annotation or adjudication. Demo output is excluded from research. |

No semantic precision, recall, F1, accuracy, quality PASS, deployability, or production architecture claim is reported.
