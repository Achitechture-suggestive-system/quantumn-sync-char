# P2 — Thí nghiệm sửa evidence và chạy lại

## Quy trình case thật

Case thật đang chờ reviewer hoàn tất Phần A/C trong `HUMAN_REVIEW_WORKSHEET.md`. Sau khi có quyết định, lưu baseline artifacts; nếu E1 được sửa thành `same_workflow_lifecycle` với hai endpoint/source hợp lệ, policy soft sẽ sinh constraint gắn `evidence_ids`. Reviewer có thể dùng `apply_evidence_relation_edit` để chuyển relation sang một cặp FR khác, rồi chạy lại pipeline. Decision ghi old/new, actor, source, reason; revision liệt kê downstream artifacts invalidated.

Nếu không evidence nào được chấp nhận theo policy, constraint list rỗng và output optimizer không đổi. Đây là kết quả cần ghi lại như unchanged do không có accepted relation khớp policy.

## Bằng chứng test-only về cơ chế propagation

Unit test P2 dùng proposal bundle và review decisions **chỉ để kiểm tra implementation**, không phải inference hoặc annotation của case thật:

| Run | Evidence đầu vào | Derived optimizer constraint | Selected groups (R IDs) | Interaction membership |
|---|---|---|---|---|
| Trước | Test-only accepted `same_workflow_lifecycle(FR-05, FR-06)` | Soft MUST_LINK(R5,R6), policy P2 | R5/R6 cùng nhóm; các R khác đơn lẻ | SC-DECISION-NOTICE cùng quantum; SC-REQUEST-ACK tách |
| Sau correction | Test-only human edit relation sang FR-04/FR-05 | Soft MUST_LINK(R4,R5), cùng policy | R4/R5 cùng nhóm; các R khác đơn lẻ | SC-REQUEST-ACK cùng quantum; SC-DECISION-NOTICE tách |

Trong cả hai test run, 203 partitions được liệt kê; các hard constraint đều thỏa (không có hard constraint nào khai báo), minimum objective là 0, và 52 candidates đạt cost 0. Khác biệt được giải thích trực tiếp bởi evidence ID/pair đã sửa; interaction `same_quantum` và Quality Profile quantum mapping được tính lại. Đây là kiểm thử deterministic bằng dữ liệu test-only, không phải kết quả case study hoặc đánh giá semantics.

## Trạng thái

Thí nghiệm bắt buộc trên accepted LLM evidence với reviewer thật chưa chạy. Không gắn nhãn human correction cho test harness.
