# Logic MVP hiện tại qua 10 bước — Tutor Support

Tài liệu này giải thích code hiện tại; trạng thái run case thật được ghi riêng ở [TUTOR_E2E_DEMO_RESULT.md](TUTOR_E2E_DEMO_RESULT.md). Tách bốn nguồn: `SOURCE_REQUIREMENT`, `LOCAL_OLLAMA_PROPOSAL`, `DETERMINISTIC_TRANSFORMATION`, `ARCHITECTURAL_POLICY`, và `HUMAN_DECISION`. Test harness mang `P2_TEST_ONLY`, không phải LLM hay review thật.

| Bước | Đầu vào và provenance | Thực thi | Đầu ra / kiểm tra | Giới hạn |
|---|---|---|---|---|
| 01 Context Understanding | Sáu FR, bốn workflow, hai scenario trong `eqcr/tutor_support.py`; `PREPARED_CASE_STUDY` / source requirement. | `RawRequirements` kiểm schema, duy nhất ID và source spans; `run_pipeline` kiểm quote/offset. | `raw_requirements`, context, source hashes/refs. | Source span đúng chỉ xác nhận ánh xạ, không xác nhận nguồn production hay tính đại diện. |
| 02 Responsibility Identification | Raw FR map; khi chạy demo, Ollama nhận FR là claim source và workflow/scenario chỉ là context. | `propose_responsibilities`: local `qwen3:4b`, JSON schema, `temperature=0`, request timeout; kiểm FR IDs, duplicates/overlap, cap 0..8 và resolve spans. | Proposal P IDs, coverage, citations, normalized requirements; mọi item `REVIEW_REQUIRED`. | Model semantics chưa được xác nhận. Proposal chưa được chấp nhận không tạo input R cho optimizer. |
| 03 Evidence Modeling | Model relation proposals hoặc quyết định người review. | `apply_tutor_demo_review` kiểm exact source refs, predicate registry, endpoint, action và responsibility pairs. Relation được approve/correct thành `RelationAnnotation`; materialize `EvidenceRecord` khi có implication/pair. | Evidence registry, review status, source IDs và relation IDs. | Cùng FR/entity hoặc workflow gần nhau không đủ làm evidence kiến trúc. APPROVE là quyết định demo stakeholder, không là nhãn độc lập. |
| 04 Constraint & Quality Reasoning | Evidence đã review, responsibility approvals và `constraint_policy_catalog` trong prepared case. | `_derive_evidence_constraints` áp dụng policy versioned; citation/status/endpoint/role gates, duplicate/conflict audit; nếu thiếu điều kiện thì `ABSTAINED`. | Soft `MUST_LINK`/`CANNOT_LINK`, policy trace, quality links. | Catalog là `INTERNAL_EXPERIMENTAL_CASE_POLICY`, chưa được independently validated. Không tự tạo hard domain constraints. |
| 05 Candidate Optimization | Chỉ responsibility đã chấp nhận/correct và constraint set hiện hành. | `run_pipeline` gọi `_optimize`: enumerator Python exhaustive đến 8 role; CP-SAT cổ điển cho 9–50. | Bell count, feasible/optimal candidates, cost, solver/completeness. | Với 6 role: Bell(6)=203 candidate partitions trước lọc. Soft weight ảnh hưởng objective; không có role thì optimizer không có partition candidate. “Quantum” không phải quantum computing. |
| 06 Quantum Boundary Refinement | Partition được chọn, responsibility records. | `_build_quanta` gán mỗi R vào đúng một group; graph builder gắn tầng/placeholder theo schema. | Candidate `Q` groups, allocation, graph, membership checks. | Boundary là proposal; ownership/deployability không được xác nhận bởi grouping. |
| 07 Interaction Design | Scenario–FR mappings, responsibility coverage, assignment. | Mapping deterministic tạo interaction edges và contract skeleton. | Hypotheses, `same_quantum`, options và contract. | `BUSINESS_PRECEDES` không quyết định Sync/Async. Contract thiếu bằng chứng vẫn `UNDECIDED`/`UNRESOLVED`. |
| 08 Quality Allocation — QAME | Prepared quality scenario, related FRs, role allocation. | QAME six-part profile, ISO/status mapping và traceability links. | Profile cho `SC-REQUEST-ACK`, `SC-DECISION-NOTICE`; target/metric/method, assigned R/Q. | Target là target source-defined; không có load test/observations nên measurement `NOT_MEASURED`, không phải quality PASS. |
| 09 Human-in-the-Loop | Proposal bundle (nếu có), output artifacts và edit người dùng nhập. | Human Review nhận actor/reason/source/action; demo run lưu riêng. Revision evidence/responsibility gọi `run_pipeline` lại và ghi old/new, snapshots, hashes, diff, full-recompute scope. | `decisions`, `revisions`, `demo_comparison`, `demo_revision_audit`. | Human decision là provenance của decision, không phải thử nghiệm. Không ghi actor/rationale thay người dùng. |
| 10 Verification & Iteration | Toàn bộ input, proposals, decisions, constraints và outputs. | Structural validators và traceability graph kiểm IDs, refs, spans, hard constraints, allocations, links, completeness, checksums. | `validation_report`, trace graph, JSON/ZIP export. | PASS chỉ trong scope từng assertion. Không có semantic accuracy, production deployability hay quality measurement tự phát sinh. |

## Nhân quả từ Ollama tới optimizer

Trong `EXPLORATORY_UNBLINDED_DEMO`, model call tạo proposal bundle; bước đầu tạo artifact run cố ý bỏ toàn bộ responsibilities/evidence/constraints do model gợi ý. Bundle chỉ nằm trong artifact proposal và UI. Sau action thật ở Human Review, `apply_tutor_demo_review` tạo responsibilities từ `APPROVE`/`CORRECT`; relation/evidence chỉ được materialize khi review tách evidence interpretation khỏi architecture implication và nêu cặp R. Pipeline sau đó đọc fixture đã review, không đọc proposal raw như verified evidence. `_derive_evidence_constraints` cần đủ các gate, rồi kết quả constraint được truyền đến `_optimize`. Từ partition đó mới dựng quanta, interaction edges, QAME profiles và traceability.

## Các phân biệt quan trọng

- `SOURCE_BACKED` nghĩa source ID/span được map; không có nghĩa source entailment đúng.
- Soft coupling do catalog là objective preference, không phải hard architectural requirement. Hard constraints phải được khai báo riêng và mọi feasible partition phải thỏa.
- Objective minimum là tối ưu với đúng hàm mục tiêu/constraint đã nêu, không phải “kiến trúc tối ưu” về maintainability, operability hoặc deployability.
- `SYNCHRONOUS`/`ASYNCHRONOUS` được sinh như pattern hypothesis; không thành contract khi chưa có source evidence và quyết định reviewer đủ điều kiện.
- `NOT_MEASURED` không phải PASS hoặc FAIL; thiếu target system/measurement giữ đúng trạng thái.
- MVP chạy lại toàn pipeline sau edit để dễ kiểm tra phụ thuộc; chưa có incremental recomputation/cache.

## Trạng thái xác thực

Code/test chứng minh flow deterministic và gate behavior. Một test-only AppTest exercise proposal-shaped data và revision để bảo đảm UI nối được. Không tính nó là inference thật hoặc semantic review. Chỉ artifacts trong [kết quả E2E](TUTOR_E2E_DEMO_RESULT.md) mới được gọi là lần chạy thực tế.
## Output trực tiếp của run Tutor unblinded — 19/11/2026

Run run-20261119T071904Z-ebd8fd64 đã gọi qwen3:4b local thật trên input SHA 7293d2b27ad89a48b737eab30bad4b448e75cfa2bcd625948280d24abfc2ad17. Bảng dưới đây nối từng việc code làm với output thực tế; không gộp proposal model vào evidence đã duyệt.

| Stage | Xử lý trong run | Output render | Nguồn và trạng thái |
|---|---|---|---|
| 01 Context | Kiểm input IDs, schema và exact source spans. | 6 FR, 4 WF, 2 scenarios; PASS. | Prepared source package; structural only. |
| 02 Responsibility | Gửi FR tới Ollama với schema/version và temperature 0; resolve citations. | P01–P06, một proposal mỗi FR; review required. | Live LLM proposal; chưa accepted. |
| 03 Evidence | Kiểm relation endpoints, predicate và citations. | E01 FR-04→FR-05, E02 FR-05→FR-06; còn là proposal; 1 prepared scope-boundary row. | LLM proposals + prepared fixture; semantic meaning unassessed. |
| 04 Policy | Chạy policy catalog có version trên evidence và role pairs đã review. | 0 constraints, 0 conflicts; hai policy result NOT_APPLICABLE. | Deterministic transformation + experimental policy. |
| 05 Optimizer | Enumerate partitions của accepted roles. | 0 roles được nhận → 0 partition/feasible/optimal. | Deterministic; gate hoạt động. |
| 06 Quantum | Gán responsibility vào partition đã chọn. | 0 quanta; INSUFFICIENT_EVIDENCE. | Deterministic. |
| 07 Interactions | Trace scenario qua responsibility và quantum. | 0 edges; INSUFFICIENT_EVIDENCE. | Deterministic; chưa có Sync/Async contract. |
| 08 QAME | Tạo profile sáu phần cho scenarios. | 2 profiles; NOT_MEASURED. | Prepared scenarios + mapping; chưa benchmark. |
| 09 Human review | Lưu actor/action/reason/source và full recompute. | 0 quyết định; đang chờ người vận hành. | Chưa có Human Decision. |
| 10 Verification | Kiểm traceability, constraint, completeness và provenance. | 10 stage records; overall REVIEW_REQUIRED. | Structural checks; không có semantic/production validation. |

Chi tiết hash, proposal audit, trạng thái các validator và việc cần làm trong Human Review nằm tại TUTOR_E2E_DEMO_RESULT.md.
## Output trực tiếp của run Tutor unblinded — 19/11/2026

Run run-20261119T071904Z-ebd8fd64 đã gọi qwen3:4b local thật trên input SHA 7293d2b27ad89a48b737eab30bad4b448e75cfa2bcd625948280d24abfc2ad17. Bảng dưới đây nối việc code làm với output thực tế; proposal model không được gộp vào evidence đã duyệt.

| Stage | Xử lý quan sát được | Output render | Nguồn và trạng thái |
|---|---|---|---|
| 01 Context | Kiểm input IDs, schema và exact source spans. | 6 FR, 4 WF, 2 scenarios; PASS. | Prepared source package; structural only. |
| 02 Responsibility | Gửi FR tới Ollama với schema/version và temperature 0; resolve citations. | P01–P06, một proposal mỗi FR; REVIEW_REQUIRED. | Live LLM proposal; chưa accepted. |
| 03 Evidence | Kiểm relation endpoints, predicate và citations. | E01 FR-04→FR-05, E02 FR-05→FR-06; còn là proposal; 1 prepared scope-boundary row. | LLM proposals + prepared fixture; semantic meaning unassessed. |
| 04 Policy | Chạy policy catalog có version trên evidence và role pairs đã review. | 0 derived constraints, 0 conflicts; hai policy result NOT_APPLICABLE. | Deterministic transformation + experimental policy. |
| 05 Optimizer | Enumerate partitions của accepted roles. | 0 roles được nhận → 0 partition/feasible/optimal. | Deterministic; review gate giữ optimizer không đọc model output raw. |
| 06 Quantum | Gán responsibility vào partition đã chọn. | 0 quanta; INSUFFICIENT_EVIDENCE. | Deterministic. |
| 07 Interactions | Trace scenario qua responsibility và quantum. | 0 edges; INSUFFICIENT_EVIDENCE. | Deterministic; chưa có Sync/Async contract. |
| 08 QAME | Tạo profile sáu phần cho scenarios. | 2 profiles; NOT_MEASURED. | Prepared scenarios + mapping; chưa benchmark. |
| 09 Human review | Lưu actor/action/reason/source và full recompute. | 0 decisions; đang chờ người vận hành. | Chưa có Human Decision. |
| 10 Verification | Kiểm traceability, constraint, completeness và provenance. | 10 stage records; overall REVIEW_REQUIRED. | Structural checks; không có semantic/production validation. |

Đầu ra trước review cố tình không có partition/Quantum groups: đây là hành vi của gate, không phải thiếu một lời gọi optimizer. Khi stakeholder gửi review thật, cùng flow sẽ nhận roles/evidence đã duyệt, chạy policy/optimizer rồi tạo interaction và QAME outputs. Xem hash và audit đầy đủ tại TUTOR_E2E_DEMO_RESULT.md.
