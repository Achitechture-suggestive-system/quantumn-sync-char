# EQCR + QAME local MVP

This repository implements the P0 demo flow from `EQCR_QAME_MVP_Demo_2026-11-19.md`.
It starts from the frozen PetClinic mini-case in `eqcr/fixture.py`, which contains
requirements and one text workflow but no source code, runtime topology, or confirmed
business policies.

The backend uses Pydantic schemas, NetworkX for the interaction graph, exhaustive
partition enumeration for the six-responsibility case, and JSON run snapshots.

## Run locally

Python 3.11 or newer is required. In PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Choose **Load PetClinic demo data**, then **Run offline fixture**. The local flow does
not require Ollama or network access. The initial run and later review revisions are
saved as JSON under `runs/<run_id>/`; the app also offers ZIP (including snapshots)
and validation-report downloads.

## Optional local LLM proposals

Start Ollama locally, install a compatible Qwen model, and use **Check local Ollama
models** in the Input tab. The app prefers `qwen3.5:4b` or `qwen3.5:9b` when either
is installed. `OLLAMA_HOST` can point the app at a different local Ollama endpoint.
For example, after installing Ollama, run `ollama pull qwen3.5:4b` in PowerShell.
The proposal bundle includes context normalization, responsibilities, typed evidence
relations, and tentative boundary hypotheses. The application checks IDs and resolves
citations to exact source spans. Every model proposal remains `REVIEW_REQUIRED`;
evidence and boundary hypotheses stay separate from deterministic evidence and
optimizer inputs. To use a complete, source-checked responsibility set, inspect it and
choose **Use these proposals for a candidate run**; the resulting run is still marked
`REVIEW_REQUIRED`.

The UI also accepts a complete structured project package in JSON. It must contain
`raw_requirements`, `responsibilities`, `evidence`, and `constraints`; source spans,
IDs, requirement links, evidence provenance, and constraint endpoints are validated
before the input is loaded. Download the editable starter from the Input tab. The
PetClinic button remains the precomputed replay path.
The current responsibility model is scoped to IDs R1–R6; structured upload does not
make the optimizer a general n-component architecture tool.

## Demo path

1. Load and run the precomputed fixture.
2. Inspect source references, typed evidence, and H1/H2/H3 what-if constraints.
3. Review all 203 partitions and the ten hard-feasible candidates tied at J=0.
4. Inspect the proposed quantum grouping and the two cited Pet–Visit interaction
   alternatives. Both Sync and Async remain `PROPOSED_NOT_VERIFIED`; no protocol is
   selected while timing, consistency, and failure requirements are unknown.
5. Inspect both QAME profiles: Owner Search is `NOT_MEASURED`; Pet–Visit has no
   supplied quality target and remains `INSUFFICIENT_EVIDENCE`.
6. In Human Review, submit `ADD MUST_LINK(R4,R6)` as H4. The run becomes
   `INFEASIBLE` and reports the H3/H4 conflict.
7. Submit `DISABLE H3` as a reviewed correction. Revalidation creates a new snapshot,
   records the reason/source/reviewer and artifact diff, and checks that unaffected
   input artifacts stayed the same.

The Human Review tab provides **Preview impact** before **Apply & Revalidate**. The
preview shows downstream artifacts as `STALE`, predicts the outcome, and does not save
the proposed decision. After application, the recomputed artifacts and cleared stale
state are recorded in the revision.

The same tab can revise responsibility names, activities, and operations with a before/after
impact preview, and records **APPROVE**, **REJECT**, or **DEFER** for responsibility,
evidence, quantum, interaction, and quality records. Review actions update review
metadata only; they do not turn an unmeasured target into a pass or prove deployability.

Each review action gets its own version, so the contradiction and its correction are
both inspectable. A constraint change recomputes the pipeline from frozen inputs;
the app compares steps 01–03 and records whether those artifacts stayed unchanged.

## Evidence and claim boundaries

- H1, H2, H3, and any human-added policies are demonstrative constraints, not
  confirmed PetClinic rules.
- J sums the weights of violated enabled soft constraints. The frozen fixture defines no
  soft constraints, so each feasible hard-constraint candidate ties at zero. The
  displayed selection is a deterministic tie-break, not an architecture recommendation.
- Responsibility and quantum boundaries are proposals. No independent deployment,
  release, rollback, data ownership, or runtime coupling evidence is included.
- Pet–Visit offers conditional Sync and Async hypotheses with source links. The edge
  stays `UNRESOLVED`, its contract fields stay `UNKNOWN`, and neither hypothesis is
  selected without relevant evidence and a decision.
- Owner Search is p95 <= 250 ms at 300 requests/s, but no measurement is recorded.
  Pet–Visit has no quality target. Neither profile claims a measured pass.

## Regression suite

The requested P0 checklist is represented by `tests/test_pipeline.py`. Run it with:

```powershell
\.venv\Scripts\python.exe -m pytest -v
```

For the implementation boundaries, runtime evidence, test results, review protocol,
and timed walkthrough, see `docs/PIPELINE_IMPLEMENTATION_STATUS.md`,
`docs/P0_RUNTIME_AUDIT.md`, `docs/VALIDATION_TEST_REPORT.md`,
`docs/HUMAN_REVISION_PROTOCOL.md`, and `docs/MVP_DEMO_SCRIPT.md`.
