# Hướng dẫn gửi gói source-only cho reviewer

## Gói dành cho reviewer

Chỉ gửi thư mục [`source_only_reviewer`](source_only_reviewer/) cho annotator. Thư mục này có đúng năm file:

- `README.md` — định nghĩa annotation và hướng dẫn hoàn tất.
- `SOURCE_MATERIAL.md` — sáu yêu cầu chức năng, bốn hoạt động workflow và hai quality scenarios cùng source IDs/spans.
- `SOURCE_DATA.json` — cùng dữ liệu nguồn ở định dạng có cấu trúc.
- `ANNOTATION_TEMPLATE.json` — responsibility worksheet trống và registry 60 relation ở trạng thái `NOT_ANNOTATED`.
- `MANIFEST.json` — protocol version và SHA-256 cho source files, từng source span và raw case hash.

Không gửi toàn bộ `docs/p2/` cho annotator. Các báo cáo nghiên cứu khác mô tả những giai đoạn phân tích không thuộc gói source-only.

## Trạng thái hiện tại

- Package: `P2-SOURCE-ONLY-PACKAGE-v1`.
- Annotation protocol: `P2-BLIND-ANNOTATION-v3`.
- Manifest SHA-256: `5725d44f491c5b680f79773482b6a53a03810cb88978b073a6ec5aacac68fe81`.
- Canonical case source SHA-256: `7293d2b27ad89a48b737eab30bad4b448e75cfa2bcd625948280d24abfc2ad17`.
- Gói này chỉ chứa source material và worksheet trắng. Chưa có annotation, model output hay kết quả phân hoạch trong gói.

Annotator làm việc trên package đã gửi, điền worksheet và hoàn tất attestation chỉ khi đúng sự thật. Họ phải ghi mọi FR chưa diễn giải vào `unresolved_requirement_ids`, không để mẫu mặc định tự gán trạng thái. Sau đó nộp JSON khóa để kiểm tra. Nếu annotator từng xem các phân tích của Tutor Support, họ không đủ điều kiện cho source-only annotation.

## Giới hạn xác thực

Validator kiểm tra file tồn tại, hash, nội dung source, schema, attestation, protocol và thời gian. Nó không thể xác thực danh tính reviewer hoặc lịch sử họ đã đọc gì. Các attestation độc lập vẫn do reviewer tự khai báo; cần quy trình tuyển chọn/ghi nhận bên ngoài nếu nghiên cứu yêu cầu xác thực danh tính hoặc blinding mạnh hơn.

Xem [quy trình kiểm tra lock](ANNOTATION_LOCK_VALIDATION.md) để xác minh package và lock. Không tạo lock thay reviewer.
