# Catalog quy tắc evidence-to-constraint của Tutor Support

## Trạng thái và phạm vi

Tutor Support dùng catalog `EQCR-P2-TUTOR-EXPERIMENTAL-POLICIES` phiên bản `1.0.0`. Catalog được khai báo là `EXPERIMENTAL_CASE_POLICY_CATALOG`, có trạng thái review `NOT_INDEPENDENTLY_VALIDATED`, và có nguồn gốc `INTERNAL_EXPERIMENTAL_CASE_POLICY`.

Đây là hai quy tắc thử nghiệm cho đường chuyển đổi evidence sang optimizer constraint. Chúng **không được gọi là tactic đã được xác nhận**, không phải dữ kiện nghiệp vụ, không khẳng định production architecture, và chưa được architecture/research reviewer độc lập duyệt.

## Quy tắc

| Policy ID / version | Quality driver được khai báo | Điều kiện implication riêng | Optimizer effect | Hạn chế |
|---|---|---|---|---|
| `P2-SOFT-SHARED-INVARIANT-COLOCATION@1.0.0` | Candidate cohesion khi reviewer xác định shared state/invariant | `COLOCATE_CANDIDATE` | Soft `MUST_LINK`, weight 1.0 | Không tự suy ra implication từ predicate; không tạo hard constraint. |
| `P2-SOFT-INDEPENDENT-CHANGE-SEPARATION@1.0.0` | Candidate changeability khi reviewer xác định independent change | `SEPARATE_CANDIDATE` | Soft `CANNOT_LINK`, weight 1.0 | Không khẳng định independent deployment; không tạo hard constraint. |

Mỗi entry khai báo version, predicate, relation, weight, quality driver, assumption, rationale, nguồn gốc policy nội bộ và điều kiện abstain. `BUSINESS_PRECEDES` không có mapping optimizer.

## Rule evaluation và trace

`run_pipeline` kiểm tra catalog qua schema chặt chẽ, sau đó ghi `constraints.policy_evaluation` cho từng policy/evidence pair. Mỗi dòng ghi catalog/policy versions, evidence ID, source IDs, responsibility endpoints nếu áp dụng, kết quả `APPLIED`, `NOT_APPLICABLE` hoặc `ABSTAINED`, lý do và derived constraint ID. Snapshot catalog được kèm để không phụ thuộc việc người đọc tìm lại fixture.

`APPLIED` chỉ có thể xuất hiện khi predicate/status khớp, evidence và hai responsibilities được reviewer approve, source spans resolve và bao phủ hai FR endpoint, architecture implication/rationale riêng đã được ghi, relation annotation được liên kết và pair endpoints hợp lệ. `UNKNOWN`, `SCOPED_ABSENT`, thiếu citation, implication không khớp, role chưa duyệt, self/unknown pair và bản ghi trùng đều không tạo constraint.

Constraint sinh ra có `origin=ARCHITECTURAL_POLICY`; ID/rationale liên kết policy, version và evidence. Optimizer chỉ nhìn thấy constraint sau các gate trên. Kết quả là preference mềm trong objective đã khai báo, không phải bằng chứng rằng kiến trúc được tạo ra là đúng.

## Bằng chứng còn thiếu

- Chưa có reviewer độc lập xác nhận hai quy tắc phù hợp với một quality-attribute response/tactic model.
- Chưa có source citation bên ngoài gắn vào từng entry; nguồn hiện tại là policy nội bộ phục vụ kiểm tra pipeline.
- Chưa có annotation hoặc model run thật sau blind checkpoint. Kết quả của các test dùng `P2_TEST_ONLY`.
- Trước khi dùng như catalog tactic tổng quát, cần architecture/research review, nguồn chuẩn được ghi, và tests cho assumptions/side effects. Nếu thiếu evidence hoặc review, giữ trạng thái `UNKNOWN`/`UNRESOLVED` và abstain.
