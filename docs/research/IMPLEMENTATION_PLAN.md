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
2. Add a policy/tactic catalog schema with IDs, version, source, quality driver, evidence preconditions, required human decision, endpoint mapping, emitted constraint, side effects and abstention conditions.
3. Keep evidence observation, interpretation, architectural decision and optimizer constraint as separate records. Unregistered predicates and ambiguous evidence abstain.
4. Add duplicate, contradiction, invalid citation, reflexive relation, endpoint mismatch, unsupported promotion and policy/version mutation tests.

Catalog entries must be reviewed and tied to a source before being treated as architectural tactics. CMU/SEI defines tactics in relation to quality-attribute response and analysis models; generic co-location/separation heuristics must not be relabeled as validated tactics.

## Milestone C — P7 optimizer verification and scale

1. Publish the objective and weight policy in machine-readable and human-readable form. Current objective: `J = Σ weight(c)` for each enabled soft constraint `c` violated by a partition; hard constraints filter feasibility.
2. Preserve the exhaustive enumerator as the small-instance oracle and retain all co-optimal solutions.
3. Add an optional CP-SAT solver behind an explicit size threshold only after it matches the exhaustive oracle for all generated small test cases and randomized seeded cases.
4. Record solver version, seed, time limit, optimality status and any enumeration cap. Add hard-feasibility validation independent of the solver, transitivity tests, all-optimum tests, infeasibility explanation and weight sensitivity artifacts.
5. Keep a clear result distinction between `OPTIMAL_FOR_DECLARED_OBJECTIVE` and architectural validation; solver optimum is not a validated architecture.

## Milestone D — P8 graph, quantum assumptions and interaction contracts

1. Extend the architecture graph to include the required Integration tier while keeping unknown nodes explicit.
2. Add versioned interaction contract schema and decision table. Sync/Async stays `UNDECIDED` absent timing, consistency, failure, retry and idempotency evidence.
3. Attach dependencies and deployment assumptions to quantum candidates with source/reviewer provenance; do not infer deployability from a partition.
4. Add deterministic editable Draw.io export from graph JSON with stable node/edge IDs, unknown placeholders, and XML round-trip/schema tests.

## Milestone E — P9–P10 scenario and measurement support

1. Represent the six quality attribute scenario parts explicitly: stimulus source, stimulus, environment, stimulated artifact, response, and response measure. Validate which parts are specified and retain unresolved fields.
2. Map characteristics using versioned ISO/IEC 25010:2023 product-quality identifiers. Preserve source quote, human/LLM/deterministic provenance, `UNMAPPED`, and reviewer decision; do not claim ISO certification.
3. Use distinct states: `SPECIFIED`, `PREDICTED`, `MEASURED`, `NOT_MEASURED`, `UNSUPPORTED`. A target is not an observation.
4. Add measurement adapters only for an available target with a documented environment, repeat protocol, raw measurement and method. No adapter may produce a pass from target text alone.

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
