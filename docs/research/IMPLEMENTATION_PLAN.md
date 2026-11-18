# Research-grade implementation plan — 2026-11-17

## Automated UI regression — 2026-11-19

Test commit `7e3d1e836eab2b04ee667506a9d2a4a72296f8f8` is pushed on `feat/p1-semantic-validation`; [CI 44422385371](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44422385371) passed. The complete local suite passed **130 tests**; compileall and `git diff --check` passed.

The Streamlit `AppTest` exercises the PetClinic offline UI flow through all ten stages and asserts QAME graph allocations, expected partition counts and unmeasured statuses. It isolates storage writes from `runs/`. This closes the automated PetClinic UI regression gap; P2 Tutor remains blocked on independent source-only annotation and subsequent real inference/review.

## QAME traceability edge validation — 2026-11-19

Follow-up code commit `172856cfa718971aa83e0f09986e53ce11534e2b` is pushed on `feat/p1-semantic-validation`; [CI 44421428402](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44421428402) passed. The full local suite remains **129 passed**; compileall and `git diff --check` passed.

The allocation assertion now recomputes responsibility and quantum allocations from the scenario inputs and current assignment, then verifies those exact graph edges and both interaction quantum endpoints. A deliberately invalid endpoint fails traceability. These checks support structural lineage only; semantic meaning, taxonomy, and measured quality remain unresolved.

## QAME traceability chain — 2026-11-19

Code commit `c1e96767f38b6a04083789f630d5d7d9e07b4b25` is pushed on `feat/p1-semantic-validation`; [CI 44419855480](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44419855480) passed. Local full suite: 129 tests; compileall and `git diff --check` passed.

Traceability now represents requirement→scenario→responsibility→quantum→interaction and quality-profile→quantum/interaction→ISO mapping state→measurement state. New assertions check allocated IDs and actual graph edges. The implementation preserves unreviewed labels as `UNMAPPED`/`UNSPECIFIED` and values as `NOT_MEASURED`/`NOT_RECORDED`; it adds no ISO classification or measurement.

A deterministic Tutor prepared-fixture rerun produced identical artifact trees twice; the in-memory bundle validator returned `PASS` for 18 members. This is prepared fixture plus deterministic transformation in `P2_TEST_ONLY`, not model inference or human review. Tutor source-only lock, fresh Ollama proposal, review decisions and actual revision experiment remain blocked externally.

Manual Streamlit smoke loaded and ran the frozen PetClinic offline fixture, showed outputs on all four UI tabs, and reported 203 partitions/10 feasible/10 zero-cost candidates. Loading Tutor afterward showed only its source-only projection with offline run disabled and no P1/P6 proposal IDs. No review submission or model call was made. Local ignored run `runs/run-20261118T232503Z-357cfb32/` was left intact. This is a browser smoke of the existing app, not an automated E2E test for the P2 model/review experiment.

## P2 evaluator payload guards — 2026-11-19

Code commit `00be77f5486023d3ad88e1f602b20167d30c710c` is pushed on `feat/p1-semantic-validation` and verified by [CI 44417777751](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44417777751). Local validation: 128 tests, compileall, and diff check passed. The P2 structural evaluator now handles non-object rows and malformed identifier types with controlled errors. This validates input handling only; it does not add semantic accuracy metrics or unblock the actual Tutor experiment.

## P2 mapping/citation metric separation — 2026-11-19

Code commit `9c7c7337fd9e94b034dd0230ab1bd667282e39af` is pushed on `feat/p1-semantic-validation` and verified by [CI 44416779052](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44416779052). Local validation: 126 tests, compileall, and diff check passed. Structural responsibility mapping now counts known FR IDs regardless of citation validity, while citation resolution and errors remain separate. This does not assess semantic responsibility correctness; the actual P2 experiment remains blocked on an independent source-only annotation lock.

## Exhaustive hard-conflict explanation milestone — 2026-11-19

Code commit `376e424f3ffcb3a0b9161d256230696b230d4ae3` is pushed on `feat/p1-semantic-validation` and verified by [CI 44415600744](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44415600744). Local validation: 125 tests, compileall, and diff check passed. For exhaustive R1–R8 optimization, transitive infeasibility now reports a deterministic deletion-minimal set of hard constraint IDs, with a test confirming each listed rule is necessary and an irrelevant rule is excluded. The core is not guaranteed minimum-cardinality and does not justify the architecture decision.

## Deterministic evidence-claim audit milestone — 2026-11-19

Code commit `a334fac8b4193c469ed0a1499a1383db4164bdf1` is pushed on `feat/p1-semantic-validation` and verified by [CI 44414391706](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44414391706). Local validation: 124 tests, compileall, and diff check passed. Duplicate exact claim/citation rows and direct status-conflict or known/UNKNOWN groups are now recorded; their evidence IDs abstain from policy-derived constraints. This does not resolve semantic or context/time conflicts. The actual Tutor experiment remains blocked on an independent source-only annotation lock.

## P2.1 milestone recheck — 2026-11-19

The prior sections are the historical plan/status recorded at the 2026-11-17 checkpoint. Since then, feature commit `931dea62472ea459eacd33b1fbe6196eb4e619ce` added and pushed the source-only package, pinned lock validation and pre-lock source-only UI boundary; [CI 44410991542](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44410991542) passed, with 121 local tests and compileall passing. Remote `main` remains at the P0 baseline.

The package and validator are now code-complete within their tested scope. The actual P2 experiment remains `BLOCKED_EXTERNAL`: a qualified reviewer must provide a valid source-only lock before local qwen inference. No real human labels, post-lock proposals, case-level optimizer outputs or revision comparison were created. Work after the blocker clears must follow [`ACTUAL_EXPERIMENT_PROTOCOL.md`](../p2/ACTUAL_EXPERIMENT_PROTOCOL.md); do not report the test-only wiring as a case result.

This plan follows the repository audit. It preserves the existing P0 baseline and keeps semantic claims separate from implementation checks. Work proceeds in small commits on `feat/p1-semantic-validation`; no change to `main` is included.

## Current audit checkpoint

- Feature commit inspected: `dbe4a5f417535d11aab9696ff60e593be19b6e1a`; remote feature ref matched. Remote `main` remains `5ece0157bf2372fb879f694cee9f5f0846fcbe1a`, and the P0 tag remains an ancestor.
- Local verification on this checkpoint: 114 tests passed; `compileall` passed. GitHub Actions run [44005282683](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44005282683) passed.
- Ollama reports the local `qwen3:4b` tag installed. No source-only lock or P2 run bundle exists, and no new inference was made. The case experiment remains `P2_BLOCKED_INDEPENDENT_ANNOTATION`.
- The Human Review interaction-contract editor is implemented and tested; no real Tutor contract decision exists. These reviews do not directly alter optimizer constraints.

## Milestone A — P2 experiment reproducibility (implemented; CI verified; case experiment blocked externally)

1. **Infrastructure implemented:** `scripts/run_p2_experiment.py` accepts the prepared case and a verified source-only lock; checks protocol/source/timestamps/model/schema/prompt versions and clean Git state before local Ollama.
2. **Infrastructure implemented:** export raw proposal and structural-evaluation JSON, manifest with code/package/input/annotation/model/prompt/timestamp metadata, per-file hashes, and a ZIP under a unique ignored run directory. Existing run directories are never overwritten.
3. **Infrastructure implemented, metrics gated:** deterministic report counts exact citation resolution, FR proposal coverage/unresolved cases, relation statuses, duplicates and structural error types. Semantic relation/responsibility metrics remain unavailable until an independently prepared adjudication file and explicit match decisions exist.
4. **Verification:** 72 tests pass locally; commit `1fe23ed7886e02b02e44e5ebb850e1b1e6dd6628` is pushed; [CI run 43849233685](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43849233685) passed.
5. **Current state:** `P2_BLOCKED_INDEPENDENT_ANNOTATION`; no qualified, unexposed reviewer has supplied a lock. The CLI returns this blocker before model discovery or inference. Do not fabricate decisions.

## Milestone B — P4–P6 evidence and policy rules

1. Version the activity/responsibility/evidence schemas without changing historical input meanings.
2. **Implemented for Tutor as an experimental case catalog:** `EvidenceConstraintPolicyCatalog` binds catalog/entry versions, internal source-basis status, quality driver, evidence preconditions, assumptions, named output relation, and abstention conditions. Per-evidence rule evaluation records APPLIED/NOT_APPLICABLE/ABSTAINED and the derived constraint ID. The catalog is explicitly not independently validated and is not presented as a general tactic catalog.
3. Keep evidence observation, interpretation, architectural decision and optimizer constraint as separate records. Unregistered predicates and ambiguous evidence abstain.
4. **Test coverage:** catalog version/uniqueness/hard-rule rejection, explicit override bypass, and UNKNOWN-evidence abstention are covered; existing citation, reflexive, endpoint, and unsupported-promotion tests remain in place.
5. **Verification:** 78 full-suite tests pass; compileall and `git diff --check` pass. Commit `ab26975b3bf9b8f2f8635ac825211a2a7a972ff6` is pushed and [CI run 43882340244](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43882340244) passed.

Catalog entries must be reviewed and tied to a source before being treated as architectural tactics. The current P2 test catalog is internal and experimental. CMU/SEI defines tactics in relation to quality-attribute response and analysis models; generic co-location/separation heuristics must not be relabeled as validated tactics.

## Milestone C — P7 optimizer verification and scale

1. **Implemented:** [`PARTITION_OPTIMIZATION.md`](PARTITION_OPTIMIZATION.md) defines `J = Σ weight(c)` for each enabled soft constraint violated; hard constraints filter feasibility. Parsed float weights are converted through their decimal string representation to integer coefficients without further rounding and within explicit limits.
2. **Preserved:** exhaustive enumeration through eight roles remains default, enumerates all candidates, and is retained as the small-instance oracle.
3. **Implemented and bounded-verified:** CP-SAT is automatically dispatched for 9–50 roles. It matched an independent product-label oracle on 12 seeded four-role cases and the exhaustive backend on a separate case. Tests cover transitivity, hard conflict explanation, determinism, multiple optima, cap/truncation and sensitivity mechanics.
4. **Implemented:** output records OR-Tools version, seed, single-worker setting, per-solve time limit, candidate cap, objective status and whether the optimum set enumeration is complete. Sensitivity scenarios are caller-supplied and explicitly non-empirical.
5. **Remaining:** no scale benchmark at 50 roles, broad runtime distribution, weight range validated by domain experts, or architectural validation. Small algorithm tests do not establish research or architecture validity; see [`PARTITION_OPTIMIZATION.md`](PARTITION_OPTIMIZATION.md).

## Milestone D — P8 graph, quantum assumptions and interaction contracts

1. **Implemented and tested:** architecture graph schema 1.0.0 includes Actor → Presentation/Application → Quantum → Integration → Infrastructure. Integration/tier nodes and edges unsupported by requirements are explicit UNKNOWN placeholders with architectural-policy provenance.
2. **Implemented and tested:** interaction contract and Sync/Async decision-table schemas are versioned. Pipeline retains `UNDECIDED`; schema blocks approved modes unless a cited human decision, reviewer, timezone-aware timestamp, non-contradictory signal and complete contract are present. The Human Review editor records a decision/revision, checks exact source spans, recomputes downstream artifacts and saves a snapshot. No real Tutor decision exists, and semantic entailment remains a human responsibility.
3. **Partial:** quantum ownership/deployment remain UNKNOWN. Existing candidate relationships are retained; richer independent deployment assumptions need architecture review and evidence.
4. **Implemented and tested:** deterministic editable Draw.io XML export with stable cell IDs, layer layout, unknown styling and endpoint validation; Streamlit download is available. Tests parse XML but do not perform a Draw.io GUI round-trip.

## Milestone E — P9–P10 scenario and measurement support

1. **Implemented and tested:** QAME scenario schema 1.0.0 emits stimulus source, stimulus, environment, stimulated artifact, response and response measure with `SPECIFIED`/`UNKNOWN`/`UNSUPPORTED`, source refs only for values present in the cited span, and partial/complete status.
2. **Partial:** output records ISO/IEC 25010:2023 version and source characteristic label; IDs remain `UNMAPPED`/`UNSPECIFIED` pending reviewed taxonomy mapping. No ISO certification claim.
3. **Preserved:** targets/metrics are source specifications, not measurements. Quality profiles keep `NOT_MEASURED` or `INSUFFICIENT_EVIDENCE`; `PREDICTED` and `UNSUPPORTED` are not synthesized.
4. **Blocked/absent:** no runnable target, valid measurement environment or raw measurements. No measurement adapter was added; a target alone never produces PASS.

ISO's official page describes the 2023 product-quality model as nine characteristics; implementation must use the standard edition rather than the superseded 2011 model.

## Milestone F — P11 evaluation and release report

1. **Protocol documented:** [`EVALUATION_TRACKS.md`](EVALUATION_TRACKS.md) separates PetClinic fixture behavior, Tutor independent case, and synthetic optimizer correctness; it records provenance, baselines, ablations, measures and gates without inventing run results.
2. **Partially specified:** source-only dual-annotator/adjudication, matching, review-effort, partition-agreement and runtime methods are recorded. External source rights, independent labels, domain review and target system are not supplied.
3. **Separated:** algorithm tests, semantic extraction, architecture review and quality measurement have distinct evidence states. There are no eligible P2 semantic or measured-quality results.
4. **Implemented, bounded:** the app artifact ZIP now records a versioned reproducibility manifest and checksums; `scripts/validate_artifact_bundle.py` verifies member coverage, hashes and JSON structure. It does not replay the pipeline or authenticate the archive. Reproducing a live Tutor experiment remains gated on independent human input.
5. **Implemented:** [`FINAL_RESEARCH_COMPLETION_REPORT.md`](FINAL_RESEARCH_COMPLETION_REPORT.md) records bounded technical evidence and separately marks the actual case experiment and research validation `BLOCKED_EXTERNAL`.

## External blockers and stop conditions

- Independent annotations must come from people who have not seen the model output being evaluated. The repository cannot authenticate identity or prior exposure; record that limitation and do not label self-reports as verified identity.
- Gold/reference metrics need at least two independent annotations and an adjudication procedure fixed before viewing comparisons. No labels will be generated by the implementation agent.
- Quality measurement needs a runnable target system and valid environment; without it the correct state is `NOT_MEASURED`.
- External case-study material needs recorded source provenance and licensing/permission before redistribution.
- A research/architecture reviewer must approve a tactic catalog before any catalog entry is used as a case constraint.

## Verification per milestone

For each code milestone: add focused unit/adversarial tests, run the complete regression suite and compile check, validate exported artifacts, review explicit staged paths and secret scan, Conventional Commit, push without force, verify remote SHA and CI, then record those facts in the next documentation commit. Preserve `runs/`, snapshots and the P0 tag.
