# P0 Runtime Audit

**Audit date:** 2026-11-14
**Repository:** `C:\disk D\quantumn-sync-char`
**Scope:** Gate A runtime recovery plus the implemented deterministic, review, export, and local Ollama paths.

## Environment

- Windows PowerShell, Python 3.13.13 in the project `.venv` (the project requires Python 3.11 or newer).
- Dependencies used for verification were installed in `.venv` and are declared in `requirements.txt`.
- Ollama was reachable at `http://127.0.0.1:11434`; `ollama list` showed `qwen3:4b`. No model was downloaded by this work.
- A first dependency install targeted the shared/global Python and changed its Starlette version, conflicting with its existing FastAPI install. Starlette was restored to 0.41.3. All subsequent work and verification used `.venv`; the global Python environment was not used for the app.

## Commands and results

| Command / action | Result |
|---|---|
| `\.venv\Scripts\python.exe -m pytest -v` | **30 passed** in 1.29 s on the final implementation. |
| `\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8765` | Server started at `http://127.0.0.1:8765`. |
| `Invoke-WebRequest http://127.0.0.1:8765/_stcore/health` | HTTP 200, body `ok`. |
| `Invoke-WebRequest http://127.0.0.1:8765/` | HTTP 200; Streamlit app HTML returned. |
| `AppTest.from_file("app.py").run()` then load and run PetClinic | No app exceptions; deterministic run rendered. |
| Streamlit AppTest: approve R1, revise R1, preview/apply H4, preview/apply `DISABLE H3` | No app exceptions. v1 baseline; v2 review-only approval; v3 responsibility revision; v4 `INFEASIBLE`; v5 `REVIEW_REQUIRED`, 5 feasible / 5 optimal; unaffected artifact check `PASS`. Revised R1 returned to `REVIEW_REQUIRED`. |
| Streamlit AppTest: upload a structured JSON project package, validate, then run | No app exceptions; accepted package was labeled `USER_SUPPLIED` and ran in `STRUCTURED_INPUT` mode. |
| Streamlit AppTest: load saved prompt-v5 model proposals, choose them for a candidate run, then run | No app exceptions; `OLLAMA_ASSISTED` / `REVIEW_REQUIRED`, 10 optimal candidates. |
| Browser run through Streamlit | Graph rendered as SVG; baseline displayed 203 partitions and 10 co-optima. Latest browser pass had 0 errors and 1 Graphviz worker fallback warning. |
| Ollama flow with `qwen3:4b`, prompt v5 | The model received C0, workflow, FRs, and quality scenarios. Six normalized requirements and six responsibilities passed citation/coverage checks; one typed evidence proposal and one boundary hypothesis resolved to exact source spans. The candidate run completed as `OLLAMA_ASSISTED` / `REVIEW_REQUIRED`, with 10 feasible and 10 optimal candidates. Every model proposal remained `REVIEW_REQUIRED`. |
| Browser end-to-end deterministic flow | Loaded the `PRECOMPUTED` PetClinic data, ran offline, previewed/applied H4 (`INFEASIBLE`), previewed/applied `DISABLE H3` (`REVIEW_REQUIRED`), and downloaded the ZIP/report. No browser errors; ZIP parsed with 17 entries and snapshots v1/v2/v3. |

## Gate A failures found and repaired

1. The original 14-test suite first reported 11 passing and 3 failing. The constraint parser matched a single character from `R1`–`R6` instead of a full responsibility ID; the parser now accepts the full IDs.
2. Revision audit output initially embedded a diff that referred back to the revision containing that diff. The stored diff now excludes the decision and revision containers and is JSON serializable.
3. A browser pass found invalid Graphviz node identifiers for the new unknown-layer placeholders. IDs are now quoted in DOT. The final graph renders, and the final browser run had no JavaScript errors.
4. A test for ZIP paths initially expected the storage helper to add `.json` to extra entries. The UI already passes complete names; the test now verifies the actual exported format.

An early Graphviz fallback warning remains: Streamlit could not find a worker script and rendered on the main thread. The SVG was visible and the browser reported no error after the DOT fix.

## Verified run artifacts

The app writes run files under `runs/`; `.gitignore` keeps run output local. These files were retained.

- `run-20261114T075254Z-2c6faa99`: v1 baseline (`REVIEW_REQUIRED`, 10 feasible); v2 contradiction (`INFEASIBLE`, 0 feasible); v3 correction (`REVIEW_REQUIRED`, 5 feasible / 5 optimal).
- `run-20261114T081311Z-2d7b8422`: local `qwen3:4b` proposal candidate run (`OLLAMA_ASSISTED`, `REVIEW_REQUIRED`, 10 feasible / 10 optimal).
- `run-20261114T081959Z-62893c06`: UI review rehearsal with v1/v2/v3 and the human correction regression check.
- `run-20261114T085333Z-8ee6a11e`: final review/impact rehearsal with v1–v5; the persisted responsibility revision has seven recomputed downstream artifacts and an empty post-revalidation stale list.
- `run-20261114T091238Z-dadd2e5e`: live `qwen3:4b` prompt-v4 candidate run with six responsibilities, one evidence proposal, one boundary hypothesis, and 10 feasible / 10 optimal candidates; status remains `REVIEW_REQUIRED`.
- `run-20261114T091359Z-c7633362`: Streamlit AppTest candidate run using the saved prompt-v4 model response; `OLLAMA_ASSISTED` / `REVIEW_REQUIRED`, 10 optimal candidates.
- `run-20261114T091634Z-ce67968a`: browser happy-path run; downloaded ZIP and validation-report JSON parsed successfully.
- `run-20261114T092107Z-b5022115`: live `qwen3:4b` prompt-v5 model-assisted candidate run with full input context; `REVIEW_REQUIRED`, 10 feasible / 10 optimal candidates.
- `run-20261114T092136Z-f364720b`: Streamlit AppTest candidate run using the saved prompt-v5 bundle; `OLLAMA_ASSISTED` / `REVIEW_REQUIRED`, 10 optimal candidates.
- `run-20261114T092512Z-2c06c772`: browser rehearsal with H4 conflict, H3 correction, and export; ZIP snapshots preserve `REVIEW_REQUIRED` → `INFEASIBLE` → `REVIEW_REQUIRED`.

## Real local model result

The prompt-v5 model-assisted generation and candidate save took 72.15 seconds. The model received C0, workflow, six FRs, and two quality scenarios, then returned six normalized requirements, six responsibility proposals, one typed evidence proposal, and one boundary hypothesis. Model citations use FR IDs; the application resolves each to the exact source ID and span. The checks passed and `can_apply_to_fixture` was true. Candidate run `run-20261114T092107Z-b5022115` has 10 feasible / 10 optimal candidates and overall status `REVIEW_REQUIRED`. The browser rehearsal exported the conflict/correction snapshots and standalone report; both parsed successfully. These results verify schema, source-link, and pipeline behavior, not semantic correctness. The app sends the Pydantic JSON Schema as Ollama's structured output `format`; see [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs) and [Ollama chat API](https://docs.ollama.com/api/chat).

## Final implementation verification (2026-11-14)

- `pytest -q`: **30 passed in 1.29 s**; `compileall`: **PASS**; Streamlit AppTest: **0 app exceptions**.
- The updated app was freshly started at `http://127.0.0.1:8766`; `/_stcore/health` and `/` returned HTTP 200. Port 8765 was already held by an existing app process, which was left untouched.
- Live Ollama run `run-20261114T101234Z-6cae71fa` used `qwen3:4b` / prompt v5. It produced six responsibilities, one typed evidence proposal, and one boundary hypothesis; source resolution passed and the run remained `REVIEW_REQUIRED`. Human edits recorded `REVIEW_REQUIRED` → `INFEASIBLE` → `REVIEW_REQUIRED`, with 10 → 0 → 5 feasible candidates.
- Fresh deterministic UI run `run-20261114T101711Z-41291a74` recorded snapshots v1/v2/v3, H3 disabled in v3, five feasible/optimal candidates, provenance and verification scope on every artifact and the review request, and all applicable validation assertions passing.
- The final ZIP check parsed 17 entries with v1/v2/v3 snapshots and an exported `REVIEW_REQUIRED` validation report.
- The baseline optimizer assertion is explicitly marked not applicable after a review/input change; conflict checks remain active. No semantic, deployment, Sync/Async selection, or quality measurement claim is made.

## Current run instructions

```powershell
cd "C:\disk D\quantumn-sync-char"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 8766
```

Open `http://127.0.0.1:8766`. The offline PetClinic flow has no Ollama dependency. To use the optional local model, start Ollama separately, choose **Check local Ollama models**, then **Run local Ollama proposals**. The measured generation time above can vary by hardware and model state.
