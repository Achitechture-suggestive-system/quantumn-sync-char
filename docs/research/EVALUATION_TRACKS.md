# P11 — Evaluation tracks and preregistered measurements

## Purpose and status

This registry separates algorithm correctness, requirements extraction, architecture review and operational quality. A passing test is not a semantic label or an architecture judgment. Current state is `PARTIAL`; none of the three tracks yields a cross-case generalization claim. Tutor semantic comparison remains `BLOCKED_EXTERNAL` until independent source-only labels and later human review exist.

## Track registry

| Track | Inputs and provenance | Baseline / comparison | Current evidence | Not established |
|---|---|---|---|---|
| A — PetClinic fixture case | Repository-prepared PetClinic requirements/scenarios and `PRECOMPUTED` responsibilities/WHAT_IF_POLICY constraints. No source-code input is required or evaluated. | Existing exhaustive partition result; where applicable, compare the same fixed input/constraints with a declared optimizer implementation. Any extraction comparison requires a separately locked source-only reference first. | Regression behavior: Bell(6)=203, ten zero-cost optima for the documented fixture configuration; H3/H4 conflict and recovery remain fixture behaviors. | No PetClinic expert labels, model-vs-reference score, real architecture review, production topology, or quality measurement. |
| B — Tutor Support unseen domain case | Six FRs, four workflow steps and two scenarios from the prepared original requirements-only case. Responsibility, relation and policy labels in tests are `P2_TEST_ONLY`; historical qwen v6 is unblinded and excluded. | Required future comparison: source-only independent annotations locked before a fresh `qwen3:4b` run; separately report deterministic baseline, raw LLM proposals, human-reviewed evidence, and downstream outputs. | Input/source schemas and test-only evidence-to-constraint-to-optimizer-to-interaction/QAME causal path are tested. P2 runner is versioned and gated. | No post-lock inference, independent annotations, adjudication, real review, before/after case, semantic metrics, or quality measurement. |
| C — Synthetic optimizer stress | Seeded generated constraint sets and prepared test-only algorithm fixtures; no domain semantics. | Independent product-label exhaustive oracle on four-role cases; exhaustive optimizer comparison; CP-SAT optimum and constraint checks; nine-role Bell(9) truncation fixture. | Twelve seeded four-role cases, one separate exhaustive comparison, 21,147 nine-role partitions, output cap behavior. The complete suite is deterministic regression evidence, not a runtime benchmark. | No empirical architecture validity, domain weight policy, 50-role scale benchmark, or generalization from synthetic structures. |

## Measures and gates

| Measure | Method once eligible | Current status |
|---|---|---|
| Responsibility extraction precision/recall/F1 | Two independent source-only annotations; predeclared granularity and match rubric; separate adjudication; one-to-many matching rules fixed before viewing proposals. | `NOT_MEASURED_NO_ADJUDICATED_REFERENCE` |
| Relation precision/recall/F1 | Fixed relation predicate/direction universe; compare only adjudicated annotations; retain UNKNOWN/NOT_ANNOTATED/SCOPED_ABSENT separately. | `NOT_MEASURED_NO_ADJUDICATED_REFERENCE` |
| Citation support | Exact ID/span resolution is reported as structural mapping. Entailment requires independent human adjudication and is reported separately. | Structural checks tested; semantic entailment `NOT_MEASURED` |
| Human agreement | Compare independent annotators before adjudication; choose and predeclare a statistic appropriate to label type and missing values. | `NOT_MEASURED_NO_TWO_ANNOTATORS` |
| Human effort | Record time per stage, review actions, corrections/rejections/deferments and protocol version prospectively. | `NOT_MEASURED_NO_REVIEW_LOG` |
| Partition agreement | Compare partitions to an independently reviewed architectural reference using predeclared partition-distance measures; report all co-optima and selected display policy. | `NOT_MEASURED_NO_REFERENCE_PARTITION` |
| Optimizer correctness | Small exhaustive oracle agreement, hard-feasibility, transitivity, multiple optima, deterministic settings, infeasibility explanation and sensitivity under declared synthetic weights. | Algorithm tests pass; no domain validation |
| Runtime / robustness | Fixed machine/software/input versions, repetitions, workload sizes and adversarial input classes; separate solve proof time from optimum enumeration. | Solver settings recorded; broad runtime distribution and scale benchmark not run |
| Quality measurement | Runnable target, environment, method, repeat protocol and raw observation; scenario target is not an observation. | `NOT_MEASURED_NO_RUNNABLE_TARGET` |

No metric may be estimated from LLM self-labels, fixtures, source citation matches alone, or the optimizer objective. Baselines and ablations listed here are configurations for future experiments, not completed runs or numeric results.

## Baseline and ablation configurations to freeze per run

1. `PRECOMPUTED_FIXTURE`: existing responsibility/evidence inputs; used only for regression behavior.
2. `LLM_PROPOSALS_ONLY`: raw local proposal bundle with no review promotion; downstream constraints must remain absent for unsupported proposals.
3. `VALIDATED_EVIDENCE_ONLY`: exact citation/schema gates with unsupported and ambiguous rows retained as abstentions.
4. `HUMAN_REVIEWED`: reviewer-approved/corrected evidence and explicit architecture implication; only documented policy rules may emit constraints.
5. `POLICY_ABLATION`: same accepted evidence with policy evaluation bypassed or one entry removed; record as a software ablation, not evidence of domain truth.
6. `OPTIMIZER_ABLATION`: same frozen constraints through exhaustive oracle versus CP-SAT where small-input comparison is possible; compare optimum set, objective and feasibility, not architectural quality.

Each actual run must freeze case/source hash, model tag/digest, prompt/schema versions, code SHA, dependency versions, reviewer protocol version, policy catalog version, solver seed/limit/candidate cap, timestamps, and output checksums. Existing P2 CLI records a bounded proposal-run manifest; a complete integrated multi-stage bundle still needs separate validation.

## Provenance and rights

- PetClinic results described here are `PREPARED_FIXTURE` outputs, not source-code-analysis results.
- Tutor requirements and workflows are a prepared original case. The repository does not record third-party licensing or independent authorship certification; do not present the case as an external production dataset.
- Synthetic optimizer inputs are `P2_TEST_ONLY` or algorithm-test fixtures.
- A live LLM output must be labeled `LOCAL_OLLAMA_PROPOSAL` only after the local model is actually invoked under a valid post-lock protocol. No such post-lock inference is recorded now.
- Human decisions remain `HUMAN_DECISION` only when the reviewer supplies them; an implementation-created example is never an expert label.
