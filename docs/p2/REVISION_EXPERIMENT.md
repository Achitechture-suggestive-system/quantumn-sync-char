# P2 — Thí nghiệm sửa relation và chạy lại

## Quy trình cho case thật

Case thật chưa có source-only lock/reviewer decisions mới theo protocol. Không tự điền một correction để thỏa acceptance. Sau khi có inference hậu-blind và reviewer đã duyệt relation cùng architecture implication:

1. Lưu baseline artifacts và hash/timestamp của source, proposal, lock, decisions.
2. Chọn một evidence đã `APPROVED`, `PRESENT`, có `relation_annotation_id`, policy implication và named R pair.
3. Trong Human Review sửa relation bằng predicate thuộc registry, hai FR endpoints, source citations bao phủ cả hai endpoints, đúng responsibility IDs và implication phù hợp predicate. Ghi relation rationale, architecture rationale, actor, source và reason.
4. Recompute pipeline. So sánh constraint/evidence IDs, feasible/optimal partitions, objective, selected group, interactions, quality mappings và traceability; kiểm hard constraints từng partition.
5. Ghi nguyên nhân nếu output không đổi. Relation bị reject/defer hoặc không khớp policy không được mô tả như optimizer treatment.

`BUSINESS_PRECEDES` không xuất hiện trong evidence-revision optimizer form vì workflow order không phải architecture constraint. `SHARES_STATE_OR_INVARIANT` chỉ hợp với `COLOCATE_CANDIDATE`; `REQUIRES_INDEPENDENT_CHANGE` chỉ hợp với `SEPARATE_CANDIDATE`.

## Test-only propagation evidence

> Các dữ liệu dưới đây do test helper tạo ra và gắn `P2_TEST_ONLY`; chúng không phải qwen output, annotation, domain truth hoặc expert decision.

| Run | Test-only reviewed relation | Policy-derived constraint | Tác động quan sát được |
|---|---|---|---|
| Trước | `SHARES_STATE_OR_INVARIANT(FR-05, FR-06)`; implication `COLOCATE_CANDIDATE`, pair `(R5,R6)` | Soft `MUST_LINK(R5,R6)`, evidence ID `EV-E01-PAIR-01` | 203 Bell partitions được liệt kê; policy thay đổi objective/optima và selected grouping; interaction SC-DECISION-NOTICE ghi `same_quantum=true`. |
| Sau | Cùng relation ID được human-edit test sang FR-04/FR-05, pair `(R4,R5)` với rationale/source fields test-only | Soft `MUST_LINK(R4,R5)` | Tính lại partition/assignment; SC-REQUEST-ACK đổi sang `same_quantum=true`, còn SC-DECISION-NOTICE đổi sang `false`. |

Trong cả hai run không khai báo hard constraints; tập feasible vì vậy tuân thủ các hard constraints đang bật một cách hiển nhiên. Test riêng kiểm mọi candidate với mọi hard constraint nếu có. Quantum group là partition display; interaction mode và quality measurement vẫn unresolved/`NOT_MEASURED`. Đây là kiểm thử causal wiring deterministically, không xác nhận relation test có ý nghĩa cho Tutor Support.

## Kết quả case study

Chưa thực hiện revision experiment bằng accepted post-blind LLM proposal và quyết định reviewer thật. Trạng thái này được giữ `PENDING_HUMAN_REVIEW`; test-only result không thay thế yêu cầu case thật. Sau khi có decisions, cập nhật phần này bằng hashes và artifact diff trước/sau, không gắn nhãn human decision cho test harness.
## Trạng thái demo live — 2026-11-19

Đã có run EXPLORATORY_UNBLINDED_DEMO riêng: run-20261119T071904Z-ebd8fd64. Đây là inference qwen3:4b local mới, nhưng proposal chưa được review. Run có 0 role được chấp nhận và 0 constraint dẫn xuất, nên chưa có before/after optimizer experiment cho case này. Các hàng propagation phía trên vẫn chỉ là test-only.

Trạng thái revision demo: AWAITING_DEMO_REVIEW. Stakeholder cần review responsibilities và relations thật; sau đó chọn một PRESENT relation đã duyệt, thỏa policy có tài liệu, trước khi revision UI dùng được. Người review nhập quyết định old/new, source, rationale và actor. Chỉ sau action đó mới ghi nhận full recomputation và before/after comparison.
