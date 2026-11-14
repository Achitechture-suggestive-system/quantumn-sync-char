# 07 — Giải thích hệ thống hiện tại qua PetClinic

Đây là case yêu cầu nhỏ. Tên PetClinic chỉ nói chủ đề demo; input không trích từ source code hay hệ thống vận hành PetClinic thật.

## Một vòng chạy qua mười bước

1. **Hiểu context:** C0 có sáu FR, một workflow dạng văn bản và hai quality scenarios. Mỗi trích dẫn có ID và offsets. Code kiểm tra ID/span.
2. **Đề xuất responsibility:** fixture đã có R1–R6 cho owner, pet và visit. Đây là PRECOMPUTED. Ollama có thể tạo bản đề xuất khác nhưng bundle vẫn cần người review, không phải nhãn đúng.
3. **Ghi evidence:** source quote nhắc tới capability; thiếu task IDs hoặc contract data thì mapping workflow và consistency vẫn unknown.
4. **Khai báo constraints:** H1 nối create/edit owner; H2 nối add/edit pet; H3 tách Add Pet khỏi Schedule Visit. Đây là chính sách what-if cho demo.
5. **Tìm grouping:** sáu responsibility tạo 203 partitions; mười thỏa hard rules với J=0. Chương trình chọn một grouping xác định để hiển thị, chỉ là tie-break.
6. **Tạo quantum candidates:** grouping hiển thị thành Q1=R1, Q2=R2/R3, Q3=R4/R5, Q4=R6. Gate kiểm mỗi R xuất hiện đúng một lần; không chứng minh độc lập triển khai.
7. **Đặt interaction cần nghiên cứu:** Pet (R4) → Visit (R6) là UNRESOLVED. Sync request-response và Async có thông báo hoàn tất đều có điều kiện, trích dẫn FR-06/scenario; chưa chọn phương án.
8. **Gắn quality:** Owner Search nối FR-01/R1/Q1 với p95 ≤ 250 ms @ 300 requests/s, status NOT_MEASURED. Pet–Visit gắn R4/R6 nhưng không có quality attribute/target, status INSUFFICIENT_EVIDENCE.
9. **Con người sửa:** thêm H4=MUST_LINK(R4,R6) xung đột H3. Preview đánh dấu downstream stale; áp dụng lưu revision và tính lại. Tắt H3 là correction do người dùng quyết định, không do LLM.
10. **Kiểm tra/xuất:** sau correction có năm feasible/optimal; report vẫn REVIEW_REQUIRED. JSON/ZIP và snapshots cho phép kiểm tra thay đổi. Đây là validation cấu trúc local, không phải phép đo chất lượng.

## Hệ thống tự động ở đâu?

Tự động: schema/ID/span checks; liệt kê partitions và tính cost theo policy đã nhập; gán R→Q cho candidate hiển thị; tạo các interaction hypotheses của case; gắn scenarios; tính impact closure; ghi decisions/revisions/snapshots; chạy assertions và export.

Không tự động xác định với chứng cứ đầy đủ: responsibility đúng nghĩa nào, policy có được business chấp thuận không, nên dùng Sync hay Async, contract/consistency, deployability, p95 đã đạt hay kiến trúc có thể được chấp nhận. Ollama viết đề xuất; validator độc lập kiểm cấu trúc/reference, không kiểm chân lý ngữ nghĩa.

Khi demo, giữ nguyên các trạng thái REVIEW_REQUIRED, UNRESOLVED, NOT_MEASURED và INSUFFICIENT_EVIDENCE. Mười optima là hòa theo objective cấu hình; năm sau correction chỉ là factibility theo constraint còn hiệu lực.
