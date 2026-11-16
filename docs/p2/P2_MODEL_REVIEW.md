# P2 — Worksheet review proposal sau blind checkpoint

## Điều kiện sử dụng

Chỉ dùng biểu mẫu này sau khi source-only worksheet đã được khóa, tải xuống và lưu. Hoạt động này không thay thế annotation độc lập. Không chỉnh sửa hoặc xóa bản annotation trước model để khớp với output.

Protocol đang ở trạng thái `ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`. Quyết định của một reviewer trong app là quyết định review có provenance, không tự động là nhãn chuyên gia hoặc gold label.

## Responsibility proposals

Mỗi proposal hiện có phải nhận một quyết định. `CORRECT` có thể tạo 1..N corrected responsibilities; `REJECT` hoặc `DEFER` cho phép proposal không đóng góp role nào. FR có thể nhận 0..N roles và role có thể trỏ đến nhiều FR. FR không được bao phủ phải tiếp tục `UNRESOLVED`.

| Proposal ID | Action: APPROVE / CORRECT / REJECT / DEFER | Corrected responsibility object(s), nếu có | FR IDs | Workflow IDs | Rationale | Reviewer / source / thời điểm |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Responsibility correction/addition cần `name`, `activity`, `operation`, một hoặc nhiều `requirement_ids`, lý do review và actor. Workflow mapping có thể để trống khi unresolved. Nguồn requirement được ứng dụng resolve lại từ FR IDs; reviewer không được tạo source span mới.

## Relation proposals

Mỗi relation proposal nhận một quyết định `APPROVE`, `CORRECT`, `REJECT` hoặc `DEFER`. `APPROVE` chỉ hợp lệ nếu citation cấu trúc đạt và predicate thuộc registry. Nếu `PRESENT`, nguồn phải bao phủ cả endpoints. Proposal ngoài predicate registry cần `CORRECT`, `REJECT` hoặc `DEFER`.

| Proposal ID | Action | Corrected subject / predicate / object / status | Source FR IDs | Architecture implication | Named responsibility pairs | Hai rationale riêng (relation / architecture) | Reviewer / source / thời điểm |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

Giá trị kiến trúc: `NONE`, `UNRESOLVED`, `COLOCATE_CANDIDATE`, `SEPARATE_CANDIDATE`. Predicate `BUSINESS_PRECEDES` chỉ có thể giữ implication `NONE` hoặc `UNRESOLVED`; nó không sinh optimizer constraint. Hai predicate kiến trúc chỉ có thể tạo soft candidate policy khi reviewer nêu implication phù hợp, rationale riêng và các cặp responsibility cụ thể khớp với endpoint FR.

## Boundary hypotheses

| Proposal ID | Action: APPROVE / CORRECT / REJECT / DEFER | Requirement group | Cited source FRs | Rationale | Reviewer / source / thời điểm |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Boundary hypotheses không đi vào optimizer trong P2; review của chúng chỉ được lưu như quyết định về hypothesis.

## Adjudication và provenance

Mỗi annotator ghi riêng action, rationale, ID phiên, actor tự khai báo và thời điểm. Không hòa giải bất đồng trong khi các đánh giá độc lập còn đang diễn ra. Quy trình đề xuất hiện tại: hai reviewer đánh giá riêng; sau khi cả hai đã khóa bản, một adjudicator thứ ba ghi bất đồng, quyết định cuối cùng và rationale. Nếu thiếu hai bản độc lập hoặc adjudication, kết quả phải giữ `UNRESOLVED`; không gắn nhãn gold.

Không sao chép nội dung bảng này vào source-only annotation. App review JSON là nơi nhập các disposition có thể tác động pipeline; quyết định thật chưa được ghi trong checkout hiện tại.
