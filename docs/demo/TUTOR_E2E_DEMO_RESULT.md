# Kết quả E2E Tutor — demo unblinded

## Trạng thái

**`AWAITING_DEMO_REVIEW`** — inference local thật và cả 10 bản ghi trạng thái pipeline đã được tạo. Human Review chưa được gửi, vì vậy proposal model chưa thành responsibility/evidence được chấp nhận và optimizer chưa nhận chúng. Đây là demo unblinded, không phải nghiên cứu P2.

## Run thực tế

| Trường | Giá trị |
|---|---|
| Case/source | `TUTOR-SUPPORT-P2-01`, prepared requirements package: 6 FR, 4 WF, 2 quality scenarios |
| Run ID | `run-20261119T071904Z-ebd8fd64` |
| Execution mode | `EXPLORATORY_UNBLINDED_DEMO` |
| Research eligibility | `EXCLUDED_FROM_BLIND_RESEARCH` |
| Artifact location | `runs/demo-unblinded/run-20261119T071904Z-ebd8fd64/` (local, ignored; không commit run artifacts) |
| Model / Ollama | `qwen3:4b`, Ollama `0.40.16`, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7` |
| Model metadata | `AVAILABLE`, size 2,497,293,931 bytes, `Q4_K_M` |
| Prompt / parameters | `requirements-context-multiresponsibility-relation-boundary-v7`, `temperature=0` |
| Input SHA-256 | `7293d2b27ad89a48b737eab30bad4b448e75cfa2bcd625948280d24abfc2ad17` |
| Raw response SHA-256 | `6503bbbdb75b1267f39c207ccb4613d12852fa6bf38d8d77b06fec72fa6973b8` |
| Inference time | `2026-11-19 14:17:40.103221` → `14:19:04.285938` (+07:00) |
| Run status | `REVIEW_REQUIRED`; demo status `AWAITING_DEMO_REVIEW` |

Ollama API được gọi qua `OLLAMA_HOST=172.17.0.1:11434`; Streamlit chỉ lắng nghe `127.0.0.1:8501`. Model tag/digest và timestamp nằm trong `ollama_proposals.json`. Đây là inference mới được khởi chạy từ nút **Run local Ollama proposals**, không phải fixture hoặc output test.

## Proposal và audit

Responsibility proposals P01–P06 được model tạo theo từng FR; mỗi item có một FR ID, source ID tương ứng, ID duy nhất và exact source span đã resolve:

| Proposal | Model name | FR / source ID |
|---|---|---|
| P01 | Search Tutor Directory | FR-01 / `TUTOR-REQ-FR-01` |
| P02 | View Tutor Profile | FR-02 / `TUTOR-REQ-FR-02` |
| P03 | Manage Tutor Availability | FR-03 / `TUTOR-REQ-FR-03` |
| P04 | Request Session | FR-04 / `TUTOR-REQ-FR-04` |
| P05 | Accept/Decline Session | FR-05 / `TUTOR-REQ-FR-05` |
| P06 | Receive Notification | FR-06 / `TUTOR-REQ-FR-06` |

Structural audit: 6/6 FR IDs valid, 6/6 source ID sets valid, 6/6 citations resolve to exact spans, no duplicate responsibility flag. E01/E02 cite both relation endpoints, belong to the declared predicate registry, and have no duplicate, conflict, or self-relation flag. B01's two cited endpoint spans resolve and its duplicate flag is false.

The structural audit did **not** assess semantic truth or ambiguity. In B01, the rationale says a separate notification service could deliver “without blocking” the tutor response; the requirements do not state that runtime property. Treat this clause as an unsupported architectural rationale for reviewer correction/rejection, not as source evidence. E01/E02 remain business-order hypotheses; `BUSINESS_PRECEDES` does not imply an architecture constraint. No semantic score is available.

Evidence provenance:

- **Source requirement / prepared case:** six FR, four workflow activities, two quality scenarios and exact source spans.
- **LLM proposal:** P01–P06, E01–E02, B01 and the context summary in `ollama_proposals.json`.
- **Deterministic transformation:** ID/span validation, proposal flags, pipeline stage records, policy evaluation, traceability and quality profile construction.
- **Architectural policy:** experimental catalog `EQCR-P2-TUTOR-EXPERIMENTAL-POLICIES@1.0.0`; its rules are not independently validated.
- **Human decision:** none in this run.
- **Prepared fixture:** initial scope-boundary row `EV-TUTOR-RUNTIME-SCOPE`; it says runtime topology is outside this requirements-only package and remains `REVIEW_REQUIRED`.

## Mười stage đã render trong run

| Bước | Trạng thái thực tế | Đầu ra thực tế trong run |
|---|---|---|
| 01 Context Understanding | `PASS` | Source IDs/spans và input hash hợp lệ; input vẫn là prepared requirements, không có source code. |
| 02 Responsibility Identification | `REVIEW_REQUIRED` | 6 model proposals ở bundle riêng; responsibility được chấp nhận = 0; 6 FR còn unresolved cho optimizer. |
| 03 Evidence Modeling | `REVIEW_REQUIRED` | 1 scope-boundary evidence fixture; E01/E02 chưa thành evidence được duyệt. Evidence structural audit `NO_FINDINGS`. |
| 04 Constraint & Quality Reasoning | `PASS` | 0 derived constraints, 0 hard conflicts. Hai policy entry trả `NOT_APPLICABLE` cho scope-boundary record. |
| 05 Candidate Optimization | `REVIEW_REQUIRED` | Enumerator chưa có R được chấp nhận: 0 partition enumerated, 0 feasible, 0 optimal, không có nhóm được chọn. |
| 06 Quantum Boundary Refinement | `INSUFFICIENT_EVIDENCE` | 0 quanta; không có responsibility assignment để phân hoạch. |
| 07 Interaction Design — Sync / Async | `INSUFFICIENT_EVIDENCE` | 0 interaction edges; chưa có assignment. |
| 08 Quality Allocation — QAME | `NOT_MEASURED` | 2 scenario profiles được tạo deterministic; performance/reliability chưa đo. |
| 09 Human-in-the-Loop Review | `REVIEW_REQUIRED` | Không có decision/revision record; app đang mở ở Human Review. |
| 10 Verification & Iteration | `REVIEW_REQUIRED` | Structural/provenance report có đủ 10 step records; không xác nhận semantic truth, deployability hay performance. |

“0 partition” là kết quả đúng của review gate, không phải optimizer đã phân hoạch model proposals. Không được trình bày các test-only 203-partition examples như output Tutor live.

### Ghi chú validator sau inference

Snapshot ban đầu có `unknown_is_not_false=false`, trong khi run chỉ có scope-boundary `SCOPED_ABSENT` và không có evidence `UNKNOWN`. Điều này là không áp dụng, không phải lỗi chuyển UNKNOWN thành phủ định. Code được sửa ở commit `4a8b1a41f0f8eadea37d56e49dc68c1570fb3847` để trường hợp không có UNKNOWN trả `null` cùng `NOT_APPLICABLE_NO_UNKNOWN_EVIDENCE`; snapshot cũ được giữ nguyên làm lịch sử run. Regression mới và toàn bộ 139 tests pass sau thay đổi.

## Để tiếp tục demo qua optimizer

Trong tab **Human Review & Validation**, demo stakeholder cần:

1. Nhập định danh stakeholder và chọn acknowledgement `DEMO_STAKEHOLDER`.
2. Với P01–P06, chọn `APPROVE`, `CORRECT`, `REJECT` hoặc `DEFER`; ghi rationale và source cho từng quyết định. Bất kỳ correction/additional responsibility nào cũng phải trích đúng source ID.
3. Với E01/E02, quyết định riêng về business relation. Chỉ chọn architecture implication và responsibility pairs nếu có căn cứ review độc lập với business ordering; nếu không, để unresolved/defer.
4. Với B01, xem xét riêng rationale “without blocking” vì property đó không có trong requirements; correct/reject/defer và ghi lý do.
5. Nhấn **Apply demo stakeholder review & recompute all stages**. Chỉ khi đó reviewed roles/evidence có thể vào policy evaluator và optimizer.
6. Chọn một evidence relation được chấp nhận để làm revision thật; ghi old/new, source, rationale và actor. App sẽ lưu snapshot trước/sau rồi chạy lại toàn pipeline.

Không có decision hay revision nào được tạo thay stakeholder. Scientific P2 vẫn `P2_BLOCKED_INDEPENDENT_ANNOTATION`; run này bị loại khỏi blind research và không tạo gold labels.
