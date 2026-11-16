# Lối vào worksheet human review P2

Để giảm nguy cơ rò rỉ thông tin, P2 dùng hai artifact tách biệt:

- [Source-only blind annotation](P2_BLIND_ANNOTATION.md) — hoàn thành, lưu và khóa trước khi chạy model.
- [Post-lock model review](P2_MODEL_REVIEW.md) — chỉ mở sau checkpoint blind annotation.

Artifact source-only không chứa proposal ID hoặc chi tiết output model. App kiểm tra hash của source và annotation trước khi cho chạy inference Tutor Support. Checkpoint ghi nhận tính toàn vẹn và thứ tự thao tác; nó không xác thực danh tính reviewer hoặc chứng minh reviewer chưa từng xem output trước đó.
