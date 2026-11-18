# P2.1 — Báo cáo giá trị nghiên cứu và trạng thái

## Phân biệt các lớp xác nhận

| Lớp | Điều có thể kết luận | Trạng thái Tutor hiện tại |
|---|---|---|
| Software verification | Một schema, gate hoặc deterministic code path hoạt động trên test inputs | Có regression và `P2_TEST_ONLY` coverage; chưa thay thế case run |
| Source grounding | Source ID/span được resolve và hash/package không đổi | Có thể kiểm định cấu trúc cho prepared package; không xác nhận entailment hoặc quyền tác giả |
| Human-reviewed interpretation | Người review đã ghi disposition, rationale và provenance | Chưa có Tutor quyết định thật |
| Mathematical feasibility/optimality | Candidate tuân thủ hard constraints; optimizer tối thiểu hóa objective đã khai báo trong giới hạn backend | Được kiểm thử trên bounded/synthetic inputs; không chứng minh architecture optimum độc lập |
| Architectural suitability | Boundary/dependency/interaction có phù hợp hệ thống thực hay không | `NOT_MEASURED`/`UNRESOLVED`; cần reviewer, source và deployment context |
| Empirical quality | Target chạy được, phép đo hợp lệ, observations tái lập | Chưa có target/adapter/observation; `NOT_MEASURED` |

## Protocol và threats to validity

- **Selection/construction:** Tutor Support là prepared synthetic case nhỏ; không đại diện cho requirements corpora hay lĩnh vực rộng.
- **Blinding/anchoring:** Source-only package hiện độc lập với model output và UI không render prepared helper mappings trước lock. Tuy nhiên identity/exposure là tự khai báo; phần mềm không xác minh reviewer đã xem gì. Người từng biết output v6/v7 không đủ điều kiện cho independent source-only annotation.
- **Reference labels:** Chưa có annotations độc lập hay adjudication. Không có gold set; không báo cáo semantic accuracy, precision, recall, F1 hoặc reviewer agreement.
- **Citation vs semantics:** ID/span/hash validation chỉ xác nhận cấu trúc và integrity, không entailment.
- **Policy validity:** Tutor catalog chứa hai soft experimental rules, chưa có source ngoài hoặc architecture review độc lập. Đây không phải tactic tổng quát.
- **Optimizer interpretation:** “Quantum” là candidate group; Python exhaustive enumeration/CP-SAT là classical. Objective optimum chỉ đúng theo input/weights/constraints đã khai báo.
- **Quality validity:** Scenario target là specification, không phải observation. ISO mapping còn `UNMAPPED`; bốn phần scenario Tutor còn thiếu; measurements chưa thực hiện.
- **Generalization and scale:** Một case không chứng minh generalization. CP-SAT 9–50 path chưa có runtime benchmark 50-role; optimum set có thể bị giới hạn cap/time.

## Trạng thái độc lập

- `IMPLEMENTATION_STATUS`: `PARTIAL` — package, lock validator, gated runner, review/policy/optimizer wiring và deterministic outputs tồn tại; coverage không đồng nghĩa mọi P4–P10 capability hoàn chỉnh.
- `RUNTIME_VERIFICATION_STATUS`: `PARTIAL` — full suite/compile kiểm tra code; chưa chạy end-to-end Tutor sau lock.
- `ANNOTATION_LOCK_STATUS`: `BLOCKED_EXTERNAL` — chưa có reviewer-supplied lock.
- `LIVE_INFERENCE_STATUS`: `BLOCKED_EXTERNAL` — qwen3:4b cài local nhưng chưa được gọi cho P2.1 vì thiếu lock.
- `HUMAN_REVIEW_STATUS`: `BLOCKED_EXTERNAL` — chưa có approve/correct/reject/defer case decisions.
- `SEMANTIC_EVALUATION_STATUS`: `NOT_MEASURED_NO_ADJUDICATED_REFERENCE`.
- `END_TO_END_EXPERIMENT_STATUS`: `BLOCKED_EXTERNAL`.

Kết luận tổng thể: software path có thể được kiểm chứng ở mức unit/integration fixtures; P2 unseen-case semantic validation và research validity chưa được chứng minh. Các metric/claims chỉ được nâng trạng thái sau khi artifact và quyết định thực sự được cung cấp.
