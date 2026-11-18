# Repository capability audit — 2026-11-17

## Latest recheck — 2026-11-19

- Latest code milestone: `9c7c7337fd9e94b034dd0230ab1bd667282e39af`, pushed to the feature branch and verified by [CI run 44416779052](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44416779052). Local suite: 126 tests; compileall and diff check pass.
- P2 structural responsibility coverage now counts known FR IDs independently from citation resolution, preventing citation errors from being misreported as missing FR mappings. This still does not evaluate responsibility meaning.

- Latest code milestone: `376e424f3ffcb3a0b9161d256230696b230d4ae3`, pushed to the feature branch and verified by [CI run 44415600744](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44415600744). Local suite: 125 tests; compileall and diff check pass.
- Exhaustive partitioning through eight responsibilities now emits a deterministic deletion-minimal hard-constraint core when transitive constraints make every partition infeasible; the scope does not claim minimum cardinality or architectural validity.

- Prior evidence-audit milestone: `a334fac8b4193c469ed0a1499a1383db4164bdf1`, pushed to the feature branch and verified by [CI run 44414391706](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44414391706). Local suite: 124 tests; compileall and diff check pass.
- `eqcr/evidence_audit.py` reports exact duplicate claim/citation rows, direct PRESENT/SCOPED_ABSENT conflicts, and known/UNKNOWN mixtures. These rows abstain from experimental policy-derived constraints. This is structural screening only; semantics, entailment and context/time differences remain unverified.

- Feature code milestone `931dea62472ea459eacd33b1fbe6196eb4e619ce` is pushed to `feat/p1-semantic-validation`; remote feature ref matches. [CI run 44410991542](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44410991542) passed. Local full suite passed 121 tests; `compileall` passed.
- Remote `main` remains `5ece0157bf2372fb879f694cee9f5f0846fcbe1a`; P0 tag ancestry remains unchanged.
- P2 now has a five-file source-only reviewer package, pinned manifest/source hashes, a v3 lock validator and a pre-lock Tutor UI that renders only the source projection. The full raw Tutor case is no longer rendered before a valid lock.
- No reviewer-supplied lock or P2 run bundle exists. `qwen3:4b` is installed locally but has not been invoked for this experiment. Actual inference/review/revision/semantic evaluation remain blocked externally.
- Existing ignored `runs/` and snapshots were left untouched. Test-generated annotation locks carry test provenance and are not study data.

## Snapshot inspected

- Checkout: `feat/p1-semantic-validation`, clean at `dbe4a5f417535d11aab9696ff60e593be19b6e1a` during this recheck.
- Remote feature ref matched that SHA. Remote `main` was `5ece0157bf2372fb879f694cee9f5f0846fcbe1a`; this work has not modified `main`.
- Tag `p0-demo-2026-11-14` resolves to P0 commit `3d517b1a39158e539239dc73d594bc0938649feb` and is contained in both local branches.
- The latest documentation recheck commit has [CI run 44005282683](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44005282683) completed successfully. A fresh local run on this checkout passed 114 tests and `compileall`.
- The current P2 experiment remains `P2_BLOCKED_INDEPENDENT_ANNOTATION`: no verified source-only lock or `runs/p2-experiments/` output exists. `ollama list` shows `qwen3:4b` installed, but no inference was called during this recheck.
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
| P2 — unseen case experiment | `eqcr/tutor_support.py`, `eqcr/p2_protocol.py`, `eqcr/p2_reviewer_package.py`, `eqcr/p2_review.py`, P2 app/CLI and tests | Package/lock/software gates `IMPLEMENTED_VERIFIED`; case experiment `BLOCKED_EXTERNAL` | Five-file allowlisted source-only package, per-file/source hashes, manifest-bound v3 lock, read-only validator and pre-lock UI leak test are covered. No reviewer-supplied lock, post-lock inference, real review decisions or before/after case run. Historical v6 is unblinded exploratory only; identity/exposure remain self-attested. |
| P3 — requirements/source intake | `RawRequirements`, `SourceRef`, `eqcr/project_io.py`, JSON upload, Ollama prompt, artifact-bundle input hashes | `PARTIAL` | Tutor P2 now has a versioned source-only package manifest. Generic intake still has no document/BPMN parser or general source-package registry; source rights/authenticity remain unverified because hashes identify bytes only. |
| P4 — activity → operation → responsibility | `Responsibility`, `LLMProposal`, `apply_tutor_human_review`, `evaluate_p2_structure`, source/workflow mappings | `PARTIAL` | Fields and 0..N human disposition path exist; structural FR-ID coverage is separated from citations. No validated activity decomposition rubric or independent semantic evaluation labels; model-generated text remains a proposal. |
| P5 — evidence graph | `EvidenceRecord`, `RelationAnnotation`, `eqcr/evidence_audit.py`, `eqcr/p2_protocol.py`, `eqcr/p2_review.py`, traceability graph | `PARTIAL` | Typed `PRESENT` / `SCOPED_ABSENT` / `UNKNOWN`, provenance, citations, endpoint checks, structural graph, exact duplicate reporting and direct status-conflict abstention exist. No expert semantic validation, context/time-aware contradiction adjudication, or independent relation labels. |
| P6 — evidence interpretation → architecture decision → constraint | `EvidenceConstraintPolicyCatalog`, Tutor experimental rules, `_derive_evidence_constraints` | `PARTIAL` | Versioned case-rule catalog and per-evidence application/abstention traces are implemented. Entries remain internal experimental policies, not independently reviewed tactics; no source-reviewed general tactic catalog exists. |
| P7 — candidate partitioning | `_partitions`, `_optimize`, `eqcr/cpsat_optimizer.py`, `tests/test_partition_oracle.py`, `tests/test_cpsat_optimizer.py` | Bounded algorithm mechanics `IMPLEMENTED_VERIFIED`; scale performance `IMPLEMENTED_UNVERIFIED` | Exhaustive set partitions preserve all feasible and co-optimal candidates up to eight responsibilities and produce a tested deletion-minimal hard core for transitive infeasibility. CP-SAT dispatch handles 9–50 and reports a capped subset of proven optima only; its transitive explanation is a must-link path plus cannot-link. Neither explanation proves architectural validity or minimum core cardinality globally. The solver was oracle-checked on seeded four-role cases and a nine-role stress fixture; no runtime benchmark at 50 or domain-validated weights. |
| P8 — quanta and interactions | `_build_quanta`, `_build_interactions`, `_build_architecture_graph`, `InteractionContract`, `eqcr.drawio_export`, Human Review contract editor | Graph/export/schema/review path `IMPLEMENTED_VERIFIED`; actual case decision `BLOCKED_EXTERNAL` | Versioned graph includes integration; deterministic Draw.io download, Sync/Async decision table, exact-span gated UI editor, revision log and downstream recomputation are tested. Tutor remains UNDECIDED; no real interaction review exists; deployment/ownership are unknown. Changing a contract does not create optimizer constraints, and tests use `P2_TEST_ONLY` decisions. |
| P9 — quality scenario allocation | `Scenario`, `_build_quality`, QAME panel, traceability | Six-part trace `IMPLEMENTED_VERIFIED`; ISO mapping `PARTIAL` | Six scenario parts have per-field completeness and source refs. Tutor leaves four unknown. Raw characteristic text is preserved but there are no reviewed ISO characteristic IDs; measurement remains not measured. |
| P10 — quality measurement | `measurement_status`, `measurement_method`, `measurement=None` | `MISSING` for measurement adapters; `BLOCKED_EXTERNAL` for live measurement | The implementation correctly does not infer a pass from a target. No representative running system or calibrated measurement adapter is present. |
| P11 — research evaluation | Regression suite, P0/P1 reports, Tutor protocol, synthetic fixture, `docs/research/EVALUATION_TRACKS.md` | Protocol `IMPLEMENTED`; evaluation `PARTIAL` / `BLOCKED_EXTERNAL` | Three tracks, future baselines/ablations and measure gates are documented. No independent adjudicated labels, case-rights review, real architecture evaluation, 50-role runtime study, reviewer-effort data, or empirical quality results. |

## Requested deliverables and interface

| Deliverable | Current state | Status |
|---|---|---|
| Architecture graph JSON | Versioned graph under `quanta.architecture_graph`; required layers include Integration. Unsupported layers remain explicitly UNKNOWN policy placeholders. | Graph schema `IMPLEMENTED_VERIFIED`; architectural truth `PARTIAL` |
| Editable Draw.io diagram | Deterministic mxfile XML exporter and Streamlit download; stable cell IDs, unknown styling and endpoint validation are tested. GUI round-trip is not tested. | Export `IMPLEMENTED_VERIFIED`; architecture `PARTIAL` |
| Interaction contracts | Version 1.0.0 contract/decision table plus Human Review JSON editor, exact-span validation, audit decision, recomputation and snapshot. Test-only decisions pass; no actual Tutor decision. | Review path `IMPLEMENTED_VERIFIED`; case semantics `BLOCKED_EXTERNAL` |
| Quantum quality profiles | Six-part scenario fields, source/fixture provenance, mapping state and separate measurement status; empirical measurement remains absent. | Allocation `IMPLEMENTED_VERIFIED`; ISO mapping/measurement `PARTIAL` |
| Reproducibility bundle | App ZIP contains versioned manifest, canonical input and reviewer-decision hashes, code/runtime/dependency/solver metadata, provenance summary, and per-member checksums; validator checks hash coverage and JSON structure. P2 model-proposal bundle remains separate; see [bundle protocol](REPRODUCIBILITY_BUNDLE.md). | Bundle integrity/schema `IMPLEMENTED_VERIFIED`; scientific rerun `PARTIAL` |
| Evaluation metrics | No independent semantic metrics are currently reported. | `BLOCKED_EXTERNAL` for label-based metrics |

## Dependencies and evidence boundary

`requirements.txt` pins OR-Tools 9.15.6755 for the CP-SAT backend. The optimizer remains classical: exhaustive Python enumeration is used through eight roles, and CP-SAT is automatically dispatched for 9–50. The CP-SAT path reports only proven optimum candidates, capped by default at 200, and does not count all feasible candidates. NetworkX is used for graph work. Tests use prepared data and do not require an Ollama daemon. The app contains an Ollama call path but the post-blind Tutor call has not occurred.

The user supplied Tutor case is a prepared case, not a licensed production corpus. A new source-only annotation must come from a reviewer who has not seen model proposals for this case. Two independent annotations plus a separately recorded adjudication are required before calling the set gold or computing semantic agreement/accuracy metrics. A runnable, representative target is needed before measured quality outputs are possible.

## Standards and research references inspected

- ISO states that ISO/IEC 25010:2023 Product quality model has nine characteristics and supplies a reference for specifying, measuring, and evaluating product quality: [official ISO page](https://www.iso.org/standard/78176.html).
- CMU/SEI describes an architectural tactic as a design decision for a quality-attribute response, grounded in a quality-attribute analysis model: [SEI technical report summary](https://www.sei.cmu.edu/library/illuminating-the-fundamental-contributors-to-software-architecture-quality/).
- CMU/SEI’s Attribute-Driven Design collection ties tactic/pattern choices to quality-attribute scenarios and functional requirements: [SEI ADD collection](https://www.sei.cmu.edu/library/attribute-driven-design-method-collection/).

These references inform the gap assessment; no standard or tactic has been silently added to the application as a human-approved architectural decision.
