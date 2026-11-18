# Hướng dẫn người ghi annotation độc lập

## Phạm vi tài liệu

Chỉ sử dụng `SOURCE_MATERIAL.md` và `SOURCE_DATA.json` trong thư mục này. Hoàn tất và khóa annotation trước khi mở tài liệu phân tích nào khác của case.

Đây là case Tutor Support nhỏ được chuẩn bị cho nghiên cứu; nội dung không đến từ hệ thống production. Tài liệu không cung cấp source code, topology triển khai hoặc quyết định kiến trúc đã được xác nhận.

## Cách ghi responsibility

- Một FR có thể có không, một hoặc nhiều diễn giải responsibility; một responsibility có thể được hỗ trợ bởi nhiều FR.
- Chỉ ghi activity/operation mà bạn thấy có căn cứ trong nguồn. Không chia nhỏ một hành động thành nhiều responsibility nếu nguồn không hỗ trợ granularity đó.
- Nếu chưa diễn giải được FR, để FR đó trong `unresolved_requirement_ids`.
- Ghi `requirement_ids`, `source_requirement_ids`, các `workflow_ids` được hỗ trợ, `source_workflow_ids` và rationale ngắn.

## Cách ghi relation

Giữ nguyên toàn bộ relation registry trong JSON. Các predicate là `BUSINESS_PRECEDES` (có hướng), `SHARES_STATE_OR_INVARIANT` và `REQUIRES_INDEPENDENT_CHANGE` (không hướng).

- `PRESENT`: nguồn hỗ trợ relation; nêu lý do và cite cả hai FR endpoint.
- `UNKNOWN`: đã cân nhắc nhưng nguồn chưa đủ để kết luận.
- `SCOPED_ABSENT`: chỉ dùng khi phạm vi nguồn nêu rõ relation bị loại trừ.
- `NOT_ANNOTATED`: chưa đưa ra quyết định; để trống citation và rationale.

Thứ tự nghiệp vụ tự nó không xác định cách nhóm, giao tiếp hay triển khai responsibility. Không điền quan hệ ngoài registry.

## Hoàn tất và khóa

1. Bắt đầu từ `ANNOTATION_TEMPLATE.json`; không đổi `case_id`, hash, protocol version, predicate hoặc endpoint trong registry.
2. Điền reviewer ID và xác nhận hai trường attestation chỉ khi đúng sự thật.
3. Với mỗi FR, thêm một hay nhiều responsibility annotations hoặc ghi rõ FR unresolved. Không để hai nhóm trùng nhau hay thiếu FR.
4. Để relation chưa đánh giá ở `NOT_ANNOTATED`; chỉ thêm rationale/citation khi đã quyết định.
5. Dùng ứng dụng EQCR + QAME để khóa JSON. Ứng dụng ghi timestamp UTC và hash nội dung. Lưu nguyên bản JSON đã khóa.
6. Chạy `python scripts/validate_p2_annotation_lock.py --annotation-lock <locked-json> --source-package <package-directory>` để kiểm tra file/hash/schema/thời điểm.

Danh tính và lịch sử tiếp xúc tài liệu được tự khai báo; phần mềm không thể xác thực độc lập reviewer đã đọc gì.
