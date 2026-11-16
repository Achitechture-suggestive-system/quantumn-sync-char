# P2 — Đánh giá extraction và protocol tạo reference labels

## Trạng thái khoa học

**`ANNOTATION_PROTOCOL_DRAFT — GOLD_LABELS_NOT_AVAILABLE`**

Chưa có independent source-only annotations được nộp bởi hai reviewer độc lập, chưa có adjudicator và chưa có gold labels. Vì vậy không có precision, recall, F1, accuracy, semantic correctness rate hay kết luận rằng model “đúng”. `SOURCE_BACKED` trong ứng dụng chỉ có nghĩa ID/span được resolve; nó không xác nhận cách hiểu.

## Inference thật đã chạy trước protocol blind mới

Checkout trước đây đã gọi local `qwen3:4b` thật với prompt `requirements-context-responsibility-evidence-boundary-v6`, `temperature=0`, input SHA-256 `41af28d651927cc1229cd2361b92b1dcda8fc397f31440d4f40c77d0a324289b`. Hai lần gọi cùng input hash cũ `aef49dd9a10d756fbd9893d35812eddf13625f4d50dc0c491e20a51ec91f2e9c` cũng từng cho wording/citations khác. Đây là dữ liệu ghi nhận từ inference cũ, **trước blind checkpoint**.

Phân loại bắt buộc của toàn bộ output cũ: `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`. Output này không được dùng để đánh giá độc lập, làm gold label, thiết kế annotation, hay làm bằng chứng rằng review thật đã xảy ra. Nó được giữ ở đây chỉ để bảo toàn provenance và mô tả lý do protocol mới cần checkpoint.

| Proposal cũ | Nội dung quan sát được | Citation / cấu trúc | Ghi chú exploratory, không phải nhãn |
|---|---|---|---|
| P1–P6 | Mỗi proposal nêu một responsibility ngắn ứng với FR tương ứng; wording dùng literal FR ID hoặc tóm tắt ngắn. | FR-01..FR-06 resolve tới source IDs/spans. | Resolve không xác nhận semantic coverage hoặc granularity. |
| E1 | `FR-06 is supported by FR-06`, status `PRESENT`. | Citation resolve; relation tự tham chiếu. | Được nhận diện là self-relation/ambiguous khi đọc lại; chưa phải expert label. |
| B1 | Gom FR-01 và FR-02, rationale nói “prerequisite for session requests”. | Citation IDs resolve. | Rationale không được nêu trong hai FR; đây là rà soát của nhóm trên input, không phải nhãn độc lập. |

Hai lần inference trước đó trên cùng hash `aef49…` có khác biệt wording/evidence; mẫu nhỏ và metadata generation chưa đủ để suy rộng về tái lập. Không có output inference hậu-blind trong checkout hiện tại. App ở prompt version mới yêu cầu blind source annotation được hash-lock trước khi gọi Tutor Support model.

## Audit citation và output

Ollama output được kiểm tra theo các trường riêng: proposal ID duy nhất, FR IDs biết trước, FR coverage 0..N, source IDs/spans resolve, proposal duplicates/overlaps, relation endpoint validity, relation registry membership, duplicate/conflicting relations, self-relations và boundary source coverage. Những kiểm tra này là deterministic structural validation.

- Trùng FR coverage không tự động là duplicate responsibility; nhiều role cho một FR là hợp lệ.
- Thiếu proposal cho một FR không tự động là lỗi: FR được ghi là uncovered/unresolved.
- Relation nằm ngoài predicate registry không thể được approve; reviewer phải correct/reject/defer.
- Citation resolve hoặc `can_apply_to_fixture=true` không được gọi là semantic validation hoặc score.
- Không có duplicate relation nào được quan sát trong một output cũ; cỡ mẫu này không chứng minh duplicate rate bằng 0.

## Protocol evaluation đề xuất trước khi đo

1. Dùng cùng frozen source bundle và prompt/schema version; ghi model tag/response tag, prompt version, generation options, thời điểm UTC, source hash, blind annotation hashes và raw response artifact.
2. Có ít nhất hai reviewer làm source-only annotation độc lập trước khi xem output. Mỗi bản được hash-lock riêng; identity chỉ tự khai báo nếu chưa có kiểm chứng ngoài ứng dụng.
3. Sau checkpoint, mỗi reviewer review model proposals độc lập bằng `APPROVE`, `CORRECT`, `REJECT`, `DEFER`. Không nhập quyết định review trở lại source-only labels.
4. Adjudicator thứ ba xử lý bất đồng sau khi hai bộ quyết định đã khóa; lưu cả bản riêng, bất đồng, quyết định và rationale. Không adjudication thì không gọi reference set là gold.
5. Trước đo lường, đăng ký matching rules cho 0..N responsibility sets, multi-FR role mapping, predicate/direction/status và source citation. Phân biệt citation-resolution rate với semantic matching.
6. Chỉ sau đó mới tính precision/recall/F1 hoặc agreement theo matching rule đã khóa; báo cáo theo case, cardinality, bất đồng và unresolved. Giữ test cases tách khỏi prompt/policy tuning.

Các bước trên là protocol draft, chưa được thực hiện. Không có metric hoặc semantic accuracy score trong báo cáo này.
