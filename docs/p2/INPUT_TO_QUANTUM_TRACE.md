# P2 — Audit luồng Ollama → Evidence → Constraint → Quantum

## Audit trước thay đổi

1. `app.py` gọi `propose_responsibilities` và giữ JSON Ollama trong session. `eqcr/ollama.py` giải citation FR về source span chính xác, nhưng gắn tất cả proposal với `REVIEW_REQUIRED`.
2. Nút candidate run gọi `apply_proposals_to_fixture`. Gate `can_apply_to_fixture` chỉ kiểm tra đủ sáu FR, citation và ID; nó không chấp nhận semantics.
3. Bundle evidence/boundary được hiển thị riêng, không được chuyển thành evidence/constraint đầu vào. Candidate fixture vẫn giữ constraints của fixture gốc.
4. `eqcr/pipeline.py` lấy `fixture["constraints"]` hoặc `constraints_override` làm toàn bộ optimizer input. Vì vậy Ollama responsibility text có thể đi vào artifacts; evidence proposal không có đường nhân quả tới optimizer.
5. Trước P2, optimizer còn có tie-break R1–R6 nằm trong code; interaction builder chọn cặp R4/R6; quality builder chọn FR-01/FR-04/FR-06. Các output này không khái quát cho Tutor Support.

## Thay đổi P2

- Scenario khai báo `related_requirement_ids`, citation source cho interaction và quality metadata. Pipeline ánh xạ từ requirement ID sang responsibility ID, không chọn ID PetClinic cố định.
- Constraint policy được khai báo trong case. Policy chỉ tạo constraint khi evidence có `PRESENT`, reviewer đặt `APPROVED`, hai responsibility endpoint cũng được reviewer duyệt, source span giải được chính xác và citation bao phủ hai endpoint.
- Output policy là soft constraint có `evidence_ids`, source refs, rationale và `origin=ARCHITECTURAL_POLICY`. Evidence chưa review, bị reject, UNKNOWN, thiếu citation endpoint hoặc citation sai không tạo constraint.
- `apply_tutor_human_review` ghi riêng quyết định approve/correct/reject cùng actor, source và reason. `apply_evidence_relation_edit` sửa evidence đã duyệt, ghi impact trước revalidation rồi để pipeline tính lại constraint, partition, quantum, interaction, quality và traceability.
- PetClinic chọn partition hiển thị qua cấu hình fixture; Tutor case dùng tie-break `MAXIMUM_GROUPS`. Tie-break chỉ chọn một candidate để hiển thị, không thay objective.

## Luồng thực tế đã chạy với local Ollama

Model `qwen3:4b`, prompt `requirements-context-responsibility-evidence-boundary-v6`, temperature 0; input hash `41af28d651927cc1229cd2361b92b1dcda8fc397f31440d4f40c77d0a324289b`. Lần chạy pipeline dùng output inference ghi trong báo cáo model.

| Bước | Input/output | Provenance và trạng thái thực tế |
|---|---|---|
| 01 Context Understanding | Sáu FR, bốn workflow, hai scenario; exact span check. | Source requirement + prepared fixture; `PASS`. |
| 02 Responsibility Identification | P1–P6 do qwen đề xuất; tất cả FR citation resolve. | LLM proposal; `REVIEW_REQUIRED`. |
| 03 Evidence Modeling | E1 (`FR-06 is supported by FR-06`) được giữ ở proposal artifact; chưa đưa vào evidence đã duyệt. | LLM proposal; `REVIEW_REQUIRED`; self-relation không tạo optimizer constraint. |
| 04 Constraint & Quality Reasoning | Không có evidence decision người thật nên policy chưa sinh constraint. | Architectural policy chưa kích hoạt; `PASS` về cấu trúc, không phải xác nhận ngữ nghĩa. |
| 05 Candidate Optimization | 203 enumerated, 203 feasible, 203 optimal, J=0. | Deterministic transformation; không nhận constraint từ E1. |
| 06 Quantum Boundary Refinement | Sáu nhóm đơn, R1–R6; candidate display tie-break. | Deterministic transformation từ partition và proposal names. |
| 07 Interaction Design | Hai edge scenario-driven; cả hai `INSUFFICIENT_EVIDENCE`, Sync/Async chưa chọn. | Deterministic pattern hypotheses + source requirement. |
| 08 Quality Allocation | Hai profile được gắn với scenario và FR; cả hai `NOT_MEASURED`. | Deterministic transformation từ prepared scenario; không có PASS chất lượng. |
| 09 Human-in-the-Loop Review | Chưa có reviewer thật. | `REVIEW_REQUIRED`; worksheet chưa điền. |
| 10 Verification & Iteration | Traceability graph cấu trúc `PASS`; pipeline report `REVIEW_REQUIRED`. | Deterministic structural checks; không chứng minh semantic entailment. |

Pipeline đã thực thi đủ mười bước cho case mới với proposal thật. Tuy vậy, lần chạy này chưa đạt acceptance “optimizer dùng accepted evidence-derived constraint” vì chưa có human decision. Unit tests xác nhận gate và propagation bằng dữ liệu test-only; không dùng test decision làm nhãn cho case thật.

## Đường nhân quả sau khi reviewer phản hồi

`source requirement → Ollama proposal → citation validation → human approve/correct → typed evidence → explicit soft policy → optimizer cost/optima → selected partition → quanta/interactions/quality → traceability`.

Nếu reviewer reject E1 hoặc sửa predicate không khớp policy, output optimizer vẫn giữ nguyên 203 optima; đó là kết quả hợp lệ và phải ghi “unchanged because no accepted evidence matched policy,” không được tự thêm constraint.
