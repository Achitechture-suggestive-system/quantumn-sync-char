# P2 — Worksheet annotation độc lập và review proposal

## Hướng dẫn

Reviewer độc lập nên hoàn thành **Phần A** chỉ từ FR/WF/scenario nguồn, lưu bản và ghi giờ hoàn thành trước khi mở bảng model ở `LLM_EXTRACTION_EVALUATION.md`. Không dùng proposal model để điền nhãn độc lập. Đây là worksheet trống; agent chưa tự điền hoặc tạo expert labels.

Đối với mỗi FR, ghi một responsibility interpretation, workflow mapping nếu có nguồn hỗ trợ, citation IDs và rationale. Có thể ghi `UNRESOLVED`; không cần ép mọi FR thành một architecture boundary. Với relation, ghi `PRESENT`, `UNKNOWN`, hoặc `SCOPED_ABSENT` theo evidence; không coi citation resolve là semantic approval.

## Phần A — annotation độc lập, chỉ xem nguồn

| FR | Nguồn tóm tắt | Responsibility được reviewer diễn giải | Activity / operation | Workflow IDs | Source IDs | Rationale | Reviewer / thời điểm |
|---|---|---|---|---|---|---|---|
| FR-01 | Search tutor theo subject và available time |  |  |  |  |  |  |
| FR-02 | View tutor profile, subject và availability |  |  |  |  |  |  |
| FR-03 | Tutor publish/update weekly slots |  |  |  |  |  |  |
| FR-04 | Learner request buổi học ở slot available |  |  |  |  |  |  |
| FR-05 | Tutor accept/decline pending request |  |  |  |  |  |  |
| FR-06 | Learner receives notice of decision |  |  |  |  |  |  |

## Phần B — relation annotation độc lập

| Subject FR | Predicate | Object FR | Typed status | Source IDs | Rationale | Reviewer / thời điểm |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |

Ghi `UNKNOWN` nếu text không đủ để xác nhận hoặc phủ định relation. Không dùng `SCOPED_ABSENT` nếu input chỉ im lặng.

## Phần C — quyết định sau khi mở model output

Model output: P1–P6, E1 và B1 được liệt kê trong `LLM_EXTRACTION_EVALUATION.md`. Mỗi quyết định cần actor, source/session, reason và thời điểm. Với P1–P6, chọn `APPROVE` hoặc `CORRECT`; CORRECT phải cung cấp cả name, activity và operation. Có thể gán workflow IDs hoặc để unresolved.

| Proposal | Decision: APPROVE/CORRECT/REJECT | Corrected value(s), nếu có | Workflow IDs | Reason | Reviewer / source / time |
|---|---|---|---|---|---|
| P1 / FR-01 |  |  |  |  |  |
| P2 / FR-02 |  |  |  |  |  |
| P3 / FR-03 |  |  |  |  |  |
| P4 / FR-04 |  |  |  |  |  |
| P5 / FR-05 |  |  |  |  |  |
| P6 / FR-06 |  |  |  |  |  |
| E1 |  | Corrected subject, predicate, object, status and source FRs nếu có | N/A |  |  |
| B1 |  | Corrected requirement group / rationale nếu có | N/A |  |  |

E1 tự nối FR-06 với FR-06. Dù citation resolve, relation có thể không có ý nghĩa kiến trúc; reviewer có thể reject, correct thành relation có endpoint/source phù hợp, hoặc để unresolved. Không cần ép approve.

## Cách áp dụng review trong ứng dụng

1. Chọn **Load Tutor Support P2 case**, kiểm tra Ollama và chạy model `qwen3:4b`.
2. Chọn dùng proposals làm candidate rồi chạy pipeline; mọi proposal vẫn chưa được duyệt.
3. Trong tab **Human Review & Validation**, sửa JSON review template. P1–P6 cần `APPROVE` hoặc `CORRECT`; E1/B1 cần một quyết định `APPROVE`, `CORRECT` hoặc `REJECT`. Mỗi row phải có `reason`, `source`, `actor`.
4. `CORRECT` responsibility cần `correction` gồm `name`, `activity`, `operation`. `CORRECT` evidence cần subject/predicate/object, typed status, source FR IDs bao phủ cả hai endpoints và rationale. Boundary correction chỉ được ghi là review hypothesis, không làm input optimizer.
5. **Apply human review & recompute P2 case** ghi decisions và chạy lại mười stage. Chỉ evidence PRESENT, reviewer-approved, citations hợp lệ và khớp policy mới sinh constraint.
6. Để kiểm tra before/after, dùng form **Revise an approved evidence relation**, nhập lại hai endpoint/source citations và reason rồi revalidate.

Ví dụ cấu trúc correction dưới đây chỉ minh họa field names; không phải annotation hoặc đề xuất ngữ nghĩa:

```json
{
  "proposal_id": "E1",
  "action": "CORRECT",
  "reason": "Reviewer explanation",
  "source": "Review session ID",
  "actor": "Reviewer ID",
  "correction": {
    "subject_requirement_id": "FR-05",
    "predicate": "reviewer-selected predicate",
    "object_requirement_id": "FR-06",
    "status": "PRESENT",
    "source_requirement_ids": ["FR-05", "FR-06"],
    "rationale": "Reviewer explanation tied to the cited source text"
  }
}
```

## Trạng thái worksheet

Chưa có actor, annotation, adjudication hay decision thật được ghi nhận. Test unit dùng `test-reviewer` chỉ xác minh code path; đó không phải dữ liệu worksheet hoặc kết quả semantic của Tutor Support.
