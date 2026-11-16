# P2 — Báo cáo validation

## Tóm tắt trạng thái

`feat/p1-semantic-validation` hiện có code path để nạp case Tutor Support, kiểm citation, chặn promotion nếu chưa có human decision, áp policy đã khai báo, chạy đủ 10 stage và tính lại downstream sau evidence correction. Local `qwen3:4b` đã chạy thật trên case mới. Live pipeline run đi qua đủ mười stage nhưng evidence model chưa được reviewer duyệt; vì vậy yêu cầu “optimizer consumes accepted evidence-derived constraints for the actual case” còn **chờ review**, không được báo PASS.

## Chạy và kiểm tra

| Kiểm tra | Kết quả |
|---|---|
| Existing regression tests + P2 tests | 54 passed (`.venv\Scripts\python.exe -m pytest -q`) |
| Compile | `compileall -q app.py eqcr tests` exit 0 |
| Local inference | `qwen3:4b`, prompt v6; final pipeline input SHA-256 `41af28d651927cc1229cd2361b92b1dcda8fc397f31440d4f40c77d0a324289b`; prior same-hash calls differed |
| Live Tutor candidate | 10 bước đã chạy; structural traceability `PASS`; overall `REVIEW_REQUIRED` |
| Live optimizer (chưa human review) | 203 enumerated / 203 feasible / 203 optimal; J=0; derived evidence constraints = 0 |
| Test-only reviewed policy path | Constraint được tạo đúng evidence ID; 203 enumerated; 52 soft-optimal; correction đổi selected group và interaction mapping |
| Hard constraint feasibility | Test-only path không khai báo hard constraint; exhaustive partitions thỏa các hard constraints đang bật |
| Semantic metric | Không báo cáo; chưa có independent reference labels/adjudication |
| GitHub push/CI | Đạt cho milestone code/docs này; branch ref khớp SHA `4bbdb03d419ab6b556e3447de0b2130dd3f95fdb`; GitHub Actions run `43818037929` thành công, test và compile đều pass. Chi tiết tại `docs/development/GITHUB_PUBLISH_LOG.md`. |

## Acceptance matrix

| Tiêu chí | Trạng thái | Bằng chứng / phần còn thiếu |
|---|---|---|
| Case không phải PetClinic; FR, workflow, ≥2 scenarios có source ID | Đạt | `NEW_CASE_STUDY.md`, exact source span tests |
| Ollama inference thật | Đạt | `LLM_EXTRACTION_EVALUATION.md`; local `qwen3:4b` |
| Citation, unsupported/ambiguous/duplicate review | Một phần | Citation IDs/span pass; E1 self-relation và B1 unsupported rationale; duplicate không quan sát trong mẫu nhỏ |
| Worksheet độc lập, không fabricated labels | Đạt như template; chưa điền | `HUMAN_REVIEW_WORKSHEET.md` |
| Human approval/correction trước promotion | Code/test đạt; case thật chờ | `apply_tutor_human_review` yêu cầu quyết định cụ thể; chưa có reviewer thật |
| Optimizer consumes evidence-derived constraints | Test-only đã chứng minh; case thật chờ | Live run hiện có 0 derived constraints vì chưa review |
| Tạo candidate, interaction, quality outputs | Đạt cấu trúc | Live run có 6 quanta, 2 edges, 2 profiles; interaction unresolved, quality NOT_MEASURED |
| Human revision và before/after thật | Test-only đã chứng minh; case thật chờ | Unit test pass; chưa có accepted case evidence để sửa |
| Regression tests | Đạt cục bộ | 54 passed; CI sau push chưa xác minh |
| Giữ P0 baseline/main | Đạt theo checkout | Chỉ sửa feature branch; chưa có thay đổi trên main |

Đây là báo cáo trạng thái hiện tại, không phải tuyên bố hoàn tất P2. Cần reviewer hoàn thành worksheet rồi mới có thể tạo case artifacts được gắn `APPROVED` và hoàn tất revision experiment thật.
