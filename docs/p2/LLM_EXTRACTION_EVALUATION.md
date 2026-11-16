# P2 — Đánh giá output extraction local

## Thiết lập và provenance

- Model Ollama đã gọi thật: `qwen3:4b`.
- Prompt version: `requirements-context-responsibility-evidence-boundary-v6`.
- Generation option: `temperature=0`; input SHA-256 của lần pipeline cuối `41af28d651927cc1229cd2361b92b1dcda8fc397f31440d4f40c77d0a324289b`.
- Trước khi mở rộng scenario source quote, hai lần gọi thật cùng input SHA `aef49dd9a10d756fbd9893d35812eddf13625f4d50dc0c491e20a51ec91f2e9c` cho wording và evidence citation khác nhau. Không tuyên bố tính tái lập từ temperature 0; seed/model execution metadata chưa được lưu.
- Bảng và pipeline dưới đây dùng output từ input hash cuối `41af…`. Không có proposal nào được xem là expert label.

## Output được dùng trong lần chạy pipeline

| Proposal | Tên | Activity / operation | Requirement citation | Citation check | Semantic review |
|---|---|---|---|---|---|
| P1 | Proposal for FR-01 | Search / tutor directory by subject and available time. | FR-01 → `TUTOR-REQ-FR-01` | exact span resolved | `REVIEW_REQUIRED` |
| P2 | Proposal for FR-02 | View / tutor profile, subjects, and listed availability. | FR-02 → `TUTOR-REQ-FR-02` | exact span resolved | `REVIEW_REQUIRED` |
| P3 | Proposal for FR-03 | Publish / weekly availability slots. | FR-03 → `TUTOR-REQ-FR-03` | exact span resolved | `REVIEW_REQUIRED` |
| P4 | Proposal for FR-04 | Request / session slot. | FR-04 → `TUTOR-REQ-FR-04` | exact span resolved | `REVIEW_REQUIRED` |
| P5 | Proposal for FR-05 | Accept/Decline / pending session request. | FR-05 → `TUTOR-REQ-FR-05` | exact span resolved | `REVIEW_REQUIRED` |
| P6 | Proposal for FR-06 | Receive / notice of tutor's decision. | FR-06 → `TUTOR-REQ-FR-06` | exact span resolved | `REVIEW_REQUIRED` |

Tên chứa literal FR ID và operation ngắn, nên dù citation hợp lệ proposal vẫn cần reviewer xác nhận hoặc sửa wording. `can_apply_to_fixture=true` chỉ là gate coverage/citation, không phải quality score.

## Evidence và boundary proposal

| ID | Proposal | Citation IDs | Kiểm tra | Đánh giá cần reviewer |
|---|---|---|---|---|
| E1 | FR-06 `is supported by` FR-06, status `PRESENT` | FR-06 (`TUTOR-REQ-FR-06`) | Citation resolve và endpoint set khớp; relation tự tham chiếu. | Tautological/ambiguous; nội dung FR-06 không chứng minh một evidence relation với chính nó. Dù reviewer chấp nhận, policy gate không sinh constraint từ self-relation. |
| B1 | Gom FR-01 và FR-02; “prerequisite for session requests” | FR-01, FR-02 | Citation resolve và bao phủ hai hypothesis endpoints. | Rationale về prerequisite không được nêu trong hai FR; boundary vẫn là giả thuyết, không được optimizer dùng. |

Không có duplicate relation trong output inference cuối; một proposal không đủ để đo duplicate rate. `citation_status=RESOLVED` kiểm tra ID/span, không đo entailment. Unsupported/ambiguous ở bảng trên là rà soát đối chiếu thủ công theo nội dung input, không phải independent reference label.

## So sánh hai lần gọi cùng input

Hai lần gọi trước đó cùng hash `aef49…` lần lượt nêu `triggers` FR-04→FR-05 với citation FR-04/05 và `leads to` cùng cặp nhưng cite FR-03; wording responsibility cũng khác. Lần pipeline cuối trên input hash mới `41af…` tạo self-relation E1. Cả output đều `REVIEW_REQUIRED`. Đây là variation quan sát được, không phải phép đo độ ổn định tổng quát.

## Không có metric semantic

Chưa có reviewer độc lập điền worksheet, adjudication hoặc reference labels. Không tính precision, recall, F1, accuracy hay semantic correctness rate. Exact-span success chỉ là kiểm tra cấu trúc citation.
