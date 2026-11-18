# P2 — Audit dependency thật từ input tới Quantum

## Kết luận audit nhân quả

Có hai đường khác nhau và phải báo cáo riêng:

1. **Candidate run chưa review:** `apply_proposals_to_fixture` có thể đưa responsibility proposals có citation hợp lệ vào biến R của optimizer để xem candidate. Candidate này vẫn `REVIEW_REQUIRED`. Evidence/boundary model proposals không tự trở thành evidence hay constraint. Đây không phải đường chứng minh quyết định semantic đã được duyệt.
2. **Run sau human review:** `apply_tutor_human_review` chỉ tạo responsibility inputs từ proposal `APPROVE`, `CORRECT`, `REJECT`, `DEFER` tường minh; relation có disposition riêng. Một relation chỉ sinh `EvidenceRecord` khi reviewer ghi implication kiến trúc riêng và named R pairs hợp lệ. Evidence được kiểm tra source spans/policy rồi mới có thể tạo soft constraint. Constraint là đầu vào enumerator, và candidate/quantum/interaction/quality outputs được tính lại từ đó.

Vì vậy causal claim P2 chỉ được kiểm tra nếu có model inference hậu-blind, reviewer decisions thật và trace đầy đủ. Test harness hiện chỉ kiểm tra wiring bằng dữ liệu `TEST-ONLY`; không thay thế run case thật.

## Entrypoints và dữ liệu thực sự đi qua

| Code entrypoint | Input dependency | Output dependency / causal effect | Evidence boundary |
|---|---|---|---|
| `eqcr.p2_experiment.run_p2_experiment` → `eqcr.ollama.propose_responsibilities` | Frozen Tutor source package, verified source-only lock, exact `qwen3:4b` tag, prompt/schema version and clean committed checkout | Calls local Ollama and exports raw response, parsed proposals and structural audit | No valid lock is present, so this path was not executed in the current P2 experiment. |
| `eqcr.ollama.apply_proposals_to_fixture` | Parsed responsibility proposals and original requirement/workflow source map | Citation-valid unreviewed responsibilities can replace the candidate responsibility list used by `run_pipeline`; the candidate remains review-required | This can affect exploratory candidate partitions, but proposal/evidence hypotheses do not become verified evidence or constraints. |
| `eqcr.p2_review.apply_tutor_human_review` | Proposal bundle plus a separate disposition for every responsibility, relation and boundary proposal | Creates approved/corrected reviewed responsibilities; creates typed relation annotations; materializes evidence only when the reviewer records a separate architecture implication and named responsibility pairs | `APPROVE` is a human decision, not an independent correctness label. `REJECT`/`DEFER` do not promote a proposal. |
| `eqcr.evidence_audit.audit_evidence_records` → `_derive_evidence_constraints` | All typed evidence rows, relation direction when an annotation is linked, exact source spans, status and optional FR endpoints | Emits deterministic duplicate/conflict groups and blocked evidence IDs; blocked rows cause a policy abstention before any constraint is emitted | The audit detects exact structural duplicates, direct `PRESENT`/`SCOPED_ABSENT` conflict, and known/`UNKNOWN` mixtures. It does not judge entailment, predicate equivalence, or temporal/context differences. |
| `eqcr.pipeline._derive_evidence_constraints` | Reviewed `PRESENT` evidence, exact endpoint citations, linked relation annotation, approved responsibility endpoints, matching policy implication and policy catalog | Emits a soft `Constraint` with source/evidence trace or a policy abstention record | This is a deterministic policy transformation over human decisions; the catalog is internal/experimental and has no hard rules. |
| `eqcr.pipeline.run_pipeline` → `_optimize` | Current responsibilities, base constraints and derived evidence constraints; explicit constraint overrides bypass the catalog | Optimizes the assembled constraint set, then recomputes quanta, interaction hypotheses, QAME profiles and traceability | For six Tutor responsibilities it uses the exhaustive classical enumerator. Only a real reviewed run can establish the case-level effect. |

The causal edge from an unreviewed responsibility proposal to candidate partitions is real but remains exploratory. The stronger research claim—validated evidence and human review driving optimizer and downstream outputs—is gated through the separate human-review and policy path above. No valid P2 case has yet traversed that path.

## P2.1 package source-only và cổng rò rỉ UI — recheck 2026-11-19

Gói reviewer được ghim đúng năm file: `README.md`, `SOURCE_DATA.json`, `SOURCE_MATERIAL.md`, `ANNOTATION_TEMPLATE.json` và `MANIFEST.json`. Bản chiếu source-only bỏ các mapping chuẩn bị sẵn như `related_requirement_ids`, trường quality helper, policy catalog, proposal và optimizer output. Manifest gắn với case/source hash hiện tại; lock v3 mang theo hash manifest. Validator kiểm tra đúng allowlist file, hash từng file, source IDs/spans, schema mẫu trắng, lock schema/coverage/attestation và thời điểm lock có timezone; timestamp tương lai bị từ chối.

Tutor UI xác thực package trước khi hiển thị. Khi chưa có lock hợp lệ, UI chỉ render `SOURCE_DATA.json`, không render toàn bộ raw Tutor object đang nằm trong memory; nút model proposal bị khóa nếu package/lock không hợp lệ. Sau lock, app mới có thể hiện raw input và proposal. AppTest xác nhận JSON trước lock chỉ gồm các trường source package và không chứa định danh nội bộ/model. Những kiểm tra này xác nhận ranh giới giao diện và integrity package, không xác nhận reviewer bên ngoài đã xem hoặc hiểu gì.

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
| Duplicate/conflict audit | Tất cả EvidenceRecord và relation direction đã khai báo | Nhóm duplicate citation, mâu thuẫn trạng thái trực tiếp, mixed-with-UNKNOWN; danh sách evidence bị chặn | Deterministic transformation | Xung đột và duplicate exact claim/citation được ghi `REVIEW_REQUIRED`, không tự chọn một phía. Không phát hiện mâu thuẫn ngữ nghĩa cần kiến thức domain. |
| Constraint derivation | EvidenceRecord không bị audit chặn + responsibility approvals + versioned experimental case-policy catalog | Soft MUST_LINK/CANNOT_LINK có `evidence_ids` | Deterministic policy evaluation over human decisions | Per policy/evidence result ghi `APPLIED`, `NOT_APPLICABLE` hoặc `ABSTAINED`, lý do, versions, source IDs, R endpoints và constraint ID. Catalog chưa independently validated; source refs phải resolve và cover FR endpoints. |
| Partition optimizer | Reviewed R IDs + base constraints + derived evidence constraints | For this six-role Tutor case, exhaustive Bell partitions, feasible/optimal sets and cost. Generic runs use exhaustive enumeration through R8 and CP-SAT for R9–R50, which reports a capped set of proven optima rather than every feasible partition. | Deterministic classical transformation | Tutor policy rules currently emit soft preferences only; no hard domain constraint is supplied. SOFT weight affects the objective; the displayed candidate is a display policy, not a recommendation. |
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
