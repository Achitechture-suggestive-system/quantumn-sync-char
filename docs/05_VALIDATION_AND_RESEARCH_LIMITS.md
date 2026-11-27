# 05 — Validation và giới hạn nghiên cứu

## Kết luận được phép từ mỗi gate

| Gate | Có thể kết luận | Không thể kết luận |
|---|---|---|
| Pydantic schema | Kiểu/trường, IDs duy nhất, trường lạ, giới hạn dữ liệu | Đúng nghĩa, đủ requirements, chất lượng kiến trúc. |
| Source span | Source ID, offsets và quote khớp input | Quote hỗ trợ được diễn giải/trách nhiệm mà model gán. |
| Evidence typing | Giữ PRESENT/SCOPED_ABSENT/UNKNOWN riêng, lưu provenance/review | Runtime coupling, consistency, causality nếu không có dữ liệu đó. |
| Constraint validator | IDs/refs tồn tại, phát hiện hard conflict | What-if policy được business xác nhận. |
| Enumerator | Tập phân hoạch được xét, hard constraints và minimum cost theo objective cấu hình | Objective mô hình hóa đúng lợi ích kiến trúc. |
| Quantum assignment | Responsibility xuất hiện đúng một lần trong nhóm hiển thị | Ownership, release, deployment, autonomy hay operability. |
| Interaction trace | Options có references và thiếu sót được giữ lại | Sync/Async đúng, contract, consistency, failure handling. |
| QAME allocation | Scenario gắn với FR/responsibility/quantum và có trạng thái đo | Target đạt, metric calibrated hay quality PASS. |
| Human review | Decision, actor, reason và nguồn được ghi lại | Sự thật kỹ thuật hay xác minh độc lập. |
| Traceability graph | Node/edge IDs, endpoint references, recorded spans, review-state và candidate membership nhất quán | Citation hỗ trợ ngữ nghĩa, policy đúng, architecture tốt hay production-ready. |
| Empirical quality | Chưa triển khai trong case này | Không thể nêu benchmark hay hiệu năng đạt. |

## Các status không thể thay thế nhau

- SOURCE_BACKED là provenance/citation đã ánh xạ; không chứng minh nội dung diễn giải.
- REVIEW_REQUIRED cho biết ý nghĩa còn chờ review.
- APPROVED/REJECTED/DEFERRED là decision của người dùng; không tạo measurement/deployment evidence.
- PASS chỉ áp dụng cho assertion cụ thể.
- INFEASIBLE nghĩa là không có partition nào thỏa hard constraints đã cấu hình.
- NOT_MEASURED và INSUFFICIENT_EVIDENCE biểu thị thiếu phép đo/bằng chứng, không phải pass/fail giả.
- UNKNOWN và UNRESOLVED không được âm thầm đổi thành false, null kết luận hoặc PASS.

## Kết quả P0 có thể tái hiện

Ngày 14/11/2026: P0 regression suite có 30 tests pass; trên nhánh P1, 44 tests pass, compileall pass và AppTest có 0 exception. Oracle độc lập dùng mọi phép gán nhãn rồi canonicalize blocks, không gọi generator restricted-growth của production: 203 partitions, 10 optima baseline; H4 tạo 0 feasible; tắt H3 còn 5 optimal. Chi tiết trong [P0 baseline](verification/P0_BASELINE_VERIFICATION.md) và [P1 semantic evaluation](verification/P1_SEMANTIC_EVALUATION.md).

## Giới hạn khoa học

Input requirements-only; responsibilities và policies có sẵn hoặc do model đề xuất; không có expert labels độc lập. H1/H2/H3 là giả định what-if. Fixture không có soft constraints nên 10 ứng viên hòa ở J=0. Pet–Visit thiếu protocol, contract, consistency và quality target; edge UNRESOLVED, options PROPOSED_NOT_VERIFIED. Owner Search target p95 ≤ 250 ms @ 300 requests/s nhưng không load test, nên NOT_MEASURED. Live Ollama `qwen3:4b` trên prompt v5 tạo sáu responsibility proposals, sáu normalized requirement references, một evidence proposal và một boundary hypothesis; span checks qua, mọi đề xuất còn REVIEW_REQUIRED. Đây không phải semantic evaluation.

Không có bằng chứng cho semantic accuracy/F1, architectural quality, deployability, operability, security hoặc generalization.
