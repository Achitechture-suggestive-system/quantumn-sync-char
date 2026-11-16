# P8 — Interaction decision table and contract

## Contract schema

Generated interaction edges use `EQCR-INTERACTION-CONTRACT@1.0.0`. The fields preserve operation, data dependency, request/response fields, versioning, consistency, latency, failure, retry, timeout, idempotency, source references and unresolved decisions. Missing values remain `UNKNOWN`. The generated case contract also carries `decision_table_id/version`, `selected_mode`, review state and provenance.

The current pipeline emits `selected_mode=UNDECIDED`, `selection_status=UNDECIDED`, `decision_basis_status=INSUFFICIENT_EVIDENCE`, with deterministic provenance. It creates cited SYNC and ASYNC pattern hypotheses, but does not select either and does not treat them as operational contracts. The Streamlit review flow does not yet offer an interaction-contract approval editor.

## Versioned table `EQCR-SYNC-ASYNC-DECISION@1.0.0`

The table is an `ARCHITECTURAL_POLICY` with status `POLICY_DEFINED_NOT_EMPIRICALLY_VALIDATED`; it records the human-review gate, not an empirical Sync/Async classifier.

| Candidate | Minimum evidence before an approved choice | Otherwise |
|---|---|---|
| `SYNC` | A human-reviewed source-backed decision explicitly states that the initiating request must wait for the linked activity to complete. Contract operation, fields, versioning, consistency, latency, failure, retry, timeout and idempotency are specified and reviewed. | `UNDECIDED` |
| `ASYNC` | A human-reviewed source-backed decision explicitly permits the initiating request to return before the linked activity completes. Completion notification/delivery semantics and failure, retry, timeout and idempotency are specified and reviewed. | `UNDECIDED` |
| `UNDECIDED` | Mode evidence is missing, ambiguous, contradictory, not human-reviewed, or expresses only business ordering. | Preserve unknown fields and reasons. |

The schema validator permits `SYNC` or `ASYNC` only with a nonempty reviewer ID, timezone-aware review timestamp, source references, a rationale, an explicit mode signal, a complete contract, and no contradictory signal or unresolved decision. This is a data validity gate, not identity verification or semantic validation. No accepted interaction decision exists in the current Tutor case.

`BUSINESS_PRECEDES`, scenario adjacency, a notification scenario, or two responsibilities in separate quanta does not alone imply co-location, Sync, Async, or deployment. Those are separate architectural decisions. Evidence can support the reason for a choice; a human still has to approve it.

## Provenance and limits

Scenario and requirement SourceRefs attached to a generated edge are deterministic traces from the prepared inputs. The option patterns and decision table are deterministic policy artifacts, not LLM output or source facts. Current outputs remain `INSUFFICIENT_EVIDENCE` and `REVIEW_REQUIRED`. The schema has no runtime protocol validation, message broker, retry implementation, or service contract verification.
