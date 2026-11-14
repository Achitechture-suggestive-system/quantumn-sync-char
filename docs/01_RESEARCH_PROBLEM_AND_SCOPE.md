# 01 — Bài toán nghiên cứu và phạm vi

## Mục tiêu

Khảo sát cách chuyển requirements chức năng/chất lượng, workflow và bằng chứng hiện có thành Architectural Quantum ứng viên có truy vết, giả thuyết tương tác và Quantum Quality Profiles để con người xem xét/chỉnh sửa.

Đây là MVP nghiên cứu cục bộ. Hệ thống không tự khuyến nghị kiến trúc cuối cùng, không chọn architectural style, không kiểm chứng hệ thống đã triển khai.

## Câu hỏi nghiên cứu

| Câu hỏi | Thao tác trong MVP | Bằng chứng đầu ra | Chưa trả lời |
|---|---|---|---|
| RQ1 — Decomposition | Nhóm responsibilities ứng viên theo policy tường minh như thế nào? | Set partitions, soft cost và Quantum groups suy ra. | Diễn giải có đúng không, nhóm có cohesion hay deploy độc lập không. |
| RQ2 — Interactions | Nên khảo sát contract Sync/Async nào giữa các nhóm? | Edge Pet → Visit UNRESOLVED và các lựa chọn có điều kiện, có citation. | Protocol đúng, consistency, latency, retry, idempotency, lỗi. |
| RQ3 — Quality | Gắn scenarios với responsibilities/quanta ra sao? | Quality Profiles giữ source target, metric đề xuất, trạng thái đo. | Target có đạt không; fixture không có benchmark hay kiến trúc chạy được. |
| RQ4 — Human revision | Thay đổi của người dùng cập nhật phụ thuộc nhưng giữ lý do thế nào? | Impact preview, decisions/revisions, snapshots, diff và revalidation. | Người review có đủ chuyên môn không; quyết định đúng về thực nghiệm không. |

## Đầu vào và đầu ra

eqcr/models.py định nghĩa package gồm raw_requirements, responsibilities, evidence, constraints. raw_requirements chứa case/context, FRs, workflows và scenarios; mỗi source reference giữ ID, quote và offsets. Demo hiện dùng đúng sáu responsibility R1–R6.

Nguồn đề xuất: fixture PRECOMPUTED trong eqcr/fixture.py; JSON do người dùng nhập; hoặc bundle từ Ollama cục bộ. Fixture chỉ là ví dụ requirements-only, không được trích từ mã nguồn PetClinic. run_pipeline trả raw_requirements, context, responsibilities, evidence, constraints, partitions, quanta, interactions, quality_profiles, decisions, revisions, validation_report và metadata. review_request ban đầu null; UI có thể bổ sung. Ollama, snapshots và export thêm artifacts ở tầng ứng dụng.

## Giả định và phần ngoài phạm vi

- Responsibilities fixture là dữ liệu đầu vào PRECOMPUTED, không do optimizer khám phá.
- H1/H2/H3 là what-if policies, không phải business facts.
- UNKNOWN khác với absent; SCOPED_ABSENT chỉ có nghĩa vắng mặt trong scope đã nêu.
- Candidate count, citation span, review approval và measurement là các khái niệm riêng.
- Chế độ offline với cùng input/revisions tạo kết quả và thứ tự xác định.

Ngoài phạm vi: Architecture Style Selection/Evaluation; ingestion PDF/BPMN/OCR tổng quát; RAG lớn, fine-tuning, multi-agent; đánh giá accuracy không có labels độc lập; load test/benchmark; bằng chứng consistency hoặc deployability.
