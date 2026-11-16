# P2 — Audit dependency thật từ input tới Quantum

## Kết luận audit nhân quả

Có hai đường khác nhau và phải báo cáo riêng:

1. **Candidate run chưa review:** `apply_proposals_to_fixture` có thể đưa responsibility proposals có citation hợp lệ vào biến R của optimizer để xem candidate. Candidate này vẫn `REVIEW_REQUIRED`. Evidence/boundary model proposals không tự trở thành evidence hay constraint. Đây không phải đường chứng minh quyết định semantic đã được duyệt.
2. **Run sau human review:** `apply_tutor_human_review` chỉ tạo responsibility inputs từ proposal `APPROVE`, `CORRECT`, `REJECT`, `DEFER` tường minh; relation có disposition riêng. Một relation chỉ sinh `EvidenceRecord` khi reviewer ghi implication kiến trúc riêng và named R pairs hợp lệ. Evidence được kiểm tra source spans/policy rồi mới có thể tạo soft constraint. Constraint là đầu vào enumerator, và candidate/quantum/interaction/quality outputs được tính lại từ đó.

Vì vậy causal claim P2 chỉ được kiểm tra nếu có model inference hậu-blind, reviewer decisions thật và trace đầy đủ. Test harness hiện chỉ kiểm tra wiring bằng dữ liệu `TEST-ONLY`; không thay thế run case thật.

## Audit từng dependency

| Nút | Đọc từ | Sinh ra | Provenance/trạng thái | Gate / giới hạn |
|---|---|---|---|---|
| Source package | FR, workflow, scenarios trong `eqcr/tutor_support.py` | Raw requirements, exact spans | Prepared fixture/source requirement | Không phải production elicitation. |
| Blind checkpoint | Source-only JSON, source-bundle hash | Annotation hash, reviewer ID tự khai báo, UTC time | Human decision trước model | UI ẩn model proposals tới khi khóa; hash phát hiện sửa nội dung sau lock, không xác minh danh tính hoặc hành vi blinding. |
| Ollama extraction | Raw FR map + workflow/scenario context; schema v7 | Normalized text, 0..8 responsibility proposals, evidence proposals, boundary hypotheses | Local LLM proposal / `REVIEW_REQUIRED` | FR IDs resolve được không chứng minh entailment. Workflow/scenario context không được dùng làm citation IDs cho model claims. |
| Citation audit | Proposal IDs/FR IDs + raw source map | exact source refs, coverage, duplicate/overlap flags, registry/direction flags | Deterministic transformation | Không có semantic score. `can_apply_to_fixture` chỉ là kiểm tra schema/citations/cap. |
| Candidate responsibility set | Citation-valid responsibility proposals | Dynamic R1..Rn candidate variables | LLM proposal, chưa review | Có thể chạy candidate optimizer để inspect; vẫn giữ `REVIEW_REQUIRED`. Không tạo verified evidence. |
| Human proposal review | Locked blind checkpoint + model proposal bundle | 0..N approved/corrected roles; relation dispositions; decision records | Human decision | Mỗi proposal cần `APPROVE/CORRECT/REJECT/DEFER`; FR có thể không có role và được ghi unresolved. |
| Relation registry | Predicate, FR endpoints, direction, status, citations, architecture implication và rationale tách riêng | Typed `RelationAnnotation` | Human decision sau model review, gắn proposal provenance | 60 predicate/pair rows chỉ thuộc blind annotation universe. Business ordering không phải implication kiến trúc. |
| Evidence materialization | `PRESENT` relation + explicit architecture implication + R pairs | EvidenceRecord gắn relation ID, FR endpoints, refs | Human decision + deterministic mapping | Citation cần bao phủ endpoints; Pydantic, source-span, role-pair validation; unknown/unregistered/rejected/deferred không được promote. |
| Constraint derivation | EvidenceRecord + responsibility approvals + versioned experimental case-policy catalog | Soft MUST_LINK/CANNOT_LINK có `evidence_ids` | Deterministic policy evaluation over human decisions | Per policy/evidence result ghi `APPLIED`, `NOT_APPLICABLE` hoặc `ABSTAINED`, lý do, versions, source IDs, R endpoints và constraint ID. Catalog chưa independently validated; source refs phải resolve và cover FR endpoints. |
| Partition optimizer | Reviewed R IDs + base constraints + derived evidence constraints | Exhaustive Bell partition candidates, feasible/optimal sets, cost | Deterministic classical Python transformation | Optimizer enumerates all candidate partitions; zero hard constraints currently come từ domain. SOFT weight ảnh hưởng objective; selected candidate là display policy, không recommendation. |
| Quantum candidates | Selected groups + responsibility records | R group allocations | Deterministic transformation | Quantum là nhãn candidate unit; không quantum computing. |
| Interactions | Scenario `related_requirement_ids` + all responsibility mappings + quantum assignment | Interaction hypotheses and same-quantum flags | Prepared scenario + deterministic transformation | Không chọn sync/async hoặc contract production. |
| Quality Profiles | Scenario target/metric/method + all roles matching FRs + assignment | Scenario responsibility/quantum mapping | Prepared scenario + deterministic transformation | `measurement=null`, `NOT_MEASURED`; không phải PASS. |
| Traceability | Source refs, proposals, lock, decisions, relations, evidence, constraints, partitions and outputs | Typed graph | Deterministic linkage | Structural graph PASS không chứng minh semantic correctness. |

## Predicate universe và policy

Blind annotation registry được cố định theo 6 FR: 30 ordered rows `BUSINESS_PRECEDES`, 15 undirected `SHARES_STATE_OR_INVARIANT`, 15 undirected `REQUIRES_INDEPENDENT_CHANGE`. `NOT_ANNOTATED` chỉ nghĩa là chưa quyết định; nó khác `UNKNOWN` và `SCOPED_ABSENT`.

| Predicate | Direction | Được ghi nhận | Optimizer mapping nếu reviewer quyết định riêng |
|---|---|---|---|
| `BUSINESS_PRECEDES` | Directed | Thứ tự nghiệp vụ | Không có, bất kể APPROVE; không suy ra topology hoặc interaction protocol. |
| `SHARES_STATE_OR_INVARIANT` | Undirected | Shared state/invariant candidate | `COLOCATE_CANDIDATE` → soft `MUST_LINK` theo policy P2. |
| `REQUIRES_INDEPENDENT_CHANGE` | Undirected | Independent-change candidate | `SEPARATE_CANDIDATE` → soft `CANNOT_LINK` theo policy P2. |

Catalog `EQCR-P2-TUTOR-EXPERIMENTAL-POLICIES@1.0.0` có hai soft rules và trạng thái `NOT_INDEPENDENTLY_VALIDATED`; chi tiết ở [catalog policy](../research/ARCHITECTURAL_POLICY_CATALOG.md). Chúng là quy tắc nội bộ thử nghiệm, không phải tactic đã xác nhận, source requirement hoặc human label. Việc reviewer duyệt predicate chưa tự động duyệt implication. Cả implication, rationale, responsibility pairs và source relation đều cần được ghi. Business order không có optimizer mapping.

## Revision impact

`apply_evidence_relation_edit` chỉ sửa một evidence đã duyệt và có relation annotation. Nó kiểm predicate registry, tương thích giữa predicate và implication, citation endpoint FR, exact R pair, rồi sửa cả relation annotation lẫn evidence materialization. `impact_preview("relation_registry")` đánh dấu evidence và các downstream constraint/partition/quantum/interaction/quality/validation/traceability artifacts cần tính lại. Revision lưu before/after, actor, source, reason và invalidated artifacts.

Nếu constraint hoặc assignment không đổi, phải nêu nguyên nhân bằng artifacts (ví dụ relation bị reject/defer hoặc policy không khớp); không mô tả “unchanged” như một tác động nhân quả.

## Inference lịch sử và test wiring

Run `qwen3:4b` v6 trước blind checkpoint là `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`; chi tiết trong `LLM_EXTRACTION_EVALUATION.md`. Không tính nó là run hậu protocol.

Unit tests hiện kiểm chứng test-only proposal/review/evidence đi qua optimizer, tạo 203 phân hoạch khi 6 R, constraint soft đổi optimal/display assignment, rồi đổi interaction `same_quantum`; source IDs giữ traceability và hard constraints được kiểm từng candidate. Đây là bằng chứng code path deterministic, không phải semantic outcome của Tutor Support. Chưa có case run hậu-blind/review thật.
