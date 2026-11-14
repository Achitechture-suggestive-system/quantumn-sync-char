# Pipeline Implementation Status

**Status basis:** source inspection and runtime checks on 2026-11-14. This is a bounded PetClinic research MVP; it is not a general architecture recommender or production verification system.

## Gates

| Gate | Status | Evidence / boundary |
|---|---|---|
| A — Runtime recovery | **Complete** | Updated app starts locally; health/root endpoints return 200; final 30-test suite, AppTest, and browser flow pass. See [P0 runtime audit](P0_RUNTIME_AUDIT.md). |
| B — Deterministic pipeline | **Working P0 subset** | All ten report steps run for the frozen PetClinic case. Structured JSON packages are accepted after schema, source-span, responsibility, evidence, and constraint reference checks. Weighted soft constraints can link to quality scenarios; automatic constraint inference remains out of scope. |
| C — Human revision | **Working review and revision paths** | Reviewable artifacts support Approve/Reject/Defer outcomes. R1–R6 name/activity/operation and step 04 policies support preview, impact, snapshots, diffs, revalidation, and unchanged-input checks. Selective stage execution and arbitrary artifact field editing remain out of scope. |
| D — Integrated verification | **Structural checks complete for current fixture** | 30 automated tests and fresh browser/AppTest runs cover deterministic and live Ollama-assisted runs, proposal citation resolution, conditional Sync/Async outputs, both quality profiles, conflict/correction, snapshots, exports, and artifact provenance metadata. No independent semantic, deployment, or performance evaluation is claimed. |
| E — Local LLM | **Optional path exercised** | Live `qwen3:4b` prompt-v5 received C0, workflow, requirements, and quality scenarios; it returned context, responsibility, typed evidence, and boundary proposals. The app resolved FR citations and ran a candidate pipeline with ten feasible / ten optimal candidates. The run remains `REVIEW_REQUIRED`; semantics remain review-required. |
| F — Demo readiness | **Locally runnable** | Four tabs, candidate and architecture graphs, report, constraint preview, snapshots, JSON/ZIP downloads, and deterministic rehearsal are present. Browser downloads were parsed successfully; draw.io export is not included. |

## Pipeline steps

| Step | Implemented behavior | Remaining boundary |
|---|---|---|
| 01 Context Understanding | Frozen input has C0, six FRs, a workflow narrative, two quality scenarios, and exact source spans. An editable structured JSON template and upload path run Pydantic and traceability validation. | There is no free-form text/BPMN parser, arbitrary document ingestion, or rich input editor. Structured upload currently follows the six-responsibility R1–R6 schema. |
| 02 Responsibility Identification | Deterministic R1–R6 proposals and optional Ollama Activity/Operation/Responsibility proposals are stored with FR and exact source-span links. The UI can revise name/activity/operation and resets semantic review to `REVIEW_REQUIRED`. | WF-01 is narrative text without stable task IDs, so task-level workflow mappings are explicitly `UNRESOLVED`. |
| 03 Evidence Modeling | Typed relation records distinguish `PRESENT`, `SCOPED_ABSENT`, and `UNKNOWN`. Ollama may also return typed evidence proposals with cited requirement/source IDs and exact spans. | Model evidence proposals remain separately stored as `REVIEW_REQUIRED`; they are not merged into validated fixture evidence or used by constraints. There is no general-purpose evidence graph editor or ingestion engine. |
| 04 Constraint & Quality Reasoning | H1/H2/H3 are explicit hard `WHAT_IF_POLICY` constraints. Human `ADD`, `SET`, `ENABLE`, `DISABLE`, and `REMOVE` edits are attributed and conflict checked. Soft constraints carry a nonnegative weight and optional quality scenario IDs. | There is no automatic evidence-to-constraint inference or automatic derivation of weights from measurements. The fixture has no soft constraints. |
| 05 Candidate Optimization | Exhaustively enumerates all 203 partitions for six responsibilities, checks hard constraints, sums weights of violated soft constraints, ties deterministically, reports conflicts, and returns 10 J=0 optima for H1–H3. | Since no soft weights are configured in the frozen fixture, the ten optima tie at J=0; selected display candidate is a tie-break, not an optimum architecture claim. |
| 06 Quantum Boundary Refinement | Candidate groups map every responsibility exactly once. The graph shows the requirement-mentioned User, unknown presentation/application tier, proposed quanta, unknown infrastructure/storage, and the unresolved Pet–Visit edge. Ollama may additionally offer source-linked boundary hypotheses. | Ownership is `UNKNOWN`, deployment is not verified, and no API/Domain/Repository/Database/Outbox/Worker internals are assumed. Model boundary hypotheses remain separate from optimizer candidates and the graph. |
| 07 Interaction Design | Pet → Visit has a cited, unresolved edge and a contract skeleton. It lists conditional Sync request-response and Async command/notification hypotheses, each `PROPOSED_NOT_VERIFIED` and `REVIEW_REQUIRED`. | No protocol is selected. Operation, data dependency, request/response fields, versioning, consistency, latency, failure handling, retry, timeout, and idempotency remain `UNKNOWN`. |
| 08 Quality Allocation | Both supplied scenarios have profiles. Owner Search traces scenario → FR-01 / R1 → proposed quantum and records its target, proposed metric, measurement method, and source. Pet–Visit traces to R4/R6 and the interaction edge. | Owner Search remains `NOT_MEASURED`. Pet–Visit has no quality target or attribute, so its metric and method are `null` and status is `INSUFFICIENT_EVIDENCE`. No pass is inferred. |
| 09 Human Review | Reviewable responsibility, evidence, quantum, interaction, and quality records accept Approve/Reject/Defer. Responsibility fields and step 04 constraints support preview, before/after, impact, reason, source, reviewer, snapshots, diffs, and revalidation. | Structural edits are limited to responsibility name/activity/operation and constraints. Review outcomes change review metadata only; they do not certify semantic correctness, deployability, or measured quality. |
| 10 Verification & Iteration | Validation report exposes all ten step statuses, structural/traceability assertions, conflict state, empirical limits, artifact-wide provenance/verification scopes, applicability for baseline-only checks, and a regression check for unaffected inputs. | Revalidation deterministically recomputes the pipeline from the frozen input, then verifies unaffected artifacts. It does not selectively execute only changed stages or persist stale artifacts between calls. |

## Change impact map for the implemented edit

A step 02 responsibility change marks evidence, constraints, partitions, quanta, interactions, quality profiles, and the validation report stale in preview. A step 04 constraint change marks these downstream artifacts stale:

`partitions → quanta → interactions → quality_profiles → validation_report`

The constraint artifact is the edited source. `raw_requirements`, `context`, `responsibilities`, and `evidence` are checked as unaffected. After successful revalidation, the revision stores the recomputed artifact names and clears its stale list. This dependency map currently covers constraint edits; the other example change routes in the project brief remain future work.

## Deliverables and exports

- Persisted artifacts include `raw_requirements`, `context`, `responsibilities`, `evidence`, `constraints`, `partitions`, `quanta`, `interactions`, `quality_profiles`, `decisions`, `revisions`, and `validation_report`.
- Each run has `snapshots/v1.json` and later revision snapshots. The ZIP includes artifact JSON plus snapshots; the UI also offers a validation-report JSON download.
- No draw.io XML export or SQLite backend is included.
- No architecture style selection/evaluation, real deployment topology, benchmark, or independent expert approval is included.
