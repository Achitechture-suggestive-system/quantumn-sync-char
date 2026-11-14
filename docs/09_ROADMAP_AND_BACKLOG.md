# 09 — Lộ trình và backlog

## P0 — baseline demo (đã hoàn tất trong phạm vi MVP)

- Ứng dụng Streamlit, fixture offline, JSON cấu trúc.
- Pipeline báo cáo mười bước.
- Ollama local tùy chọn, schema/citation checks, không tự phê duyệt.
- Liệt kê partitions cho sáu responsibility, hard conflicts, ties và quantum boundaries đề xuất.
- Sync/Async hypotheses; QAME allocation không giả measurement.
- Human review, sửa responsibility/constraint, impact preview, chạy lại, snapshots/diff/export.
- P0: 30 tests pass; compileall, AppTest, localhost smoke ghi trong docs/verification/P0_BASELINE_VERIFICATION.md.
- Commit baseline 3d517b1… trên main, tag p0-demo-2026-11-14; push xác minh.

P0 hoàn tất nghĩa là luồng phần mềm cục bộ có thể chạy lại trong scope đã nêu, không phải kiến trúc được duyệt.

## P1 — semantic validation và truy vết (đã hoàn tất trên feature branch; chờ CI)

Làm ở feat/p1-semantic-validation để giữ main ổn định:

1. Oracle phân hoạch độc lập cho n=6 xác nhận 203/10/0/5, không import generator private của pipeline.
2. Negative tests bắt citation thiếu/sai, evidence PRESENT không support, source không có trong package, unknown responsibility constraint và JSON lỗi/UTF-8/type; regression cover conflict và human correction.
3. Graph trace các nguồn fixture/LLM, evidence, constraints, partitions, quanta, interactions, QAME, quyết định và revision; structural checks không được gắn nhãn semantic verification.
4. Fixture requirements/workflow nhỏ mang nhãn SYNTHETIC_TEST_FIXTURE; hiện dùng kiểm schema/source-span/proposal-interface, không phải một demo pipeline end-to-end.
5. Worksheet hướng dẫn annotation cho nghiên cứu tương lai; chưa có nhãn chuyên gia hay precision/recall.
6. Human correction làm mới traceability và impact preview; pipeline vẫn tính lại toàn bộ, chưa có incremental execution.

Exit gate: 44 tests pass; compileall và AppTest pass; Ollama run có exact-span validation nhưng proposals vẫn review-required. Chi tiết trong docs/verification/P1_SEMANTIC_EVALUATION.md. Việc push/CI vẫn là milestone kế tiếp; không tự merge.

## CI và sau demo

- Workflow `.github/workflows/python-ci.yml` đã thêm trên feature branch: Ubuntu 24.04 và Python 3.13, pytest và compileall, không cần Ollama/model/secret. Hai lần chạy đầu thành công; lần chạy với runner cố định đang được xác nhận.
- Trước demo 19/11: chạy lại offline, tests và AppTest; nếu Ollama sẵn sàng thì ghi model/prompt/span checks; diễn tập export.
- Sau demo: thêm nhiều case và labels độc lập, thỏa thuận giữa reviewers và metric semantic; chỉ đo quality ở môi trường đại diện.
- Style Selection/Evaluation, OCR/PDF/BPMN tổng quát, RAG lớn và deployment nằm ngoài phạm vi.
