# MVP Demo Script (6–8 minutes, after model proposals are prepared)

## Before the demo

Start the local app:

```powershell
cd "C:\disk D\quantumn-sync-char"
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8766
```

Open `http://127.0.0.1:8766`. The deterministic path requires no network service or Ollama. If presenting the model path, start Ollama and confirm a local Qwen model is listed. On the audited machine, `qwen3:4b` is installed; the latest prompt-v5 model-assisted flow took about 72 seconds. Run it before the timed walkthrough if generation latency is uncertain.

## Walkthrough

### 00:00–01:00 — Input and scope

1. Select **Load PetClinic demo data**.
2. Show C0, six FRs, the single narrative workflow, and two scenarios.
3. State that this is requirements-only input with no source code, runtime topology, or confirmed business rules. Point out the `PRECOMPUTED` fixture label.
4. Optional structured input: download the editable JSON template, then upload a complete project package and choose **Load structured project JSON**. The package must contain `raw_requirements`, `responsibilities`, `evidence`, and `constraints`; schema, identifier, source-span, and referential checks run on load.

### 01:00–02:00 — Optional model proposal

1. Choose **Check local Ollama models** and select an installed model.
2. Choose **Run local Ollama proposals**.
3. Show the prompt version, input hash, generation parameters, context summary, six responsibility proposals, typed evidence proposal, boundary hypothesis, and resolved source references.
4. Explain that matching source spans establish provenance only; every proposal remains `REVIEW_REQUIRED`. Evidence and boundary hypotheses do not automatically change fixture evidence or optimizer candidates.
5. For a model-assisted run, choose **Use these proposals for a candidate run**, then **Run with these LLM proposals**. If no model is installed or generation is slow, continue with the offline fixture.

### 02:00–03:00 — Evidence and constraints

1. Open **Evidence & Constraints**.
2. Show a `PRESENT` source-backed relation, the `UNKNOWN` Pet–Visit consistency relation, and the `SCOPED_ABSENT` runtime topology record.
3. Show H1/H2/H3 as what-if policies, not established PetClinic rules.

### 03:00–04:15 — Candidate and graph

1. Open **Quantum & Contracts**.
2. Show Bell(6)=203, ten feasible co-optima, and J=0. Explain that all tie because the fixture has no soft constraints.
3. Show Q1–Q4 graph membership and exactly-once assignment.
4. Show unknown presentation/application and infrastructure/storage layers as dashed placeholders. Select a node/edge in the detail controls to inspect evidence and rationale.
5. Show Pet → Visit as `UNRESOLVED`; both cited Sync and Async options are conditional `PROPOSED_NOT_VERIFIED` hypotheses, and all contract fields remain `UNKNOWN`.
6. Show both QAME profiles: Owner Search → R1 → Q1 is `NOT_MEASURED`; Pet–Visit → R4/R6 has no target or metric and remains `INSUFFICIENT_EVIDENCE`.

### 04:15–06:30 — Conflict, preview, correction

1. Open **Human Review & Validation**.
2. Optional: expand the R1 responsibility editor, change a name/activity/operation, preview its downstream impact, and apply. Its semantic status returns to `REVIEW_REQUIRED`; this extra revision adds one snapshot version.
3. Keep target step `04`, object ID `H4`, and new value `ADD MUST_LINK(R4,R6)`. Enter the reason/source/reviewer and choose **Preview impact**.
4. Show affected partitions/quanta/interactions/quality/report marked `STALE`; preview predicts `INFEASIBLE` and does not save a snapshot.
5. Choose **Apply & Revalidate**. Show the new version and H3/H4 conflict; no feasible partition is returned.
6. Change object ID to `H3` and new value to `DISABLE H3`. Explain that the what-if cannot-link is withdrawn for this experiment.
7. Preview and apply. Show `REVIEW_REQUIRED`, 5 feasible / 5 optimal candidates, the decision reason and actor, and the unchanged-input regression check.

### 06:30–08:00 — Compare and export

1. Compare v1, v2, and v3 in the review tab. v1 is the baseline; v2 preserves the contradiction; v3 records the human correction.
2. Show the final validation report and its explicit limits.
3. On the Input tab, use **Download all run artifacts (ZIP)** or **Download validation report (JSON)**. A live browser run confirmed that the ZIP preserves all three snapshots and the final report.

## Expected result and claim boundary

- Baseline: 203 total partitions, 10 hard-feasible/optimal candidates, J=0, overall `REVIEW_REQUIRED`.
- H4 contradiction while H3 is active: `INFEASIBLE`, zero feasible candidates, conflict names H3/H4.
- Disable H3: five feasible/optimal candidates; unchanged input artifacts check `PASS`; overall status remains `REVIEW_REQUIRED`.
- Do not claim the selected quantum is practically optimal, that the LLM is semantically correct, that deployment boundaries are proven, that either Pet–Visit protocol is selected, or that 250 ms at 300 requests/s was achieved.
