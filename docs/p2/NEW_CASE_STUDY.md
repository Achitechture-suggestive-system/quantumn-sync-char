# P2 — Ca nghiên cứu Tutor Support mới

## Phạm vi và nhãn nguồn

`TUTOR-SUPPORT-P2-01` là ca requirements nhỏ do nhóm dự án chuẩn bị riêng cho P2; không dùng mã nguồn PetClinic hay fixture P0. Đây là dữ liệu minh họa đã chuẩn bị, không phải hệ thống production hoặc kết quả chuyên gia. Nguồn được đóng gói theo từng ID trong `eqcr/tutor_support.py`.

| ID | Yêu cầu chức năng | Source ID |
|---|---|---|
| FR-01 | Learner tìm tutor theo môn học và thời gian rảnh. | `TUTOR-REQ-FR-01` |
| FR-02 | Learner xem hồ sơ, môn học và thời gian tutor đăng. | `TUTOR-REQ-FR-02` |
| FR-03 | Tutor đăng và cập nhật lịch rảnh hằng tuần. | `TUTOR-REQ-FR-03` |
| FR-04 | Learner yêu cầu một buổi học ở khung giờ đang rảnh. | `TUTOR-REQ-FR-04` |
| FR-05 | Tutor chấp nhận hoặc từ chối yêu cầu buổi học đang chờ. | `TUTOR-REQ-FR-05` |
| FR-06 | Learner nhận thông báo khi tutor chấp nhận hoặc từ chối. | `TUTOR-REQ-FR-06` |

Workflow tách thành các hoạt động có source ID riêng: `WF-01` tìm tutor, `WF-02` xem hồ sơ/chọn giờ, `WF-03` gửi yêu cầu và tutor quyết định, `WF-04` learner nhận thông báo. Workflow được chuyển vào model như ngữ cảnh, nhưng schema trích xuất hiện chỉ cho phép citation FR; không được ghi workflow ID như bằng chứng citation của proposal.

| Scenario | Nguồn | Liên kết FR | Target | Trạng thái |
|---|---|---|---|---|
| `SC-REQUEST-ACK` — xác nhận yêu cầu buổi học | Source ID cùng tên | FR-04, FR-05 | p95 ≤ 2 giây tại 50 yêu cầu/phút | `NOT_MEASURED` |
| `SC-DECISION-NOTICE` — thông báo quyết định tutor | Source ID cùng tên | FR-05, FR-06 | ≥99% thông báo trong 30 giây, cửa sổ 24 giờ | `NOT_MEASURED` |

Scenario links là khai báo của bộ dữ liệu chuẩn bị; chúng cấp nguồn cho interaction/quality allocation. Chúng không phải phát hiện do Ollama hoặc reviewer tạo.

## Provenance

- **Source requirement / prepared fixture:** FR, workflow và quality scenario ở trên cùng exact source span.
- **LLM proposal:** Chỉ các giá trị được ghi riêng trong `LLM_EXTRACTION_EVALUATION.md`; tất cả ở trạng thái `REVIEW_REQUIRED` trước review.
- **Deterministic transformation:** R1–R6 ánh xạ theo thứ tự requirement; interaction edges và Quality Profiles ánh xạ từ scenario link; Bell partition enumeration dùng Python cổ điển.
- **Architectural policy:** `P2-SOFT-LIFECYCLE-COHESION` chỉ biến evidence `same_workflow_lifecycle` được duyệt thành soft MUST_LINK với weight 1.0.
- **Human decision:** Chưa có quyết định của reviewer thật được ghi nhận. Worksheet vẫn để trống.
- **Prepared fixture:** Responsibility placeholders chỉ giúp kiểm tra schema; không phải dự đoán model hay kết luận thiết kế.

Không đổi fixture hoặc verified baseline P0 trên `main`.
