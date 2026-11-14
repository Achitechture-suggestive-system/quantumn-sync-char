# Quy trình human revision

## Trước khi áp dụng

Review artifact nhận object, action APPROVE/REJECT/DEFER, lý do, source và reviewer. Kết quả RECORDED_NO_STRUCTURAL_CHANGE; review không sửa evidence/measurement hay tự xác minh semantics.

Structural revision nhận object, giá trị mới, lý do, nguồn và actor. Hệ thống đọc giá trị cũ thực tế, kiểm tra thay đổi và tính impact preview/status dự kiến. Preview không lưu decision hoặc snapshot.

## Sửa constraint trong demo

1. Chạy fixture để tạo v1.
2. Ở bước 04, thêm H4=ADD MUST_LINK(R4,R6), kèm lý do/nguồn/người sửa.
3. Preview hiển thị conflict H3/H4, artifacts downstream stale và dự báo INFEASIBLE.
4. Apply/revalidate tạo v2 với 0 candidate khả thi.
5. Disable H3 với lý do tường minh; đây là thay đổi what-if do con người chọn.
6. Revalidate tạo v3 với 5 khả thi/optima; status vẫn REVIEW_REQUIRED.

Run local run-20261114T101711Z-41291a74 giữ snapshots v1/v2/v3. JSON thô bị Git ignore.

## Sửa responsibility

UI thay name/activity/operation. Decision giữ before/after, actor, reason, source và impact. Semantic status trở lại REVIEW_REQUIRED. Test test_human_responsibility_edit_invalidates_downstream_and_resets_review xác nhận raw input không đổi.

## Vùng tính lại

Impact map cho biết vùng stale. Khi apply, app.py gọi lại toàn bộ run_pipeline và phát lại decisions; đây chưa phải selective/incremental execution. Xem [Human-in-the-loop](06_HUMAN_IN_THE_LOOP.md).
