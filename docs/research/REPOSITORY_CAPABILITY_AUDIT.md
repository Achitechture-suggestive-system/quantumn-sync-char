# Repository capability audit — 2026-11-16

## Snapshot inspected

- Checkout: `feat/p1-semantic-validation`, clean at `66534a54c12f3aa2a5aca4618806583e71dee19a` during audit.
- Remote feature ref matched that SHA. Remote `main` was `5ece0157bf2372fb879f694cee9f5f0846fcbe1a`; this work has not modified `main`.
- Tag `p0-demo-2026-11-14` resolves to P0 commit `3d517b1a39158e539239dc73d594bc0938649feb` and is contained in both local branches.
- Feature CI run `43841700612` verified implementation commit `1ec2c1b649901873a12cb43dba703bf7a723a411`; docs follow-up run `43842022641` verified `66534a54c12f3aa2a5aca4618806583e71dee19a`. Both passed regression tests and compilation.
- The current code suite recorded in `docs/p2/P2_VALIDATION_REPORT.md` is 63 tests. It does not call Ollama. Current P2 state remains `ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`.
- Local `runs/` contains prior ignored run and snapshot data. It was inspected only for existence and left untouched.

## Status meanings

- `IMPLEMENTED_VERIFIED`: code exists and a current automated check or recorded execution covers the stated bounded behavior.
- `IMPLEMENTED_UNVERIFIED`: code exists, but no adequate verification evidence was found for the claimed behavior.
- `PARTIAL`: some required behavior is present, with material gaps listed below.
- `MISSING`: no implementation was found in the inspected checkout.
- `BLOCKED_EXTERNAL`: completing or validating the capability requires an independent person, licensed/approved source, or runnable target outside this repository.

These statuses describe the software and evidence separately. Passing a schema/test does not establish semantic correctness.

## P0–P11 and pipeline capability map

| Research stage | Repository implementation | Status | Verified scope and remaining boundary |
|---|---|---|---|
| P0 — preserved local MVP | `app.py`, `eqcr/fixture.py`, `eqcr/pipeline.py`, `eqcr/review.py`, `eqcr/storage.py`; P0 tag and verification report | `IMPLEMENTED_VERIFIED` | Local Streamlit flow, fixture, enumerator, review/snapshot/export behavior are recorded. This is a demo baseline, not a production architecture validation. |
| P1 — structural/traceability validation | `eqcr/models.py`, `eqcr/traceability.py`, `tests/test_semantic_validation.py`, `tests/test_traceability.py`, `tests/test_partition_oracle.py` | `IMPLEMENTED_VERIFIED` | Strict schemas, source-span checks, negative tests, graph checks, and an independent exhaustive oracle for six responsibilities. No semantic gold labels or generalization claim. |
| P2 — unseen case experiment | `eqcr/tutor_support.py`, `eqcr/p2_protocol.py`, `eqcr/p2_review.py`, P2 app flow and `tests/test_p2_tutor_support.py` | `PARTIAL`; experiment `BLOCKED_EXTERNAL` | Protocol/hash gate and test-only causal wiring exist. No real post-lock inference, independent annotation, actual review decisions, or real before/after case run. Historical v6 is unblinded exploratory only. |
| P3 — requirements/source intake | `RawRequirements`, `SourceRef`, `eqcr/project_io.py`, JSON upload, Ollama prompt | `PARTIAL` | Structured JSON and exact source-span validation exist. No versioned document/BPMN parser, source-license record, source-package registry, or immutable run manifest. |
| P4 — activity → operation → responsibility | `Responsibility`, `LLMProposal`, `apply_tutor_human_review`, source/workflow mappings | `PARTIAL` | Fields and 0..N human disposition path exist. No validated activity decomposition rubric or independent evaluation labels; model-generated text remains a proposal. |
| P5 — evidence graph | `EvidenceRecord`, `RelationAnnotation`, `eqcr/p2_protocol.py`, `eqcr/p2_review.py`, traceability graph | `PARTIAL` | Typed `PRESENT` / `SCOPED_ABSENT` / `UNKNOWN`, provenance, citations, endpoint checks, and structural graph exist. No expert semantic validation, full duplicate/contradiction adjudication across arbitrary evidence, or independent relation labels. |
| P6 — evidence interpretation → architecture decision → constraint | `EvidenceConstraintPolicyCatalog`, Tutor experimental rules, `_derive_evidence_constraints` | `PARTIAL` | Versioned case-rule catalog and per-evidence application/abstention traces are implemented. Entries remain internal experimental policies, not independently reviewed tactics; no source-reviewed general tactic catalog exists. |
| P7 — candidate partitioning | `_partitions`, `_optimize`, `eqcr/cpsat_optimizer.py`, `tests/test_partition_oracle.py`, `tests/test_cpsat_optimizer.py` | Bounded algorithm mechanics `IMPLEMENTED_VERIFIED`; scale performance `IMPLEMENTED_UNVERIFIED` | Exhaustive set partitions preserve all feasible and co-optimal candidates up to eight responsibilities. CP-SAT dispatch handles 9–50 by code limit and reports a capped subset of proven optima only. The solver was oracle-checked on seeded four-role cases and a nine-role stress fixture; no runtime benchmark at 50 or domain-validated weights. |
| P8 — quanta and interactions | `_build_quanta`, `_build_interactions`, `_build_architecture_graph`, `InteractionContract`, `eqcr.drawio_export`, Streamlit candidate graph | Graph/export and schema `IMPLEMENTED_VERIFIED`; reviewed decisions `BLOCKED_EXTERNAL` | Versioned graph includes integration; deterministic Draw.io download and Sync/Async decision table are tested. Pipeline stays UNDECIDED; UI has no interaction-contract approval editor, deployment/ownership are unknown. |
| P9 — quality scenario allocation | `Scenario`, `_build_quality`, QAME panel, traceability | Six-part trace `IMPLEMENTED_VERIFIED`; ISO mapping `PARTIAL` | Six scenario parts have per-field completeness and source refs. Tutor leaves four unknown. Raw characteristic text is preserved but there are no reviewed ISO characteristic IDs; measurement remains not measured. |
| P10 — quality measurement | `measurement_status`, `measurement_method`, `measurement=None` | `MISSING` for measurement adapters; `BLOCKED_EXTERNAL` for live measurement | The implementation correctly does not infer a pass from a target. No representative running system or calibrated measurement adapter is present. |
| P11 — research evaluation | Regression suite, P0/P1 reports, Tutor protocol, synthetic fixture, `docs/research/EVALUATION_TRACKS.md` | Protocol `IMPLEMENTED`; evaluation `PARTIAL` / `BLOCKED_EXTERNAL` | Three tracks, future baselines/ablations and measure gates are documented. No independent adjudicated labels, case-rights review, real architecture evaluation, 50-role runtime study, reviewer-effort data, or empirical quality results. |

## Requested deliverables and interface

| Deliverable | Current state | Status |
|---|---|---|
| Architecture graph JSON | Versioned graph under `quanta.architecture_graph`; required layers include Integration. Unsupported layers remain explicitly UNKNOWN policy placeholders. | Graph schema `IMPLEMENTED_VERIFIED`; architectural truth `PARTIAL` |
| Editable Draw.io diagram | Deterministic mxfile XML exporter and Streamlit download; stable cell IDs, unknown styling and endpoint validation are tested. GUI round-trip is not tested. | Export `IMPLEMENTED_VERIFIED`; architecture `PARTIAL` |
| Interaction contracts | Version 1.0.0 contract and Sync/Async decision table; current mode stays UNDECIDED. No UI approval editor or actual accepted decision. | `PARTIAL` |
| Quantum quality profiles | Six-part scenario fields, source/fixture provenance, mapping state and separate measurement status; empirical measurement remains absent. | Allocation `IMPLEMENTED_VERIFIED`; ISO mapping/measurement `PARTIAL` |
| Reproducibility bundle | ZIP contains JSON artifacts and available snapshots. P2 model output has prompt/model/input metadata when real inference occurs. No full environment/code/source/result manifest is generated. | `PARTIAL` |
| Evaluation metrics | No independent semantic metrics are currently reported. | `BLOCKED_EXTERNAL` for label-based metrics |

## Dependencies and evidence boundary

`requirements.txt` pins OR-Tools 9.15.6755 for the CP-SAT backend. The optimizer remains classical: exhaustive Python enumeration is used through eight roles, and CP-SAT is automatically dispatched for 9–50. The CP-SAT path reports only proven optimum candidates, capped by default at 200, and does not count all feasible candidates. NetworkX is used for graph work. Tests use prepared data and do not require an Ollama daemon. The app contains an Ollama call path but the post-blind Tutor call has not occurred.

The user supplied Tutor case is a prepared case, not a licensed production corpus. A new source-only annotation must come from a reviewer who has not seen model proposals for this case. Two independent annotations plus a separately recorded adjudication are required before calling the set gold or computing semantic agreement/accuracy metrics. A runnable, representative target is needed before measured quality outputs are possible.

## Standards and research references inspected

- ISO states that ISO/IEC 25010:2023 Product quality model has nine characteristics and supplies a reference for specifying, measuring, and evaluating product quality: [official ISO page](https://www.iso.org/standard/78176.html).
- CMU/SEI describes an architectural tactic as a design decision for a quality-attribute response, grounded in a quality-attribute analysis model: [SEI technical report summary](https://www.sei.cmu.edu/library/illuminating-the-fundamental-contributors-to-software-architecture-quality/).
- CMU/SEI’s Attribute-Driven Design collection ties tactic/pattern choices to quality-attribute scenarios and functional requirements: [SEI ADD collection](https://www.sei.cmu.edu/library/attribute-driven-design-method-collection/).

These references inform the gap assessment; no standard or tactic has been silently added to the application as a human-approved architectural decision.
