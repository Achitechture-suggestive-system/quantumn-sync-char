# Trạng thái triển khai pipeline

**Cập nhật:** 14/11/2026. Mô tả chi tiết, có nguồn mã, ở [Pipeline 01–10](02_PIPELINE_01_TO_10.md).

| Năng lực | Trạng thái đã xác minh |
|---|---|
| Fixture offline/JSON cấu trúc | Chạy schema và source-span checks; semantics vẫn cần review. |
| Mười bước | run_pipeline tạo đủ mười bước trong validation report. |
| Ollama local | Proposal path có trong code; qwen3:4b đã cài. Baseline audit không chạy inference mới. |
| Constraint/optimizer | Bell(6)=203; mười co-optima J=0; hard conflict INFEASIBLE; sau correction có năm. |
| Quantum/interactions/QAME | Gán nhóm cấu trúc; Pet–Visit UNRESOLVED; Sync/Async hypotheses; Owner Search NOT_MEASURED; Pet–Visit INSUFFICIENT_EVIDENCE. |
| Human review/export | Review, chỉnh sửa, preview, tính lại toàn pipeline, snapshots/diff/export. |
| Giới hạn nghiên cứu | Gate cấu trúc; chưa có semantic accuracy, deployability, production quality hoặc load-test pass. |

Lệnh, phiên bản, đầu ra tại [P0 verification](verification/P0_BASELINE_VERIFICATION.md). P1 tiếp tục trên branch riêng; main giữ baseline demo.
