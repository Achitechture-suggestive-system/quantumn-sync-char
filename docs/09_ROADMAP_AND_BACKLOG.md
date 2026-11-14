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

## P1 — semantic validation và truy vết (đang thực hiện)

Làm ở feat/p1-semantic-validation để giữ main ổn định:

1. Thêm oracle phân hoạch độc lập cho n=6, kiểm 203/10/0/5 mà không import private algorithm của pipeline.
2. Thêm negative tests cho source citation thiếu/sai, evidence không có support, constraint conflict, JSON lỗi, Ollama không chạy và human revision đổi downstream.
3. Truy vết nguồn chuyển đổi fixture/LLM/rule/human/optimizer từ FR/workflow đến proposal/evidence/constraint/partition.
4. Tạo fixture requirements/workflow nhỏ, nhãn SYNTHETIC_TEST_FIXTURE; không trình bày như nghiên cứu thực tế độc lập.
5. Tạo worksheet cho nhãn người đánh giá tương lai; proposal vẫn REVIEW_REQUIRED. Không bịa precision/recall.
6. Kiểm tra vùng phụ thuộc và snapshots khi có correction; ghi rõ pipeline vẫn tính lại toàn bộ nếu chưa implement incremental.

Exit gate: tests pass; docs/verification/P1_SEMANTIC_EVALUATION.md ghi lệnh, ví dụ, kết quả và giới hạn. Push branch, xác minh SHA/CI; không tự merge.

## CI và sau demo

- Thêm workflow Python 3.13 chạy pytest/compileall, không cần Ollama/secret. Không giả lập model call.
- Trước demo 19/11: chạy lại offline, tests và AppTest; nếu Ollama sẵn sàng thì ghi model/prompt/span checks; diễn tập export.
- Sau demo: thêm nhiều case và labels độc lập, thỏa thuận giữa reviewers và metric semantic; chỉ đo quality ở môi trường đại diện.
- Style Selection/Evaluation, OCR/PDF/BPMN tổng quát, RAG lớn và deployment nằm ngoài phạm vi.
