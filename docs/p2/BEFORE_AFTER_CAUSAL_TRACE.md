# P2.1 — Causal trace từ review tới output

## Luồng dữ liệu được audit

```text
Tutor source bundle + package manifest
  → external source-only annotation lock
  → Ollama qwen3:4b proposal + raw response
  → deterministic schema/citation/duplicate/registry audit
  → human approve/correct/reject/defer
  → reviewed responsibilities + typed relation evidence
  → separate human architecture implication
  → versioned policy evaluation (APPLIED / NOT_APPLICABLE / ABSTAINED)
  → evidence-derived soft constraints
  → exhaustive classical partition optimizer (6-role case)
  → candidate Quanta, interaction hypotheses, QAME profiles, traceability
  → Human Review correction + recompute + versioned before/after snapshot
```

Ollama proposals alone do not enter the evidence-to-constraint path. `apply_tutor_human_review` requires explicit decisions, exact source IDs and compatible reviewed relation fields. `_derive_evidence_constraints` checks approved endpoints, evidence provenance, citations, separate architecture implication and catalog rules. `run_pipeline` then passes the base plus derived constraints into `_optimize`; downstream builders compute candidate quanta, interaction hypotheses, quality allocation and traceability. Human Review relation editing invalidates and recomputes downstream artifacts. Interaction-contract review is a separate path and does not create optimizer constraints.

See [INPUT_TO_QUANTUM_TRACE.md](INPUT_TO_QUANTUM_TRACE.md) for the field-level dependency table and [P2 validation report](P2_VALIDATION_REPORT.md) for the test-only examples.

## Provenance categories

| Output/edge | Provenance | Current actual Tutor status |
|---|---|---|
| FR/WF/scenario IDs, quotes, spans | `PREPARED_FIXTURE` / source requirement representation | Prepared and package-hash checked; not independently sourced/licensed |
| Responsibility and evidence candidate text | `LOCAL_OLLAMA_PROPOSAL` only after actual model call | No new post-lock output |
| Citation resolution, schema checks, policy rules, objective calculation | `DETERMINISTIC_TRANSFORMATION` | Code and tests cover bounded mechanics |
| Relation-to-constraint policy selection | `ARCHITECTURAL_POLICY` | Internal Tutor experiment catalog; not independently validated tactic |
| Relation review, implication, correction | `HUMAN_DECISION` only after actual reviewer input | None supplied |
| Candidate partition/quantum/interaction/QAME | Deterministic transformation of the exact accepted inputs | Only test-only examples; not actual case output |

## Before/after experiment status

No genuine before/after case experiment exists. Tests intentionally create `P2_TEST_ONLY` reviewed evidence to verify that a soft `MUST_LINK` can change objective/partition assignments and that mapped interactions recompute. The test proves a software dependency for that constructed input, not that a Tutor responsibility is correct or that a real reviewer correction has any particular effect.

Once an actual lock, inference and human decisions exist, record both run IDs and hashes, changed decision/evidence/policy/constraint, each feasible partition, selected display tie-break, interactions, QAME and traceability. If outputs do not change, report the actual dependency path and the reason; do not describe a no-op as causal impact.
