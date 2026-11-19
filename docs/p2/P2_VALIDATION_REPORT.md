# P2 — Báo cáo validation

## Trạng thái

**`ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`**

**Experiment status: `P2_BLOCKED_INDEPENDENT_ANNOTATION`.** Chưa có reviewer tự xác nhận đủ điều kiện/chưa tiếp xúc model output và chưa có annotation source-only được khóa. Không chạy inference từ fixture hoặc giả lập label để vượt blocker này.

**P2 case thật chưa hoàn tất.** Branch đã có Tutor Support, protocol source-only blind, review decisions và code path relation → policy constraint → exhaustive partitioner → downstream outputs. Chưa có source-only annotation thật, inference qwen hậu-lock, model review thật hoặc revision experiment thật. Không gọi test harness là kết quả model/case study.

## Browser smoke trên ứng dụng hiện tại — 2026-11-19

Streamlit UI được mở cục bộ và chạy **PetClinic `PRECOMPUTED` fixture** qua nút offline; các tab Input, Evidence & Constraints, Quantum & Contracts và Human Review & Validation đều mở được. Trang optimizer hiển thị 203 partitions, 10 feasible candidates và 10 optimum có J=0; graph, interaction, QAME và validation panels hiện diện. Không submit bất kỳ review/constraint action nào. App tạo run local ignored `runs/run-20261118T232503Z-357cfb32/`; đã để nguyên.

Sau đó load Tutor: source-only data được hiển thị, P1/P6 proposal IDs không xuất hiện, `Run offline fixture` bị disable trước lock. Không nhập hoặc khóa annotation; không gọi Ollama và không chạy model review. Trang hiện tại ghi zero console errors và một non-blocking GraphViz worker fallback warning. Đây là manual browser smoke cho UI gating và fixture flow, không phải automated browser suite, Tutor experiment hay bằng chứng ngữ nghĩa.

## Automated UI regression — 2026-11-19

Code/test commit `7e3d1e836eab2b04ee667506a9d2a4a72296f8f8` thêm Streamlit `AppTest` từ thao tác load PetClinic đến assertion đủ 10 pipeline stages, QAME trace-chain allocations, 203 partitions, 10 feasible/optimal candidates và trạng thái đo chất lượng `NOT_MEASURED`/`INSUFFICIENT_EVIDENCE`. Test monkeypatch persistence để không ghi file vào `runs/`. Local full suite: **130 passed**; compileall và diff check passed; [CI 44422385371](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44422385371) passed trên đúng SHA. Đây là regression UI của PetClinic `PRECOMPUTED`, không kiểm tra end-to-end Tutor inference/review hoặc semantic validity. `main` và P0 baseline không đổi.

## Cập nhật deterministic evidence audit — 2026-11-19

Code milestone `a334fac8b4193c469ed0a1499a1383db4164bdf1` thêm audit claim evidence tổng quát cho exact duplicate claim+citation, `PRESENT` đối nghịch `SCOPED_ABSENT`, và known state đi cùng `UNKNOWN`. Các evidence IDs bị trùng hoặc mơ hồ được liệt kê trong `artifacts.evidence.audit.blocked_evidence_ids`; `_derive_evidence_constraints` ghi `ABSTAINED` thay vì tạo constraint. Undirected endpoint canonicalization chỉ dùng khi direction được khai báo trong relation annotation. Predicate equivalence, entailment, thời gian/context và ý nghĩa nguồn không được suy diễn.

Verification là test code với `P2_TEST_ONLY`: **124 tests passed**, `compileall` và `git diff --check` passed; [CI run 44414391706](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44414391706) passed trên SHA trên. Đây không phải reviewer decision hoặc kết quả semantic evaluation; trạng thái case vẫn `P2_BLOCKED_INDEPENDENT_ANNOTATION`.

## Cập nhật tách FR mapping và citation — 2026-11-19

Tại code commit `9c7c7337fd9e94b034dd0230ab1bd667282e39af`, evaluator tính proposal FR coverage từ ID đã biết độc lập với exact citation resolution. Proposal có FR ID hợp lệ nhưng source reference sai vẫn được ghi là mapping cấu trúc và nhận `RESPONSIBILITY_CITATION_INVALID`; hai kết quả không che lấp nhau. Ý nghĩa responsibility vẫn chưa được đánh giá.

Local full suite: **126 tests passed**; compileall và diff check passed. [CI run 44416779052](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44416779052) passed trên code SHA. Test chỉ dùng dữ liệu `P2_TEST_ONLY`; semantic precision/recall/F1 vẫn `NOT_MEASURED_NO_ADJUDICATED_REFERENCE` và actual Tutor case vẫn `P2_BLOCKED_INDEPENDENT_ANNOTATION`.

## Cập nhật adversarial payload validation — 2026-11-19

Code commit `00be77f5486023d3ad88e1f602b20167d30c710c` bổ sung validation với malformed JSON row và ID/source/endpoint sai kiểu. Hàng không phải JSON object bị dừng với `P2ExperimentError`; malformed IDs được ghi thành error type thay vì làm evaluator crash. Đây chỉ là tính bền vững của structural evaluator.

Full suite: **128 tests passed**; compileall và diff check passed; [CI run 44417777751](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44417777751) passed trên code SHA. Chưa có inference hậu-lock, annotator, adjudication hoặc semantic metric thật.

## Recheck trạng thái hiện tại — 2026-11-17

| Bằng chứng | Kết quả |
|---|---|
| Checkout / remote feature ref | `feat/p1-semantic-validation`, clean at recheck; local HEAD and remote ref both `dbe4a5f417535d11aab9696ff60e593be19b6e1a`. [CI run 44005282683](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44005282683) passed. Fresh local checks on this code state: 114 tests passed; `compileall` passed. |
| P0 / `main` | Remote `main` vẫn `5ece0157bf2372fb879f694cee9f5f0846fcbe1a`; P0 tag vẫn là ancestor của `main`. |
| Annotation lock / model run | Không tìm thấy lock JSON trong checkout; `runs/p2-experiments/` chưa tồn tại. Không có post-lock inference hoặc reviewer decisions mới. |
| Local model availability | `ollama list` trả về tag `qwen3:4b` (ID prefix `359d7dd4bcda`). Đây chỉ là availability check; không gọi inference và không tạo model output. |
| Kết luận | `P2_BLOCKED_INDEPENDENT_ANNOTATION` vẫn giữ nguyên. Model chỉ được chạy sau khi nhận source-only annotation lock hợp lệ từ annotator chưa từng xem proposal Tutor. |

Pasted methodology review đã dẫn tới thay đổi protocol: source-only labels được tách khỏi review output, 0..N responsibilities cho mỗi FR, relation universe có registry cố định và status riêng, `APPROVE/CORRECT/REJECT/DEFER` được hỗ trợ, và adjudication/gold-label protocol được ghi rõ. Những thay đổi này làm cho inference v6 trước đó không đủ điều kiện làm blind experiment.

## Kiểm tra cục bộ của milestone hiện tại

| Kiểm tra | Kết quả / phạm vi |
|---|---|
| Regression + P2 tests at P6 milestone | `.venv\Scripts\python.exe -m pytest -q --tb=short` — 78 passed at the policy-catalog commit. Experiment-runner and policy-catalog tests use test-only data; none invokes Ollama. Current P7 working-tree validation is recorded separately below. |
| Compile | `.venv\Scripts\python.exe -m compileall -q app.py eqcr tests scripts` — exit 0. |
| Frozen P0 baseline / `main` | Không chủ ý sửa `main`, fixture baseline hoặc tag; chỉ làm việc trên `feat/p1-semantic-validation`. |
| Ollama v6 lịch sử | Đã gọi thật trước protocol mới; `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`, không làm inference hậu-blind hoặc reference label. |
| Ollama v7 hậu-blind | Chưa chạy; cần source-only annotation thật được khóa trước khi app mở model proposals. |
| P2 experiment CLI | `scripts/run_p2_experiment.py` yêu cầu annotation lock v3, exact source/package hashes, clean committed checkout, model tag `qwen3:4b`, prompt/schema versions; ghi local model metadata/digest nếu API cung cấp. Chưa chạy do blocker độc lập. |
| P2 result export | Test-only exporter verifies run manifest, per-file SHA-256 checksum list and ZIP creation. No live run bundle exists. |
| Source/citation audit | Unit tests kiểm exact span, unknown IDs, missing endpoint citations, duplicate relation và self-relation gates; chưa có v7 live output để đánh giá. |
| Optimizer causal wiring | Test-only accepted relation → versioned policy evaluation → soft constraint → optimizer → interactions/quality mapping; evaluation trace links policy/evidence/source/R endpoints. Đây là kiểm code path, không phải case evidence. |
| Versioned policy evaluation | Catalog `EQCR-P2-TUTOR-EXPERIMENTAL-POLICIES@1.0.0` records each evidence/policy outcome and abstention reason. Internal experimental rules are not independently reviewed tactics. |
| P7 optimizer code path | Exhaustive backend remains for R1–R8; CP-SAT is selected for R9–R50. Its output reports only proven optima, with a default cap of 200 and explicit completeness status. A reviewed six-role Tutor input would use the exhaustive backend; no actual post-review Tutor run exists yet. |
| P7 algorithm tests and CI | `tests/test_cpsat_optimizer.py` — 19 passed; full suite — 97 passed; compileall and staged `git diff --check` passed. Tests include 12 seeded four-role comparisons with an independent oracle, separate exhaustive comparison, nine-role Bell(9) fixture, transitivity, infeasibility explanation, cap, sensitivity, traceability and bad-parameter checks. They are synthetic algorithm tests, not Tutor model results. Commit `91b6b2e733bf7aa8ac36a400bda0123c9377cd44` is pushed; [CI run 43887720769](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43887720769) passed. |
| P8/P9 deterministic code and CI | Integration graph placeholder, deterministic Draw.io export, versioned interaction contract/decision table, and six-part QAME completeness plus ISO `UNMAPPED` state are implemented. Source fields only become `SPECIFIED` when their values occur in the cited span; unsupported prepared fields remain identified. These are policy/schema transformations; no mode/quality decision or measurement is inferred. Full suite — 104 passed; compileall and staged `git diff --check` passed. Commit `722c18245e0a7bd7f94674b2fd55c3174785613c` is pushed; [CI run 43892678200](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43892678200) passed. Raw Tutor source hash changes with optional six-part schema fields; future source-only locks must use the new canonical hash. |
| Human interaction-contract review path | Human Review JSON editor requires a complete `InteractionContract`, reviewer/time/rationale and exact source span, stores decision/revision and snapshot, and reruns downstream outputs. Mode does not derive optimizer constraints; the deterministic test asserts partitions and quality allocation remain unchanged while interaction/traceability changes. Test uses `P2_TEST_ONLY`, not an actual architecture decision. Full suite — 114 passed; compileall and diff check passed. Commit `8707334310dcd8fb7520b9d519a6023b753143a3` is pushed; [CI run 43898934609](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43898934609) passed. No Tutor contract decision exists. |
| Run artifact bundle manifest | App ZIP now records code/runtime/dependency/solver metadata, input and human-decision hashes when present, per-artifact provenance summary and output SHA-256. `scripts/validate_artifact_bundle.py` checks safe/unique member names, JSON parsing and checksum coverage. This does not authenticate the bundle or replay the run. Local full suite — 110 passed; compileall and `git diff --check` passed. Implementation/test commits `27f556d7087466ca4c97663994077362fe51e6ff` / `fc477903cef93db892057cb94ccc71e2c27d5103`; remote feature ref matches the latter and [CI run 43896335329](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43896335329) passed. Initial CI run `43895817702` failed because a test assumed the GitHub run ID was absent; follow-up isolates environment metadata and also tests the CI-present state. |
| Hard constraints | Test kiểm mỗi feasible candidate đối chiếu hard constraints đang bật. Tutor fixture hiện không khai báo hard domain constraint. |
| Human decisions / revision case thật | Chưa có; worksheet vẫn trống. Không tự thêm approvals, corrections hoặc scores. |
| Quality results | Hai scenario profiles có thể được tạo deterministic; measurement tiếp tục `NOT_MEASURED`. |
| Semantic score | Không có; thiếu independent reviewers và adjudicated gold labels. |
| Push/CI cho protocol milestone | Commit `1ec2c1b649901873a12cb43dba703bf7a723a411` đã được push; remote branch SHA khớp. [GitHub Actions run 43841700612](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43841700612) success. |

## Evidence provenance

| Output | Nguồn |
|---|---|
| FR/WF/scenario IDs | Prepared case/source requirement. |
| Historical P1–P6/E1/B1 v6 | Local LLM proposal, unblinded trước protocol; ghi rõ exploratory. |
| Current model schema v7 | Deterministic schema/prompt definition; chưa có inference v7 thực. |
| Blind lock | Human annotation nếu được nộp; test fixture chỉ có provenance test-only. |
| Evidence → constraints | Human relation/implication decision + deterministic mapping using versioned internal experimental case policy. Chưa có actual human output hoặc independent policy validation. |
| Candidate partitions/interactions/quality | Deterministic transformation; test runs là `P2_TEST_ONLY`, live post-review case chưa chạy. |
| Review decisions | Human decision chỉ khi reviewer thực sự cung cấp; chưa có quyết định case thật trong checkout. |

Structural evaluation của runner đếm proposal coverage/unresolved FRs, exact source-ref resolution, relation status và error types. Đây là kiểm tra deterministic. Responsibility/relation semantic correctness chỉ được tính nếu có adjudicated reference và explicit matching decisions; hiện report để `NOT_MEASURED_NO_ADJUDICATED_REFERENCE`.

## Acceptance matrix

| Tiêu chí | Trạng thái |
|---|---|
| Case ngoài PetClinic, nguồn FR/WF/scenario traceable | Đã chuẩn bị và test cấu trúc. |
| Ollama thật v7 sau blind checkpoint | Chưa đạt; v6 cũ bị loại khỏi blind evidence. |
| Cited proposals và unsupported/duplicate/ambiguous checks | Code/test đã có; đánh giá live hậu-lock đang chờ output. |
| Source-only worksheet trước model | Template và UI lock có; chưa có reviewer chưa tiếp xúc model output nộp annotation. |
| Hai reviewer độc lập, adjudication và gold labels | Protocol draft; chưa thực hiện, vì vậy không có semantic metric. |
| Review actions và unsupported proposal gate | Code/test path có; case thật chờ human decisions. |
| Evidence policy vào optimizer cho case thật | Test-only path đã xác minh; actual case pending. |
| 10 pipeline stages với model-reviewed case thật | Chưa đạt; chỉ synthetic test path đã chạy. |
| Human revision before/after case thật | Chưa đạt; chỉ synthetic test path đã kiểm causal propagation. |
| Regression tests | P6 commit passed 78 tests; [GitHub Actions run 43882340244](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43882340244). P7 commit passes 97 tests locally and in CI; [run 43887720769](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43887720769). |
| GitHub milestone / CI | Policy-catalog commit `ab26975b3bf9b8f2f8635ac825211a2a7a972ff6` đã xác minh trên branch và Actions thành công; actual case experiment vẫn pending. |

### Checklist chạy P2 khi reviewer độc lập sẵn sàng

1. Chỉ định annotator chưa từng thấy Tutor model output; không gửi họ `LLM_EXTRACTION_EVALUATION.md`, P2 model-review worksheet, hay output v6/v7.
2. Annotator đọc source-only materials, hoàn tất 0..N roles, đánh dấu FR unresolved, và điền relation registry theo phạm vi/rationale.
3. Annotator tự khai báo `source_only_attested=true` và `no_prior_model_output_exposure=true`, rồi khóa/tải JSON qua app. Nếu không thể tự khai báo trung thực, dừng với `P2_BLOCKED_INDEPENDENT_ANNOTATION`.
4. Sau khi code đã commit và working tree sạch, model đã cài và Ollama chạy, thực hiện:

```powershell
.\.venv\Scripts\python.exe scripts\run_p2_experiment.py `
  --annotation-lock ".\P2_BLIND_ANNOTATION_LOCK.json" `
  --source-package ".\docs\p2\source_only_reviewer" `
  --model qwen3:4b
```

5. Kiểm manifest/checksums trong `runs/p2-experiments/<run-id>/`; xem raw proposals và structural error report.
6. Mở riêng [P2_MODEL_REVIEW.md](P2_MODEL_REVIEW.md), ghi `APPROVE/CORRECT/REJECT/DEFER` thật, chạy reviewed 10-stage case và revision trước/sau.
7. Chỉ thêm semantic metrics sau khi hai annotation độc lập và adjudication/matching rules được ghi. Không có target chạy được thì quality tiếp tục `NOT_MEASURED`.

## Cập nhật P2.1 — package source-only và lock validator — 2026-11-19

Commit `931dea62472ea459eacd33b1fbe6196eb4e619ce` bổ sung package reviewer đúng năm file allowlisted, manifest/hash theo source spans, lock gắn manifest version/hash, CLI chỉ-đọc để kiểm tra lock và ngăn UI hiển thị raw Tutor helper mappings trước lock. AppTest kiểm source-only payload nhìn thấy; lock test từ chối timestamp tương lai. Đây là infrastructure/test evidence, không phải annotation hoặc experiment result. Local full suite hiện tại: 121 passed; `compileall -q app.py eqcr scripts tests` và `git diff --check` qua. Remote ref đã xác minh cùng SHA; [CI run 44410991542](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44410991542) completed success.

`main` vẫn `5ece0157bf2372fb879f694cee9f5f0846fcbe1a`, không thay đổi.

Các báo cáo P2.1 mới:

- [Source-only package guide](SOURCE_ONLY_REVIEWER_GUIDE.md) và [lock validation](ANNOTATION_LOCK_VALIDATION.md).
- [Actual experiment protocol](ACTUAL_EXPERIMENT_PROTOCOL.md) và [current Tutor experiment state](ACTUAL_TUTOR_EXPERIMENT.md).
- [Causal before/after trace](BEFORE_AFTER_CAUSAL_TRACE.md) và [research validity](P2_RESEARCH_VALIDITY_REPORT.md).

Kết quả trạng thái ở lần recheck: source package đã được commit và push; lock thật không có; Ollama có tag `qwen3:4b` nhưng không được gọi. Do đó inference, human review, actual optimizer/10-stage case run, revision experiment và semantic metrics vẫn chờ reviewer độc lập. UI source-only gate phát hiện và khắc phục việc raw Tutor input/helper mappings từng xuất hiện trước lock.

Sau commit tài liệu `5a2ed9e10b03860037afacdec73818d97370a393`, [CI run 44412232466](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44412232466) passed. Browser smoke trên app local ngày 2026-11-19 đã nạp Tutor case, kiểm DOM trước lock không có helper mappings hoặc proposal IDs `P1–P6/E1/B1`, kiểm nút `Run local Ollama proposals` vẫn disabled sau khi UI phát hiện model. Không thực hiện inference; đây là kiểm tra UI thủ công, không phải reviewed end-to-end case run.

## Nhánh demo unblinded được cách ly — 2026-11-19

Implementation milestone trên `feat/tutor-exploratory-demo` thêm mode `EXPLORATORY_UNBLINDED_DEMO`, lưu dưới `runs/demo-unblinded/`, ghi rõ `EXCLUDED_FROM_BLIND_RESEARCH`, và từ chối demo bundles trong blind evaluator. Nó cho phép operator trình diễn live model sau checkbox riêng, nhưng không tạo source-only lock, blind labels hoặc semantic score. Thay đổi demo không chuyển trạng thái P2 research khỏi `P2_BLOCKED_INDEPENDENT_ANNOTATION`.

Test-only AppTest exercise pending run (zero responsibilities), explicit review, policy-to-optimizer flow and evidence revision. Đây là kiểm tra wiring, không phải human decision hoặc kết quả case thật. Tại thời điểm code milestone chưa có live inference/review/revision; trạng thái demo được cập nhật riêng trong [demo report](../demo/TUTOR_E2E_DEMO_RESULT.md). P0 `main` giữ nguyên.

## Nhánh demo unblinded được cách ly — 2026-11-19

Implementation milestone trên `feat/tutor-exploratory-demo` thêm mode `EXPLORATORY_UNBLINDED_DEMO`, lưu dưới `runs/demo-unblinded/`, ghi rõ `EXCLUDED_FROM_BLIND_RESEARCH`, và từ chối demo bundles trong blind evaluator. Nó cho phép operator trình diễn live model sau checkbox riêng, nhưng không tạo source-only lock, blind labels hoặc semantic score. Thay đổi demo không chuyển trạng thái P2 research khỏi `P2_BLOCKED_INDEPENDENT_ANNOTATION`.

Test-only AppTest exercise pending run (zero responsibilities), explicit review, policy-to-optimizer flow and evidence revision. Đây là kiểm tra wiring, không phải human decision hoặc kết quả case thật. Tại thời điểm code milestone chưa có live inference/review/revision; trạng thái demo được cập nhật riêng trong [demo report](../demo/TUTOR_E2E_DEMO_RESULT.md). P0 `main` giữ nguyên.
