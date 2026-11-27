# P2 — Ca nghiên cứu Tutor Support mới

## Phạm vi và trạng thái dữ liệu

`TUTOR-SUPPORT-P2-01` là một case requirements nhỏ, nguyên bản, được chuẩn bị riêng cho P2; không dùng mã nguồn hoặc fixture PetClinic. Đây là `PREPARED_FIXTURE`, không phải yêu cầu production, annotation chuyên gia hay bằng chứng triển khai. Nội dung và exact source span được định nghĩa trong `eqcr/tutor_support.py`.

| ID | Yêu cầu chức năng | Source ID |
|---|---|---|
| FR-01 | Learner tìm tutor theo môn học và thời gian rảnh. | `TUTOR-REQ-FR-01` |
| FR-02 | Learner xem hồ sơ, môn học và thời gian tutor đăng. | `TUTOR-REQ-FR-02` |
| FR-03 | Tutor đăng và cập nhật lịch rảnh hằng tuần. | `TUTOR-REQ-FR-03` |
| FR-04 | Learner yêu cầu một buổi học ở khung giờ đang rảnh. | `TUTOR-REQ-FR-04` |
| FR-05 | Tutor chấp nhận hoặc từ chối yêu cầu buổi học đang chờ. | `TUTOR-REQ-FR-05` |
| FR-06 | Learner nhận thông báo khi tutor chấp nhận hoặc từ chối. | `TUTOR-REQ-FR-06` |

Workflow có source ID riêng: `WF-01` tìm tutor; `WF-02` xem hồ sơ/chọn giờ; `WF-03` gửi yêu cầu và tutor quyết định; `WF-04` learner nhận thông báo. Scenario links là khai báo trong prepared case, không phải phát hiện từ Ollama hoặc reviewer.

| Scenario | Source ID | FR liên quan | Target | Trạng thái đo |
|---|---|---|---|---|
| `SC-REQUEST-ACK` — xác nhận yêu cầu buổi học | `SC-REQUEST-ACK` | FR-04, FR-05 | p95 ≤ 2 giây tại 50 yêu cầu/phút | `NOT_MEASURED` |
| `SC-DECISION-NOTICE` — thông báo quyết định tutor | `SC-DECISION-NOTICE` | FR-05, FR-06 | ≥99% thông báo trong 30 giây, cửa sổ 24 giờ | `NOT_MEASURED` |

## Provenance của các đầu ra

| Đầu ra | Provenance | Cách diễn giải được phép |
|---|---|---|
| FR, WF, scenario và source spans | Prepared fixture / source requirement | Dùng làm input có ID; chưa phải dữ liệu production. |
| Responsibility/evidence/boundary proposal | Local LLM proposal | Chưa xác nhận nghĩa; chỉ thành candidate sau citation validation. |
| Source-only annotation và relation statuses | Human decision, nếu reviewer điền và khóa | Ghi nhận annotation trước khi mở proposal; chưa là gold label khi thiếu người độc lập và adjudication. |
| R IDs, exact citation resolution, interaction edges, quality profiles | Deterministic transformation | Có thể truy về source/proposal/reviewer decision; không tự xác nhận nghĩa. |
| Evidence-derived constraint | Architectural policy sau human review | Soft candidate preference, chỉ tạo khi evidence, implication và role pair được duyệt tường minh. |
| Placeholder responsibilities trong template | Prepared fixture | Chỉ để giữ schema; không được trình bày là model output hoặc human label. |

Chính sách P2 dùng `SHARES_STATE_OR_INVARIANT` → soft `MUST_LINK` chỉ khi reviewer tách riêng quyết định `COLOCATE_CANDIDATE`; `REQUIRES_INDEPENDENT_CHANGE` → soft `CANNOT_LINK` chỉ khi reviewer tách riêng `SEPARATE_CANDIDATE`. Predicate workflow `BUSINESS_PRECEDES` chỉ biểu diễn thứ tự nghiệp vụ và không bao giờ tự sinh constraint kiến trúc. Các policy này là quyết định thiết kế có thể đảo ngược, không phải quy tắc của Tutor Support.

## Tình trạng nghiên cứu

Một số output Ollama cũ được tạo trước khi có blind checkpoint. Chúng được giữ lại như quan sát exploratory, không được dùng làm label độc lập hay số liệu semantic. Từ protocol P2 hiện tại, UI buộc reviewer khóa source-only annotation với timestamp/hash trước khi cho phép gọi local model. Chưa có reviewer thật hoàn tất checkpoint trong repo này; do đó case chưa có kết quả inference hậu-blind hoặc review thật.

Không thay fixture hoặc verified baseline P0 trên `main`. Thuật toán phân hoạch là enumerator Python cổ điển; “Quantum” là tên đơn vị candidate, không phải quantum computing hoặc production architecture.
