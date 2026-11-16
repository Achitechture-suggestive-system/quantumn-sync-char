# Research-grade implementation plan — 2026-11-16

This plan follows the repository audit. It preserves the existing P0 baseline and keeps semantic claims separate from implementation checks. Work proceeds in small commits on `feat/p1-semantic-validation`; no change to `main` is included.

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
2. **Implemented and tested:** interaction contract and Sync/Async decision-table schemas are versioned. Pipeline retains `UNDECIDED`; schema blocks approved modes unless a cited human decision, reviewer, timezone-aware timestamp, non-contradictory signal and complete contract are present. Streamlit has no interaction approval editor; no real decision exists.
3. **Partial:** quantum ownership/deployment remain UNKNOWN. Existing candidate relationships are retained; richer independent deployment assumptions need architecture review and evidence.
4. **Implemented and tested:** deterministic editable Draw.io XML export with stable cell IDs, layer layout, unknown styling and endpoint validation; Streamlit download is available. Tests parse XML but do not perform a Draw.io GUI round-trip.

## Milestone E — P9–P10 scenario and measurement support

1. **Implemented and tested:** QAME scenario schema 1.0.0 emits stimulus source, stimulus, environment, stimulated artifact, response and response measure with `SPECIFIED`/`UNKNOWN`/`UNSUPPORTED`, source refs only for values present in the cited span, and partial/complete status.
2. **Partial:** output records ISO/IEC 25010:2023 version and source characteristic label; IDs remain `UNMAPPED`/`UNSPECIFIED` pending reviewed taxonomy mapping. No ISO certification claim.
3. **Preserved:** targets/metrics are source specifications, not measurements. Quality profiles keep `NOT_MEASURED` or `INSUFFICIENT_EVIDENCE`; `PREDICTED` and `UNSUPPORTED` are not synthesized.
4. **Blocked/absent:** no runnable target, valid measurement environment or raw measurements. No measurement adapter was added; a target alone never produces PASS.

ISO's official page describes the 2023 product-quality model as nine characteristics; implementation must use the standard edition rather than the superseded 2011 model.

## Milestone F — P11 evaluation and release report

1. Create three separately versioned tracks: the documented PetClinic case, Tutor Support, and synthetic algorithmic stress cases. Record source/provenance/licensing per input.
2. Specify independent annotator protocol, adjudication, matching rules, baselines, ablations, reviewer effort, uncertainty and runtime measurement before collecting data.
3. Separate algorithm correctness, semantic extraction, architecture review and empirical quality measurement in the reports.
4. Add artifact-bundle validation and a reproducibility rerun command; report actual configurations and actual results only.
5. Produce `FINAL_RESEARCH_COMPLETION_REPORT.md` with independent statuses `TECHNICALLY_COMPLETE`, `CASE_EXPERIMENT_COMPLETE`, `RESEARCH_VALIDATED`, `BLOCKED_EXTERNAL`, and `PARTIAL`.

## External blockers and stop conditions

- Independent annotations must come from people who have not seen the model output being evaluated. The repository cannot authenticate identity or prior exposure; record that limitation and do not label self-reports as verified identity.
- Gold/reference metrics need at least two independent annotations and an adjudication procedure fixed before viewing comparisons. No labels will be generated by the implementation agent.
- Quality measurement needs a runnable target system and valid environment; without it the correct state is `NOT_MEASURED`.
- External case-study material needs recorded source provenance and licensing/permission before redistribution.
- A research/architecture reviewer must approve a tactic catalog before any catalog entry is used as a case constraint.

## Verification per milestone

For each code milestone: add focused unit/adversarial tests, run the complete regression suite and compile check, validate exported artifacts, review explicit staged paths and secret scan, Conventional Commit, push without force, verify remote SHA and CI, then record those facts in the next documentation commit. Preserve `runs/`, snapshots and the P0 tag.
