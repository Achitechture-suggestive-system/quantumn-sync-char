# Validation and Test Report

**Date:** 2026-11-14
**Environment:** Windows; project `.venv`; Python 3.13.13; Pydantic 2.14.3; Streamlit 1.67.

## Automated suite

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Final result after the interaction, QAME profile, provenance, and applicability updates: **30 passed in 1.29 seconds**.

Coverage includes:

- Required schemas, unique identifiers, source references, exact source spans, typed evidence states, provenance, and review status.
- Bell(6)=203 enumeration, ten feasible zero-cost optima, and hard must/cannot conflict detection.
- Exactly-once responsibility membership, unknown ownership/infrastructure layers, unresolved Pet–Visit contract, cited conditional Sync/Async hypotheses without protocol selection, and allocation of both quality scenarios while preserving `NOT_MEASURED` / `INSUFFICIENT_EVIDENCE`.
- Artifact provenance and verification scope on every persisted artifact; baseline-only optimizer checks are explicitly marked not applicable after a human or input revision.
- Human Approve/Reject/Defer status recording, replay across structural recomputation, and a test proving an approved quality profile remains unmeasured and does not pass validation.
- Weighted soft-constraint optimization with quality-scenario references, and responsibility field revision that invalidates downstream artifacts and resets its review status.
- Constraint revision audit fields, dependency closure, stale preview list, correction outcome, serializable before/after diff, and unchanged unaffected inputs.
- Structured project package validation, source-checked LLM proposal promotion boundary, invalid/mismatched source reference rejection, typed evidence/boundary proposal citation resolution while preserving `REVIEW_REQUIRED`, and deterministic operation when Ollama is unavailable.
- ZIP artifact and versioned snapshot entry names.

Test names in `tests/test_pipeline.py`:

`test_schema_required_fields`, `test_no_missing_source_reference`, `test_unknown_is_not_false`, `test_evidence_relations_keep_provenance_and_review_state`, `test_bell6_partition_count_203`, `test_what_if_10_zero_cost_optima`, `test_soft_constraint_weight_and_quality_scenario_link_are_used`, `test_must_cannot_conflict_detected`, `test_each_responsibility_assigned_once`, `test_quantum_graph_exposes_unknown_layers_and_evidence`, `test_contract_unresolved_without_evidence`, `test_quality_target_not_measured`, `test_human_quality_review_does_not_fake_a_measurement_or_pass` (three review actions), `test_human_responsibility_edit_invalidates_downstream_and_resets_review`, `test_human_revision_audit_and_impact`, `test_dependency_graph_computes_transitive_impact_preview`, `test_human_correction_resolves_conflict_and_captures_actual_before_value`, `test_regression_unchanged_unaffected_artifacts`, `test_reproducible_rerun_with_frozen_fixture`, `test_structured_project_package_validates_source_spans`, `test_source_checked_llm_proposals_can_feed_candidate_pipeline`, `test_revision_diff_is_serializable_without_self_reference`, `test_invalid_llm_source_reference_stays_review_required`, `test_llm_evidence_and_boundary_proposals_resolve_sources_but_remain_review_required`, `test_ollama_unavailable_does_not_block_deterministic_mode`, and `test_zip_export_contains_artifacts_and_versioned_snapshots`.

The final suite also includes `test_sync_and_async_options_are_cited_hypotheses_without_selection` and `test_artifacts_include_provenance_and_scoped_verification_status`.

## App and workflow checks

- Streamlit started on `127.0.0.1:8765`; `/_stcore/health` and `/` returned HTTP 200.
- Streamlit AppTest loaded the PetClinic fixture and completed the deterministic run with no app exceptions.
- Streamlit AppTest uploaded a structured JSON package, validated it, and completed a deterministic `STRUCTURED_INPUT` run with no app exceptions.
- Streamlit AppTest rendered the saved prompt-v5 Ollama bundle, selected it for a candidate run, and completed `OLLAMA_ASSISTED` / `REVIEW_REQUIRED` with ten optimal candidates and no app exceptions. The saved run is `run-20261114T092136Z-f364720b`.
- Streamlit AppTest recorded `APPROVED` for R1, revised R1's operation, previewed and applied `MUST_LINK(R4,R6)`, then previewed and applied `DISABLE H3`. Snapshots v1–v5 preserved the baseline, review outcome, responsibility edit, `INFEASIBLE` conflict, and corrected `REVIEW_REQUIRED` result. The responsibility edit reset R1 to `REVIEW_REQUIRED` and the persisted revision recorded recomputed outputs with no stale artifacts remaining.
- The H4 preview marked partitions, quanta, interactions, quality profiles, and validation report `STALE`; it predicted `INFEASIBLE` without saving a snapshot. The final correction had 5 feasible / 5 optimal candidates and an unaffected-input regression check of `PASS`.
- The correction `DISABLE H3` predicted `REVIEW_REQUIRED`; applying saved v3 with five feasible and five optimal candidates. The regression check reported `PASS` for unchanged input/context/responsibility/evidence artifacts.
- Browser inspection confirmed the graph renders as SVG at a readable size, lists 203 partitions and 10 co-optima, and shows the Pet–Visit connection as `UNRESOLVED`. After quoting Graphviz IDs, the final browser pass had zero errors; the only warning was Graphviz worker fallback.
- The live `qwen3:4b` prompt-v5 flow received C0, workflow, requirements, and quality scenarios. It generated six normalized requirements, six responsibility proposals, one evidence proposal, and one boundary hypothesis. The app resolved FR citations to exact source spans and saved candidate run `run-20261114T092107Z-b5022115` as `OLLAMA_ASSISTED` / `REVIEW_REQUIRED`, with ten feasible and ten optimal candidates. Model-assisted generation plus candidate save took 72.15 seconds. This verifies output shape, source resolution, and candidate-pipeline integration, not semantic accuracy.
- The live browser ran the `PRECOMPUTED` case, previewed/applied H4, corrected it by disabling H3, and downloaded the final ZIP and report. The 17-entry ZIP contained snapshots v1/v2/v3 with statuses `REVIEW_REQUIRED`, `INFEASIBLE`, and `REVIEW_REQUIRED`; H3 was disabled in v3. The standalone report parsed as `REVIEW_REQUIRED`.

## Final implementation verification (2026-11-14)

- `pytest -q`: **30 passed in 1.29 s**. `python -m compileall -q app.py eqcr`: **PASS**.
- Streamlit AppTest: **0 app exceptions**; checked that local proposal artifacts preserve model, prompt, input hash, provenance, review status, and verification scope.
- Updated Streamlit server on `127.0.0.1:8766`: health and root returned **HTTP 200**. Browser completed the deterministic PetClinic run, H4 conflict preview/application, and H3 correction preview/application.
- Latest review run `run-20261114T101711Z-41291a74`: v1 `REVIEW_REQUIRED` / 10 feasible, v2 `INFEASIBLE` / 0 feasible, v3 `REVIEW_REQUIRED` / 5 feasible. H3 is disabled in v3. The review request and all JSON artifacts carry provenance and verification scope; all applicable assertions pass.
- The baseline-only “10 zero-cost optima” check is explicitly `NOT_APPLICABLE_AFTER_REVIEW_OR_INPUT_EDIT` in corrected runs. The conflicting constraint remains reported as `INFEASIBLE`.
- Built and parsed a ZIP from the final artifacts and snapshots: **17 entries**, snapshots v1/v2/v3 present, exported validation status `REVIEW_REQUIRED`.
- Live local Ollama UI run `run-20261114T101234Z-6cae71fa` used `qwen3:4b` and prompt v5. It returned six responsibility proposals, one evidence proposal, and one boundary hypothesis, all review-required; exact citation checks passed. Its UI correction snapshots recorded 10 → 0 → 5 feasible candidates.
- These checks establish reproducible local computation, source-span resolution, and recorded reviewer actions. They do not establish semantic correctness, deployability, selected Sync/Async safety, or measured quality.

## Status boundaries

The checks establish code-level structure, fixture-level optimization, repeatability, app rendering, and a locally generated schema-conforming response. They do not establish that responsibility semantics are correct, that the proposed quanta are deployable, that a sync/async contract is safe, that the 250 ms target passes, or that the case is expert-approved. Those results remain `REVIEW_REQUIRED`, `UNKNOWN`, `UNRESOLVED`, or `NOT_MEASURED` in the artifacts.
