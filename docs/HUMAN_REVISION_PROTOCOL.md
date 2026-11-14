# Human Revision Protocol

The Human Review tab supports Approve/Reject/Defer for a reviewable artifact, revision of R1–R6 name/activity/operation fields, and revision of supported step 04 constraints. Review outcomes change review metadata only. Responsibility and constraint edits change model inputs and trigger revalidation.

## Approve, reject, or defer an artifact

1. Choose a responsibility, evidence relation, quantum candidate, interaction, or quality profile.
2. Choose **APPROVE**, **REJECT**, or **DEFER** and provide a justification, source, and reviewer identifier.
3. Choose **Record artifact review**. The app records the old/new review status in decisions and revisions, updates the artifact's review field, writes the next snapshot, and shows the outcome in the report.

These review-only actions do not change constraints, partitions, contracts, or measurements, so they do not mark structural outputs stale. An approved quality profile remains `NOT_MEASURED`; an approved quantum remains `PROPOSED_NOT_VERIFIED`.

## Revise a responsibility

1. Expand **Edit name, activity, or operation and preview downstream impact**.
2. Select R1–R6, edit the supported fields, and provide the reason, source, and reviewer.
3. Choose **Preview responsibility impact** to see the proposed before/after values and affected outputs. No input or snapshot is saved by preview.
4. Choose **Apply responsibility revision & Revalidate** to update the frozen run input, recompute downstream artifacts, compare unaffected artifacts, and save the next snapshot.

The current responsibility revision keeps the existing FR reference/source span and resets that responsibility's review state to `REVIEW_REQUIRED`. Activity-to-WF-01 task mappings remain `UNRESOLVED` because the fixture has no task IDs.

## Preview then apply

1. Open **Human Review & Validation** and inspect the current validation report and audit records.
2. Enter the proposed edit and select **Preview impact**. The preview runs against a temporary candidate and displays predicted status/candidate counts. It marks downstream artifacts `STALE` and names the artifacts that the dependency map will recompute. It does not save a decision or snapshot.
3. Review the impact and choose **Apply & Revalidate** to persist the change. The system recomputes, compares unaffected artifacts, appends the decision/revision, saves the current JSON artifacts, and writes the next immutable snapshot.
4. Compare the earlier snapshot with the current run in the UI. The earlier snapshot remains available under `runs/<run_id>/snapshots/`.

## Supported edits

Target step must be `04`.

| Edit | Example | Object ID |
|---|---|---|
| Add hard must-link | `ADD MUST_LINK(R4,R6)` | New ID, e.g. `H4` |
| Add hard cannot-link | `ADD CANNOT_LINK(R1,R6)` | New ID, e.g. `H4` |
| Change an existing relation | `SET H3 CANNOT_LINK(R4,R5)` | The same constraint ID, e.g. `H3` |
| Disable a policy | `DISABLE H3` | `H3` |
| Enable a policy | `ENABLE H3` | `H3` |
| Remove a constraint | `REMOVE H4` | `H4` |

Self-links and duplicate IDs are rejected. Hard constraints are never relaxed automatically.

## Audit fields and impact

Each applied change records a decision ID, revision ID, target step/object, actual old value, submitted old-value label, new value, reason, source, reviewer, UTC timestamp, result, affected steps/artifacts, before/after values, and artifact diff. Constraint edits affect `constraints`, `partitions`, `quanta`, `interactions`, `quality_profiles`, `validation_report`, and the decision/revision audit. Responsibility edits affect `evidence`, `constraints`, `partitions`, `quanta`, `interactions`, `quality_profiles`, and `validation_report`. For the current responsibility edit, `raw_requirements` and `context` are checked as unaffected.

The preview uses a dependency map to show stale outputs. After a successful apply, the revision records the recomputed downstream artifact names and an empty post-revalidation stale list. Current revalidation recomputes the deterministic pipeline from the frozen input and checks the unaffected values; it does not selectively skip computation for unaffected stages.

## Safety and current limits

- H1/H2/H3 are what-if demo policies. A human change is recorded as `HUMAN_OVERRIDE`, with the reason attached as its provenance.
- A constraint conflict produces `INFEASIBLE`; the system does not show an invalid partition as feasible.
- Responsibility edits are limited to name/activity/operation; evidence relations, interaction contracts, quality measurements, and arbitrary constraint weights are not editable in the UI. Approve/Reject/Defer changes only review metadata for those records.
- Human approval or a recorded decision does not turn `PROPOSED_NOT_VERIFIED` into deployability evidence and does not turn `NOT_MEASURED` into a performance pass.
- `runs/` is local ignored output. The app never deletes prior snapshots.
