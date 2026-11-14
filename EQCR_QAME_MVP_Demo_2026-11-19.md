> **Trạng thái thực thi ngày 14/11/2026:** kế hoạch P0/P1 gốc bên dưới được giữ lại làm bối cảnh, không phải bằng chứng rằng mọi hạng mục đã hoàn tất. P0 hiện được bảo toàn tại commit 3d517b1a39158e539239dc73d594bc0938649feb trên nhánh main và tag p0-demo-2026-11-14. Kết quả chạy có phạm vi ở docs/verification/P0_BASELINE_VERIFICATION.md; mô tả implementation hiện hành bắt đầu tại docs/00_START_HERE.md. Các mục P1 vẫn là backlog cho tới khi có commit/test tương ứng.
# EQCR + QAME — Checklist MVP demo trước thứ Năm 19/11/2026

**Ngày lập kế hoạch:** 14/11/2026. **Freeze demo:** hết thứ Tư 18/11/2026.

## 1. Mục tiêu demo và phạm vi

Một luồng **từ requirement + workflow chưa có source code** tới **quantum candidates + interaction proposal + quality profile**, có **human review → revision → impacted rerun → revalidation** và log thay đổi. Đồ án **không** tự chọn/evaluate architecture style. Sử dụng **PetClinic mini-case** gồm R1–R6; 3 chính sách H1/H2/H3 chỉ là *what-if policy* để demo optimizer, không được nhận là sự thật nghiệp vụ đã xác nhận.

**Điều kiện bắt buộc:** người demo bấm nút chạy được end-to-end local; LLM không được là nguồn bảo chứng duy nhất; mọi quyết định từ LLM có citation/source ID hoặc `REVIEW_REQUIRED`; nếu thiếu chứng cứ trả `UNKNOWN`/`UNRESOLVED`.

**Ưu tiên:** P0 = bắt buộc trước 18/11; P1 = thêm nếu P0 hoàn tất; P2 = sau buổi demo.

## 2. Các deliverables P0, bám nguyên thứ tự pipeline Draw.io

| # | Bước trong Draw.io | Việc MVP phải làm | Input → Output cần lưu | Validator / Demo check | Ưu tiên |
|---|---|---|---|---|---|
| 01 | Context Understanding | Nạp `C0`, 5–8 FR, 1 workflow mô tả bằng text/JSON, 2 scenarios; Ollama trích xuất bản chuẩn hóa | `raw_requirements.json` → `context.json` | Có requirement ID, source text/span, không tự bịa requirement | P0 |
| 02 | Responsibility Identification | Ollama đề xuất R1–R6 theo Activity → Operation → Responsibility; có màn hình sửa | `context.json` → `responsibilities.json` | ID duy nhất, có FR/activity reference; yêu cầu người review phần ngữ nghĩa | P0 |
| 03 | Evidence Modeling | Lưu typed relations `PRESENT`, `SCOPED_ABSENT`, `UNKNOWN`; liên kết nguồn và status | `responsibilities.json` → `evidence.json` | Không biến UNKNOWN thành false; mọi `PRESENT` phải có source hoặc marked assumption | P0 |
| 04 | Constraint & Quality Reasoning | Nạp/biên tập H1:R2-R3 must-link, H2:R4-R5 must-link, H3:R4-R6 cannot-link từ fixture *what-if*; phát hiện conflict | `evidence.json`, `scenarios.json`, policy → `constraints.json` | Phân biệt hard/soft, source-backed/policy/human override; bắt được must/cannot cùng cặp | P0 |
| 05 | Candidate Optimization | Liệt kê partition 6 responsibilities (Bell(6)=203), tính hàm objective, lọc hard constraints, top candidates | `constraints.json` → `partitions.json` | Chính sách H1/H2/H3 cho 10 nghiệm tối ưu J=0; conflict → `INFEASIBLE` | P0 |
| 06 | Quantum Boundary Refinement | Chọn candidate, đặt Quantum ID, ownership/role, nhóm responsibility, ghi boundary rationale | `partitions.json` → `quanta.json` | Mỗi responsibility đúng một primary Quantum trong partition; không mất/nhân đôi R | P0 |
| 07 | Interaction Design — Sync / Async | Phát hiện ít nhất dependency Pet–Visit; xuất Sync/Async/UNRESOLVED + contract skeleton và lý do | `quanta.json`, scenarios → `interactions.json` | Không khẳng định Sync/Async khi thiếu consistency/latency evidence; field contracts có trạng thái | P0 |
| 08 | Quality Allocation — QAME | Map both supplied scenarios: Owner Search target p95 ≤250ms @300rps → R1 → Q; Pet–Visit has no quality attribute/target and traces to R4/R6 plus its interaction | scenarios, quanta, edges → `quality_profiles.json` | Preserve source trace; Owner Search is `NOT_MEASURED`, Pet–Visit is `INSUFFICIENT_EVIDENCE`; no fake PASS | P0 |
| 09 | Human-in-the-Loop Review | UI sửa constraint H3, chọn lý do + nguồn + người review, version snapshots/diff; router xác định steps bị ảnh hưởng | `review_request.json` → `decisions.json`, `revisions.json` | Mỗi sửa có before/after, reason, actor, affected artifacts; revision không phá bản cũ | P0 |
| 10 | Verification & Iteration | Chạy local gates + integrated check, gắn `PASS/FAIL/REVIEW_REQUIRED/INSUFFICIENT_EVIDENCE`; xuất báo cáo | outputs 01–09 → `validation_report.json` | Các hard constraints và traceability được xác minh; không claim empirically verified khi chưa đo | P0 |

### Deliverable liên quan UI và xuất dữ liệu

- [x] **P0-UI:** Chạy `streamlit run app.py`; có tối thiểu 4 tabs: **Input**, **Evidence & Constraints**, **Quantum & Contracts**, **Human Review & Validation**. Mỗi tab có JSON/data bảng rõ ràng. Đã mở app và kiểm tra bốn tabs.
- [x] **P0-GRAPH:** Hiển thị các Quantum candidates + cạnh interaction (có nhãn `Sync?`/`Async?`/`UNRESOLVED`) bằng `st.graphviz_chart` hoặc draw.io export. Đã xác nhận graph SVG và cạnh Pet–Visit `UNRESOLVED` trong browser.
- [x] **P0-REVIEW:** Form `target step`, `object id`, `old/new`, `reason`, `source`, nút **Apply & Revalidate**. Đã chạy preview, conflict H4, correction H3, và revalidation trong browser.
- [x] **P0-EXPORT:** Tải JSON đầy đủ, validation report và draw.io *nếu xuất draw.io đã sẵn*; không khóa demo nếu xuất XML chưa xong. ZIP artifacts/snapshots và validation JSON đã tải, mở và kiểm tra; draw.io XML chưa được thêm.
- [x] **P0-REPLAY:** Có nút **Load PetClinic demo data** và nút **Run offline fixture** để demo không lệ thuộc thời gian LLM generate; fixture phải ghi nhãn `PRECOMPUTED`. Đã chạy offline fixture thành công.

## 3. Công nghệ tối giản

- **LLM local:** Ollama với Qwen model tương thích phần cứng (`qwen3.5:4b` hoặc `qwen3.5:9b` sau khi xác minh có sẵn trên Ollama). LLM chỉ trích xuất/đề xuất evidence có refs; dùng JSON schema/Pydantic; nhiệt độ thấp, lưu prompt+model version.
- **Backend/core:** Python 3.11+, Pydantic, NetworkX, exhaustive enumeration cho n=6, pytest. **OR-Tools CP-SAT là P1** (không cần cho Bell(6) nhỏ).
- **UI:** Streamlit. **Storage:** JSON snapshots trong `runs/<run_id>/`, có thể thêm SQLite P1. Không cần FastAPI/React/Postgres/Redis cho demo đầu.
- **Validation:** pure Python validators tách khỏi LLM.

## 4. Dữ liệu PetClinic mini-case

| ID | Tên |
|---|---|
| R1 | Find Owner |
| R2 | Create Owner |
| R3 | Edit Owner |
| R4 | Add Pet |
| R5 | Edit Pet |
| R6 | Schedule Visit |

- `H1 MUST_LINK(R2,R3)`; `H2 MUST_LINK(R4,R5)`; `H3 CANNOT_LINK(R4,R6)` là **what-if policy**, không phải kết luận kiến trúc thật.
- Candidate hiển thị mẫu: `{R1}|{R2,R3}|{R4,R5}|{R6}`.
- Quality scenario mẫu: Owner Search p95 <=250ms tại 300 requests/s; **target đặt ra, chưa đo**.
- Interaction mẫu Pet↔Visit: `UNRESOLVED` cho đến khi nhập decision/context về consistency, latency, failure, contract.

## 5. Bốn thí nghiệm live bắt buộc

1. **Happy path**: Import data → LLM proposals → local validate → enumerate → select candidate → interactions → quality → report. Kỳ vọng: status có thể `REVIEW_REQUIRED`/`NOT_MEASURED`, không fake VERIFIED.
2. **Contradiction**: giữ H3 cannot-link R4–R6, thêm must-link R4–R6. Kỳ vọng `INFEASIBLE`, chỉ rõ cặp H3/H4; không tạo partition.
3. **Human correction**: từ case conflict, thay H3 hoặc hủy ràng buộc đối nghịch có lý do, tiếp tục optimize, lưu v1/v2, hiển thị diff.
4. **Impact/regression**: khi sửa H3, đánh dấu constraints/partitions/boundary/interactions/quality là affected; revalidate. Đảm bảo context/requirements không tự đổi khi chỉ sửa constraint.

### Bộ kiểm thử pytest tối thiểu

- `test_schema_required_fields`
- `test_no_missing_source_reference`
- `test_unknown_is_not_false`
- `test_bell6_partition_count_203`
- `test_what_if_10_zero_cost_optima`
- `test_must_cannot_conflict_detected`
- `test_each_responsibility_assigned_once`
- `test_contract_unresolved_without_evidence`
- `test_quality_target_not_measured`
- `test_human_revision_audit_and_impact`
- `test_regression_unchanged_unaffected_artifacts`
- `test_reproducible_rerun_with_frozen_fixture`

## 6. Kế hoạch từ 14 đến 18/11/2026

| Ngày | Giao việc trọng tâm | Exit gate cuối ngày |
|---|---|---|
| **Thứ Bảy 14/11** | Project skeleton, schemas, PetClinic fixtures, Ollama smoke test, UI input | `app.py` chạy, load được fixture, một request local LLM thành JSON hợp lệ hoặc có fallback rõ ràng |
| **Chủ Nhật 15/11** | Steps 01–04: context, responsibility, evidence, constraints, validators | FR→R→evidence→H1/H2/H3 hiển thị, có source links và trạng thái review |
| **Thứ Hai 16/11** | Steps 05–06: enumeration, objective, candidate display, graph | 203 partitions, 10 tối ưu J=0 theo fixture, graph Q1–Q4 |
| **Thứ Ba 17/11** | Steps 07–08: contracts, quality allocation, gates | Có Pet–Visit interaction và Owner Search profile, không giả lập đạt metrics |
| **Thứ Tư 18/11** | Steps 09–10: feedback, rerun, audits, regression; chạy rehearsal | Chạy live 4 thí nghiệm và lưu 2 snapshots + report; freeze demo |
| **Thứ Năm 19/11** | Demo | Không thay đổi kiến trúc/stack vào ngày demo |

## 7. Ngoài scope đến ngày 19/11 (P2)

- Training/fine-tuning LLM, self-host large 27B+ nếu thiếu phần cứng.
- Multi-agent orchestration, RAG/KB quy mô lớn, ingestion arbitrary PDF/BPMN với OCR.
- Kết luận Architecture Style Selection/Evaluation.
- Benchmark p95 250ms @300rps trong hệ thống thật, chưa có môi trường đo.
- Production database, CI/CD phức tạp, đăng nhập đa vai trò, microservice deployment, graph editor drag-and-drop đầy đủ.
- Nghiên cứu định lượng quy mô lớn/khẳng định khả năng tổng quát hóa trên nhiều dự án.

## 8. Script demo trong 6–8 phút

1. **00:00–01:00:** Giới thiệu C0 + FR/NFR/workflow, bấm Load PetClinic; mô tả không dùng source code.
2. **01:00–02:00:** Show LLM extraction với source refs; validator đánh dấu unknown và review-required.
3. **02:00–03:00:** Show evidence graph và H1/H2/H3 what-if policy.
4. **03:00–04:00:** Run optimizer, 203 partitions → 10 nghiệm tối ưu; mở quantum graph.
5. **04:00–05:00:** Show Pet–Visit as `UNRESOLVED` with cited, conditional Sync/Async hypotheses and unknown contract fields; show both quality profiles and their measurement states.
6. **05:00–06:30:** Human Review: thêm constraint mâu thuẫn → FAIL rõ nguyên nhân → sửa có ghi lý do → Recompute.
7. **06:30–08:00:** Compare versions, impacted steps, validation report, export JSON.

## 9. Tiêu chí được phép nói và không được phép nói

**Được nói:** “Chúng tôi đã demo được pipeline từ tài liệu đầu vào đến candidate architecture, nhận feedback và revalidate có lưu nguồn.”

**Không nói khi chưa có bằng chứng:** “Quantum này là tối ưu thực tế”, “đã đạt hiệu năng 250 ms”, “LLM hiểu đúng 100%”, “case study đã được chuyên gia độc lập phê duyệt”.

**Thành công tối thiểu:** Demo được end-to-end với PetClinic, một lỗi bị phát hiện, một human correction làm thay đổi kết quả đúng cách, và report có thể truy vết.
