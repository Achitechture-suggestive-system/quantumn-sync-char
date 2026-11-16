# P2 — Worksheet annotation độc lập, chỉ xem source

## Mục đích và trạng thái

Worksheet này dành cho một người annotator đọc **chỉ requirements, workflow và quality scenarios** của Tutor Support. Hoàn thành, lưu và khóa nó trước khi mở bất kỳ output Ollama nào. Không có proposal, model name hay model rationale trong phần source-only. File này là mẫu trống; chưa có nhãn chuyên gia.

Trạng thái nghiên cứu hiện tại: `ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`. Một bản do một người điền có thể là annotation độc lập trước model, nhưng chưa tạo thành gold labels. Cần ít nhất hai annotator làm riêng và bước adjudication đã định trước để tạo reference set.

## Quy tắc cardinality

- Mỗi FR có thể được diễn giải bởi **0..N** responsibility annotations.
- Một responsibility annotation có thể liên kết **một hoặc nhiều FR**.
- FR có 0 annotation phải ghi trong `unresolved_requirement_ids`; không suy ra nhãn rỗng là “không có responsibility”.
- Không ép một FR thành một role hoặc một role cho mỗi FR.
- Ghi workflow mapping chỉ khi người annotator thấy quan hệ đó được hỗ trợ; citation source ID và rationale vẫn cần nêu rõ.

## Relation registry cố định

Ứng dụng tạo sẵn toàn bộ 60 dòng quan hệ có thứ tự trước annotation: 30 dòng có hướng `BUSINESS_PRECEDES` (mỗi cặp FR khác nhau có hai hướng) và 15 cặp không hướng cho mỗi predicate `SHARES_STATE_OR_INVARIANT` và `REQUIRES_INDEPENDENT_CHANGE`. Không thêm, xóa hoặc đổi endpoint/predicate trong registry.

Mỗi dòng bắt đầu ở `NOT_ANNOTATED`. Người annotator có thể đánh:

- `PRESENT`: relation được nội dung nguồn hỗ trợ; ghi source IDs và rationale. Với `PRESENT`, citations phải bao phủ cả hai FR endpoint.
- `UNKNOWN`: đã xem xét nhưng văn bản không đủ để xác định relation.
- `SCOPED_ABSENT`: chỉ dùng nếu package xác định rõ phạm vi nơi relation bị loại trừ; im lặng không phải absence.
- `NOT_ANNOTATED`: chưa đưa ra quyết định về dòng đó. Trạng thái này khác với `UNKNOWN`.

`BUSINESS_PRECEDES` chỉ là thứ tự nghiệp vụ và không kéo theo co-location, separation, Sync/Async hoặc deployment. Architectural implication là một quyết định riêng sau model review; source-only relation annotation không tự khai báo implication.

## Gửi annotation

1. Chọn **Load Tutor Support P2 case** và chỉ đọc khung **Raw requirements, workflow, and scenarios**.
2. Tải mẫu JSON hiển thị trong **Source-only annotation JSON**. Điền annotator ID tự khai báo, xác nhận `source_only_attested=true`, annotations 0..N và unresolved FRs.
3. Cập nhật các dòng trong relation registry cần annotation; để các dòng còn lại là `NOT_ANNOTATED`.
4. Dùng **Lock source-only annotation before model review**. Ứng dụng kiểm tra case/source hash, IDs, coverage, universe quan hệ và citations, sau đó thêm thời khóa biểu UTC cùng hash annotation.
5. Tải và lưu bản JSON đã khóa trước khi bật model output. Không sửa bản đã khóa; muốn sửa phải tạo phiên bản annotation mới và khóa lại trước khi mở proposal.

Hash chỉ là integrity checkpoint cục bộ. Reviewer identity tự khai báo, không được xác thực bên ngoài; checkpoint không chứng minh người đó đã tuân thủ blinding.

## Tiêu chí khóa

Annotation chỉ khóa khi mọi FR có ≥1 diễn giải hoặc có tên trong `unresolved_requirement_ids`; các nhóm này phải rời nhau và bao phủ đủ sáu FR. Citation phải dùng source IDs có trong case. Relation registry phải giữ nguyên đủ 60 dòng. `NOT_ANNOTATED` là giá trị hợp lệ và không tạo gold label.

## Biểu mẫu thủ công rút gọn

| Annotation ID | FR ID(s) | Responsibility / name | Activity | Operation | Workflow IDs | Source IDs | Rationale |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

| Relation ID | Subject FR | Predicate | Object FR | Status | Source IDs | Rationale |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Dùng JSON registry đầy đủ trong ứng dụng làm bản làm việc chính; bảng trên chỉ hỗ trợ đọc/ghi chú. Không điền các ô này bằng agent thay cho người annotator.

## Sau khi khóa

Chỉ sau khi source-only annotation đã được lưu và khóa, annotator mới có thể xem [P2_MODEL_REVIEW.md](P2_MODEL_REVIEW.md). Đây là một hoạt động khác; không sửa lại annotation độc lập để làm cho nó khớp proposal. Protocol cho nhiều annotator, adjudication và gold-label evaluation được mô tả trong [đánh giá extraction](LLM_EXTRACTION_EVALUATION.md).
