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

Ngày 14/11/2026: regression suite 30 tests pass; AppTest không exception; Streamlit localhost health/root HTTP 200; fixture Bell(6)=203, mười co-optima J=0. H4 MUST_LINK(R4,R6) đối nghịch H3 tạo INFEASIBLE/0; tắt H3 tạo 5. [Báo cáo P0](verification/P0_BASELINE_VERIFICATION.md) ghi lệnh/môi trường/phạm vi.

P0 so sánh bằng chính code enumerator, chưa có oracle độc lập. Không tuyên bố cross-validation thuật toán trước khi P1 bổ sung oracle riêng.

## Giới hạn khoa học

Input requirements-only; responsibilities và policies có sẵn hoặc do model đề xuất; không có expert labels độc lập. H1/H2/H3 là giả định what-if. Fixture không có soft constraints nên 10 ứng viên hòa ở J=0. Pet–Visit thiếu protocol, contract, consistency và quality target; edge UNRESOLVED, options PROPOSED_NOT_VERIFIED. Owner Search target p95 ≤ 250 ms @ 300 requests/s nhưng không load test, nên NOT_MEASURED.

Không có bằng chứng cho semantic accuracy/F1, architectural quality, deployability, operability, security hoặc generalization.
