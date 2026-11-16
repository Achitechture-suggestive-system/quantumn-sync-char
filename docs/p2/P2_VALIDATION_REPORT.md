# P2 — Báo cáo validation

## Trạng thái

**`ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`**

**Experiment status: `P2_BLOCKED_INDEPENDENT_ANNOTATION`.** Chưa có reviewer tự xác nhận đủ điều kiện/chưa tiếp xúc model output và chưa có annotation source-only được khóa. Không chạy inference từ fixture hoặc giả lập label để vượt blocker này.

**P2 case thật chưa hoàn tất.** Branch đã có Tutor Support, protocol source-only blind, review decisions và code path relation → policy constraint → exhaustive partitioner → downstream outputs. Chưa có source-only annotation thật, inference qwen hậu-lock, model review thật hoặc revision experiment thật. Không gọi test harness là kết quả model/case study.

Pasted methodology review đã dẫn tới thay đổi protocol: source-only labels được tách khỏi review output, 0..N responsibilities cho mỗi FR, relation universe có registry cố định và status riêng, `APPROVE/CORRECT/REJECT/DEFER` được hỗ trợ, và adjudication/gold-label protocol được ghi rõ. Những thay đổi này làm cho inference v6 trước đó không đủ điều kiện làm blind experiment.

## Kiểm tra cục bộ của milestone hiện tại

| Kiểm tra | Kết quả / phạm vi |
|---|---|
| Regression + P2 tests | `.venv\Scripts\python.exe -m pytest -q --tb=short` — 72 passed. Experiment-runner tests use `TEST_ONLY_NOT_MODEL_OUTPUT`; none invokes Ollama. |
| Compile | `.venv\Scripts\python.exe -m compileall -q app.py eqcr tests scripts` — exit 0. |
| Frozen P0 baseline / `main` | Không chủ ý sửa `main`, fixture baseline hoặc tag; chỉ làm việc trên `feat/p1-semantic-validation`. |
| Ollama v6 lịch sử | Đã gọi thật trước protocol mới; `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`, không làm inference hậu-blind hoặc reference label. |
| Ollama v7 hậu-blind | Chưa chạy; cần source-only annotation thật được khóa trước khi app mở model proposals. |
| P2 experiment CLI | `scripts/run_p2_experiment.py` đã có; yêu cầu annotation lock v2, đúng source hash, clean committed checkout, model tag `qwen3:4b`, prompt version v7 và local model digest. Chưa chạy do blocker độc lập. |
| P2 result export | Test-only exporter verifies run manifest, per-file SHA-256 checksum list and ZIP creation. No live run bundle exists. |
| Source/citation audit | Unit tests kiểm exact span, unknown IDs, missing endpoint citations, duplicate relation và self-relation gates; chưa có v7 live output để đánh giá. |
| Optimizer causal wiring | Test-only accepted relation → declared soft policy → optimizer → interactions/quality mapping; đây là kiểm code path, không phải case evidence. |
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
| Evidence → constraints | Human relation/implication decision + deterministic mapping + architectural policy. Chưa có actual human output. |
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
| Regression tests | 72 local tests passed; [GitHub Actions run 43849233685](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43849233685) also passed on the experiment-runner commit. |
| GitHub milestone / CI | Experiment-runner commit `1fe23ed7886e02b02e44e5ebb850e1b1e6dd6628` đã xác minh trên branch và Actions thành công; actual case experiment vẫn pending. |

### Checklist chạy P2 khi reviewer độc lập sẵn sàng

1. Chỉ định annotator chưa từng thấy Tutor model output; không gửi họ `LLM_EXTRACTION_EVALUATION.md`, P2 model-review worksheet, hay output v6/v7.
2. Annotator đọc source-only materials, hoàn tất 0..N roles, đánh dấu FR unresolved, và điền relation registry theo phạm vi/rationale.
3. Annotator tự khai báo `source_only_attested=true` và `no_prior_model_output_exposure=true`, rồi khóa/tải JSON qua app. Nếu không thể tự khai báo trung thực, dừng với `P2_BLOCKED_INDEPENDENT_ANNOTATION`.
4. Sau khi code đã commit và working tree sạch, model đã cài và Ollama chạy, thực hiện:

```powershell
.\.venv\Scripts\python.exe scripts\run_p2_experiment.py `
  --annotation-lock ".\P2_BLIND_ANNOTATION_LOCK.json" `
  --model qwen3:4b
```

5. Kiểm manifest/checksums trong `runs/p2-experiments/<run-id>/`; xem raw proposals và structural error report.
6. Mở riêng [P2_MODEL_REVIEW.md](P2_MODEL_REVIEW.md), ghi `APPROVE/CORRECT/REJECT/DEFER` thật, chạy reviewed 10-stage case và revision trước/sau.
7. Chỉ thêm semantic metrics sau khi hai annotation độc lập và adjudication/matching rules được ghi. Không có target chạy được thì quality tiếp tục `NOT_MEASURED`.
