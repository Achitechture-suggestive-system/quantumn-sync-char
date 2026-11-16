# P2 — Báo cáo validation

## Trạng thái

**`ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`**

**P2 case thật chưa hoàn tất.** Branch đã có Tutor Support, protocol source-only blind, review decisions và code path relation → policy constraint → exhaustive partitioner → downstream outputs. Chưa có source-only annotation thật, inference qwen hậu-lock, model review thật hoặc revision experiment thật. Không gọi test harness là kết quả model/case study.

Pasted methodology review đã dẫn tới thay đổi protocol: source-only labels được tách khỏi review output, 0..N responsibilities cho mỗi FR, relation universe có registry cố định và status riêng, `APPROVE/CORRECT/REJECT/DEFER` được hỗ trợ, và adjudication/gold-label protocol được ghi rõ. Những thay đổi này làm cho inference v6 trước đó không đủ điều kiện làm blind experiment.

## Kiểm tra cục bộ của milestone hiện tại

| Kiểm tra | Kết quả / phạm vi |
|---|---|
| Regression + P2 tests | `.venv\Scripts\python.exe -m pytest -q --tb=short` — 63 passed. Test-only proposals dùng provenance `P2_TEST_ONLY`. |
| Compile | `.venv\Scripts\python.exe -m compileall -q app.py eqcr tests` — exit 0. |
| Frozen P0 baseline / `main` | Không chủ ý sửa `main`, fixture baseline hoặc tag; chỉ làm việc trên `feat/p1-semantic-validation`. |
| Ollama v6 lịch sử | Đã gọi thật trước protocol mới; `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`, không làm inference hậu-blind hoặc reference label. |
| Ollama v7 hậu-blind | Chưa chạy; cần source-only annotation thật được khóa trước khi app mở model proposals. |
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

## Acceptance matrix

| Tiêu chí | Trạng thái |
|---|---|
| Case ngoài PetClinic, nguồn FR/WF/scenario traceable | Đã chuẩn bị và test cấu trúc. |
| Ollama thật v7 sau blind checkpoint | Chưa đạt; v6 cũ bị loại khỏi blind evidence. |
| Cited proposals và unsupported/duplicate/ambiguous checks | Code/test đã có; đánh giá live hậu-lock đang chờ output. |
| Source-only worksheet trước model | Template và UI lock có; chưa có người điền. |
| Hai reviewer độc lập, adjudication và gold labels | Protocol draft; chưa thực hiện, vì vậy không có semantic metric. |
| Review actions và unsupported proposal gate | Code/test path có; case thật chờ human decisions. |
| Evidence policy vào optimizer cho case thật | Test-only path đã xác minh; actual case pending. |
| 10 pipeline stages với model-reviewed case thật | Chưa đạt; chỉ synthetic test path đã chạy. |
| Human revision before/after case thật | Chưa đạt; chỉ synthetic test path đã kiểm causal propagation. |
| Regression tests | 63 local tests passed; CI run 43841700612 cũng passed tests và compile. |
| GitHub milestone / CI | Protocol/code-wiring commit `1ec2c1b649901873a12cb43dba703bf7a723a411` đã xác minh trên branch và Actions thành công; actual case experiment vẫn pending. |

Để tiếp tục phần thực nghiệm: một reviewer cần hoàn thành source-only worksheet trong [P2_BLIND_ANNOTATION.md](P2_BLIND_ANNOTATION.md), khóa JSON trong app; sau đó gọi `qwen3:4b`, rồi cung cấp review riêng theo [P2_MODEL_REVIEW.md](P2_MODEL_REVIEW.md). Thực nghiệm này vẫn không tạo gold labels nếu thiếu reviewer thứ hai và adjudication.
