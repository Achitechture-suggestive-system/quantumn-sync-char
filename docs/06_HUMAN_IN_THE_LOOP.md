# 06 — Human-in-the-loop và tính lại kết quả

## Ba thao tác khác nhau

1. **Review artifact:** APPROVE/REJECT/DEFER ghi object, người review, reason và source. Kết quả RECORDED_NO_STRUCTURAL_CHANGE; không sửa constraint hay xác minh ngữ nghĩa.
2. **Sửa responsibility:** chỉnh name/activity/operation, lưu before/after và reason. Đối tượng trở về REVIEW_REQUIRED; raw input gốc vẫn giữ nguyên.
3. **Sửa constraint (bước 04):** UI preview impact rồi mới cho áp dụng. Cú pháp hỗ trợ ADD/SET/ENABLE/DISABLE/REMOVE theo schema.

Thông tin người sửa, lý do và source là bắt buộc. Hệ thống đọc old value thực tế, đồng thời giữ nhãn old value do người dùng nhập riêng.

## Phụ thuộc và preview

eqcr/impact.py định nghĩa dependency graph. Ví dụ: responsibilities → evidence/partitions/quanta/validation; evidence → constraints/quanta/interactions; constraints → partitions/validation; partitions → quanta; quanta → interactions/quality; interactions → quality/validation. Đóng bắc cầu của graph tạo stale list và affected steps.

Preview chỉ dự đoán, không lưu decision/snapshot. Khi người dùng áp dụng, app.py gọi lại toàn bộ run_pipeline với input đã sửa, sau đó phát lại decisions, dựng traceability graph mới và lưu snapshot. Impact map ghi vùng bị ảnh hưởng, gồm traceability; phép tính chưa incremental, không dùng cache chọn lọc. Test/regression so artifacts lẽ ra không đổi; điều này không chứng minh diễn giải semantically đúng. APPROVE evidence chỉ đổi review status và provenance graph; không làm target quality thành measured.

## Các snapshot P0 đã chạy

Run cục bộ run-20261114T101711Z-41291a74 có snapshots sau (JSON thô được Git bỏ qua):

| Phiên bản | Thay đổi | Khả thi/tối ưu | Status |
|---|---|---:|---|
| v1 | Fixture, H1–H3 active | 10 / 10 | REVIEW_REQUIRED |
| v2 | Thêm H4 MUST_LINK(R4,R6), H3 active | 0 / 0 | INFEASIBLE |
| v3 | Tắt H3, giữ H4 | 5 / 5 | REVIEW_REQUIRED |

v3 giữ H4 và ghi rõ lý do con người tắt H3. Assertion baseline 10 optima trở thành not applicable sau revision, tránh báo regression giả cho input đã đổi. Run ID là bằng chứng local; có thể tạo lại theo [kịch bản demo](08_MVP_DEMO_SCRIPT.md).

Test sửa R1 xác nhận raw input không đổi, nội dung chỉnh được cập nhật, status semantic trả REVIEW_REQUIRED và downstream bị invalidated/recomputed. Code vẫn chạy lại toàn bộ pipeline; danh sách invalidation để truy vết, không phải tối ưu hiệu năng.
