# Changelog

## NFR theo ISO/IEC 25010 và ba phương án Quantum — 2026-11-20

- Thêm đề xuất nhãn ISO/IEC 25010:2023 từ NFR, đoạn chữ khớp và component được nêu trong văn bản. Ánh xạ được xác nhận mới tham gia phân hoạch, truy vết theo NFR và xuất JSON. Các chỉ số vận hành vẫn `NOT_MEASURED`.
- So sánh và lưu lựa chọn A/B/C theo các chi phí có thể truy vết. Studio ưu tiên biên Pareto và ghi rõ phương án trội hơn khi bổ sung một phương án ngoài biên.
- Browser smoke xác nhận NFR-01 làm đổi phương án xếp đầu từ P011 sang P031 ở chế độ characteristics. Ba phương án là P031, P011 và P029. Kiểm tra thêm một NFR tự nhập cho Customer Login nhận hai nhãn đề xuất và chỉ cập nhật sơ đồ sau xác nhận.
- 149 bài kiểm tra cục bộ và CI trên commit triển khai đều qua. [GitHub Actions](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44714611105)

## Truy vết requirement và chia theo characteristics — 2026-11-20

- Studio nhập requirement có mã và cho gắn mỗi nguồn vào characteristic của component. Sơ đồ đầu ra hiển thị mã có thể bấm để mở nội dung nguồn. Bảng truy vết và JSON review cho biết đường từ requirement đến Quantum.
- Chế độ **Chia theo characteristics** xếp phương án khả thi theo chi phí rải, chi phí trộn, rồi điểm trọng số. So sánh theo SYNC và trọng số tiếp tục có trong Studio.
- Kiểm tra trình duyệt trên cổng 8501. Sau khi chuyển Ticket Creation sang đặc tính Nhất quán luồng ticket và gắn `REQ-04`, đổi chế độ xếp từ P047 sang P031 đưa Ticket Creation vào Q2 cùng Ticket Router. Chi phí tách kho giảm 1 xuống 0, chi phí ASYNC giữ chung tăng 0 lên 1. Đã kiểm tra bấm mã mở đúng nguồn và gỡ mã vẫn giữ đặc tính đã gán.
- 147 bài kiểm tra cục bộ và CI trên commit triển khai đều qua. [GitHub Actions](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44682122391)

## Khôi phục luồng Quantum Studio — 2026-11-20

- Khôi phục bộ giải, chính sách SYNC/ASYNC và so sánh A/B của `e10bd81`. Gỡ bảng độ nhạy và phân tích Ollama khỏi Studio. Phần **Characteristics** trong từng Quantum vẫn hiện đặc tính, component phụ trách và các nhóm cùng phụ trách.
- Kiểm tra trực tiếp trên cổng 8501. **Phân tích sơ đồ** hiển thị P011 và ánh xạ Q1–Q3. **Ưu tiên giữ dữ liệu** xếp P031 đầu, nơi Q1 và Q2 cùng phụ trách Trải nghiệm khách hàng. Human Review hiển thị và lỗi `omit_axis` không xuất hiện.
- 144 bài kiểm tra cục bộ và CI trên commit khôi phục đều qua. [GitHub Actions](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44676901252)

## Ollama và characteristics trong sơ đồ Quantum — 2026-11-20

- Đầu ra hiển thị từng characteristic, component phụ trách và Quantum cùng phụ trách. Bảng độ nhạy thử bỏ lần lượt điểm rải và điểm trộn đặc tính. Chi phí ASYNC giữ chung chỉ tính khi bật ưu tiên tách và ghi căn cứ.
- Ollama `qwen3:4b` chọn các dữ kiện và câu hỏi từ cặp A/B. Studio dựng câu giải thích từ số liệu đã tính. Cách này xử lý trường hợp thử nghiệm ban đầu mô hình đọc ngược chiều chi phí tách kho. Kết quả gắn với cặp phương án và cấu hình đã dùng, có trạng thái cần review.
- Kiểm tra Ticket Support trên trình duyệt cho thấy P011 so với P031 giảm chi phí ASYNC ưu tiên tách nhưng giữ chung từ 1 xuống 0 và tăng chi phí tách dữ liệu từ 0 lên 1. Ollama chọn câu hỏi về giao nhận, độ trễ và lỗi khi `CREATE → ROUTE` qua ranh giới. Lượt kiểm tra cuối hiển thị đề xuất sau khoảng 1,6 giây. Đổi ưu tiên làm bản phân tích cũ hết hiệu lực. Sơ đồ cũng hiển thị Q1 và Q2 cùng phụ trách Trải nghiệm khách hàng trong P031.
- 151 bài kiểm tra cục bộ và CI trên commit triển khai đều qua. [GitHub Actions](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44674102902)

## Chia Quantum theo SYNC — 2026-11-20

- Studio xếp các phương án khả thi theo chi phí SYNC qua ranh giới, chi phí ASYNC giữ chung rồi điểm trọng số. Các chế độ theo trọng số vẫn có trên màn so sánh.
- Kết quả truy characteristic về từng component phụ trách và phân luồng SYNC/ASYNC/UNKNOWN thành nội bộ hoặc qua ranh giới. JSON review lưu cách xếp hạng và các ánh xạ theo phương án.
- Ticket Support mặc định chọn P011. Kiểm tra trình duyệt xác nhận SYNC nội bộ Q2, ASYNC từ Q1 đến Q2 và đổi thứ hạng khi chọn giữ dữ liệu. 144 bài kiểm tra và [CI](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44667341488) qua trên commit `1f3ee3348f30f99827e735c13b6bf315c36bdca8`.

## Sơ đồ tương tác Quantum Studio — 2026-11-19

- Thay tab nhập bảng bằng sơ đồ kéo thả. Chỉnh component, tập characteristics, kho và quan hệ ngay trong sơ đồ. Tách tọa độ bố cục khỏi `Architecture`.
- Vẽ đầu ra từ phân hoạch đã tính, truy vết component, cạnh và phần kho tới Quantum. Giải thích điểm bằng cùng đóng góp chi phí mà bộ giải sử dụng.
- 143 bài kiểm tra qua. Browser smoke kiểm kéo thả, giữ tọa độ, ánh xạ cạnh ASYNC, truy kho tách, sửa characteristic, nối cạnh SYNC và tính lại trade-off. Ca kiểm tra khác Ticket Support đổi từ hai Quantum sang một khi đổi đặc tính.
- [CI](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44554382575) qua trên commit `f50836c40d5aa5bca7bda774b560423d69e25418`.

## Quantum Studio — 2026-11-19

- Entry point mặc định đọc component, quan hệ Sync/Async, kho và characteristics. Bộ giải liệt kê phân hoạch, lọc ràng buộc cứng và so sánh các phương án Pareto.
- Human Review chọn nhanh ưu tiên, xem thứ hạng thay đổi, chọn A/B hoặc yêu cầu chỉnh. Mỗi quyết định lưu cùng mô hình và trade-off tại thời điểm review.
- Ticket Support xét 203 cách chia, giữ 37 cách khả thi và tìm hai phương án tương ứng hình 2 và 3 dưới giả định demo. Giao diện nghiên cứu chuyển sang `research_app.py`.
- 142 bài kiểm tra và compileall qua. Đã mở app cục bộ, kiểm tra hai sơ đồ và đổi ưu tiên trong trình duyệt. [CI](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44491723562) qua trên commit `1f28da61b65bca28afc9fe891d0408e247484fbf`.

## Tutor exploratory demo isolation — 2026-11-19

- Tạo nhánh `feat/tutor-exploratory-demo` từ feature P2 hiện tại, giữ `main`/P0 nguyên trạng. Thêm execution mode `EXPLORATORY_UNBLINDED_DEMO`, UI acknowledgement, storage root tách, demo eligibility trong metadata/manifest và evaluator gate để không nhận demo làm blind data.
- Tutor Ollama proposals chỉ là audit artifacts lúc chờ review. Test-only AppTest đi qua explicit review → policy-derived soft constraint → optimizer → full evidence revision/recompute và hash/snapshot audit; đây là wiring test, không phải inference hoặc human decision thật.
- Bổ sung capture Ollama/model metadata nếu endpoint khả dụng và yêu cầu actor/reason/source nhập thật cho demo review. Sửa trạng thái chờ review để chạy khi optimizer roles còn rỗng.
- Verification: 138 tests pass; compileall và `git diff --check` pass. Commit `f981e55125ddee3f3c10a34d4adb8c4319b3fa04` đã push lên nhánh mới; GitHub Actions [run `44476894324`](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44476894324) completed success trên đúng SHA. Chưa có live inference hoặc stakeholder action; [demo result](../demo/TUTOR_E2E_DEMO_RESULT.md) giữ đúng trạng thái đó.
- Scientific P2 vẫn `P2_BLOCKED_INDEPENDENT_ANNOTATION`; không có semantic metric, gold label hoặc thay đổi P0.

## Automated UI regression — 2026-11-19

- Thêm Streamlit `AppTest` chạy PetClinic offline flow từ load đến đủ 10 pipeline stages, kiểm tra trạng thái fixture, QAME trace chain và `NOT_MEASURED`/`INSUFFICIENT_EVIDENCE`.
- Test cô lập `save_run` và `save_snapshot`, không ghi đè hoặc tạo dữ liệu trong `runs/`.
- Verification: full suite **130 passed**, compileall và diff check passed. Code commit `7e3d1e836eab2b04ee667506a9d2a4a72296f8f8` đã push; [CI 44422385371](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44422385371) success.
- Đây là UI regression cho PetClinic `PRECOMPUTED` fixture; không phải Tutor model inference, reviewer decision, hay bằng chứng semantic correctness.

## QAME allocation edge validation — 2026-11-19

- Tăng `qame_allocations_resolve` từ kiểm tra node sang tính lại liên kết requirement/scenario/responsibility/quantum/interaction mong đợi và kiểm tra từng cạnh, gồm source/target quantum của interaction.
- Thêm adversarial test dùng quantum endpoint không tồn tại; traceability trả `FAIL` thay vì pass khi tham chiếu sai.
- Verification: 129 tests passed; compileall, `git diff --check`, staged secret-pattern scan passed. Code commit `172856cfa718971aa83e0f09986e53ce11534e2b` đã push; [CI 44421428402](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44421428402) success.
- Không thay đổi semantic status, ISO characteristic mapping hoặc measurement; Tutor vẫn thiếu annotation lock/model review thật.

## QAME traceability chain — 2026-11-19

- Traceability graph bổ sung liên kết FR→scenario→responsibility→quantum/interaction→characteristic mapping→measurement state, gồm cả các cạnh endpoint quantum cho interaction.
- Thêm assertions kiểm tra allocations và cạnh QAME; trạng thái `UNMAPPED`, `NOT_MEASURED`, `null` và `NOT_RECORDED` được giữ nguyên khi thiếu human classification/measurement.
- Verification: full suite 129 tests passed; compileall, `git diff --check` passed. Deterministic Tutor fixture replay bằng nhau qua hai lần; in-memory bundle validator `PASS`, 18 members. Code commit `c1e96767f38b6a04083789f630d5d7d9e07b4b25` đã push; [CI 44419855480](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44419855480) success.
- Đây là `PREPARED_FIXTURE` + `DETERMINISTIC_TRANSFORMATION` trong `P2_TEST_ONLY`, không phải LLM output, reviewer decision, ISO classification hay đo lường.
- Manual UI smoke: PetClinic fixture render/run và cả bốn tab hoạt động; Tutor trước lock chỉ hiển thị source-only, P1/P6 ẩn, offline run disabled. Không nhập review hoặc gọi Ollama; local ignored run `runs/run-20261118T232503Z-357cfb32/` được giữ nguyên. Một GraphViz worker fallback warning, không có console error trên trang hiện tại.

## P2 structural evaluator payload guards — 2026-11-19

- Kiểm tra raw requirements, proposal arrays và object rows trước khi evaluator truy cập trường; ID/endpoint/source ID sai kiểu trở thành structural error được nêu tên hoặc dừng bằng `P2ExperimentError` có kiểm soát.
- Thêm adversarial tests cho list/object sai kiểu; không sinh semantic score và không thay `P2_TEST_ONLY` thành model output.
- Verification: 128 tests passed; compileall, `git diff --check`, staged secret-pattern scan passed. Code commit `00be77f5486023d3ad88e1f602b20167d30c710c` đã push; [CI 44417777751](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44417777751) success.

## P2 mapping and citation coverage separation — 2026-11-19

- Sửa `evaluate_p2_structure`: `coverage_by_requirement` đếm FR IDs đã biết độc lập với exact citation resolution; citation invalid vẫn tạo lỗi riêng. FR bị map hợp lệ không còn bị báo nhầm là uncovered chỉ vì citation sai.
- Thêm diễn giải machine-readable xác định coverage này chỉ là cấu trúc, không phải semantic correctness. Không tạo independent labels hoặc accuracy metrics.
- Verification: 126 tests passed; compileall, `git diff --check`, staged secret-pattern scan passed. Code commit `9c7c7337fd9e94b034dd0230ab1bd667282e39af` đã push; [CI 44416779052](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44416779052) success.

## Exhaustive hard-conflict explanations — 2026-11-19

- Khi exhaustive optimizer R1–R8 không có partition khả thi và không có conflict cùng cặp được báo riêng, giảm hard-rule set theo thứ tự ID ổn định để tạo `DELETION_MINIMAL_HARD_CONSTRAINT_CORE`.
- Output nói rõ bỏ từng constraint trong core sẽ khôi phục ít nhất một partition. Không gọi đây là minimum-cardinality core hoặc bằng chứng rằng constraint có justification kiến trúc.
- Verification: 125 tests passed; compileall, `git diff --check`, staged secret-pattern scan passed. Code commit `376e424f3ffcb3a0b9161d256230696b230d4ae3` đã push; [CI 44415600744](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44415600744) success.

## Deterministic evidence-claim audit — 2026-11-19

- Thêm `eqcr.evidence_audit.audit_evidence_records` để báo cáo exact duplicate claim/citation, direct `PRESENT`/`SCOPED_ABSENT` conflict và mixed-with-`UNKNOWN`, đồng thời canonicalize endpoint chỉ khi relation direction khai báo là undirected.
- Constraint policy abstain với mọi evidence ID bị duplicate hoặc conflict; artifact `evidence.audit` lưu nhóm, IDs, trạng thái và giới hạn structural. Không suy ra semantic contradiction, entailment, thời gian/context hay đổi `UNKNOWN` thành vắng mặt.
- Verification: 124 tests passed; `compileall -q app.py eqcr scripts tests`, `git diff --check` và staged secret-pattern scan passed. Code commit `a334fac8b4193c469ed0a1499a1383db4164bdf1` đã push và remote-verified; [CI 44414391706](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44414391706) success.
- Test dùng `P2_TEST_ONLY`; không có reviewer label, case inference hoặc semantic metric mới. `main` và P0 không thay đổi.

## P2.1 browser smoke record — 2026-11-19

- Chạy app Streamlit local và nạp Tutor case; DOM trước lock chỉ hiển thị source-only data, không có helper mappings hay mã proposal P1–P6/E1/B1.
- Sau khi UI phát hiện `qwen3:4b`, nút chạy proposal vẫn disabled do thiếu lock. Không gọi model và không chạy pipeline/reviewer experiment.
- Ghi nhận thủ công trong validation report. Đây không phải automated browser E2E test hoặc kết quả case-level.
- Docs commit `5a2ed9e10b03860037afacdec73818d97370a393` đã push; [CI 44412232466](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44412232466) success.

## P2.1 source-only reviewer package and lock validation — 2026-11-19

- Thêm package Tutor source-only có manifest/hashes và blank 0..N responsibility/relation worksheets; pin lock protocol v3 với manifest hash.
- Thêm CLI chỉ-đọc kiểm package/lock/time-order, từ chối lock timestamp tương lai, và truyền package path rõ ràng vào runner/model proposal path.
- Sửa Input tab Tutor: trước lock chỉ render source-only package, không render raw helper mappings; AppTest kiểm tra payload nhìn thấy. Không tạo lock, inference, human decisions hay semantic metrics thay reviewer.
- Commit code `931dea62472ea459eacd33b1fbe6196eb4e619ce` đã push; [CI run 44410991542](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44410991542) success. Trước push: 121 tests, compileall, diff check, staged-path và credential-pattern scan đều qua. Remote `main` giữ nguyên SHA P0.
- Không có lock annotation do reviewer cung cấp; `qwen3:4b` chỉ được kiểm tra khả dụng. P2 case experiment vẫn `BLOCKED_EXTERNAL`.

## P2/research status recheck — 2026-11-17

- Rechecked the feature branch and remote `main`/P0 ancestry; refreshed the P0–P11 audit, gap matrix, implementation plan, final status report and Ollama-to-optimizer dependency trace. Corrected the prior report's stale statement that interaction-contract review was unavailable in the UI.
- Current checkout before this documentation follow-up was `dbe4a5f417535d11aab9696ff60e593be19b6e1a`; [CI run 44005282683](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/44005282683) passed. Fresh local verification: 114 tests passed and compileall passed.
- Local `qwen3:4b` is installed, but no eligible source-only lock or P2 run bundle exists. No inference, review decision, semantic score or real case revision was created; status remains `P2_BLOCKED_INDEPENDENT_ANNOTATION`.

## Human-reviewed interaction contracts — 2026-11-16

- Added a Human Review JSON editor for complete Sync/Async contracts, exact source-span checks, explicit reviewer/rationale/timestamp, decision/revision records and versioned snapshots. Recomputes interaction, QAME and traceability outputs; the mode does not create optimizer constraints, so partitions remain unchanged by design.
- Updated interaction provenance in run manifests. Source-span mapping is structural only; the editor does not establish semantic entailment or reviewer qualification. No real Tutor interaction decision was supplied.
- Verification: 114 tests passed locally, including UI render, test-only approved contract propagation, invalid citation rejection, audit trace, unchanged partition/QAME behavior and bundle provenance. Compileall and diff checks passed. Commit `8707334310dcd8fb7520b9d519a6023b753143a3` matches the remote feature ref; [GitHub Actions run 43898934609](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43898934609) passed.

## Versioned run artifact bundle — 2026-11-16

- App ZIP exports now include an `EQCR-REPRODUCIBILITY-BUNDLE@1.0.0` manifest, SHA-256 for input/source/review artifacts and each payload, code/runtime/dependency/optimizer metadata, and provenance counts. Missing source rights, versions, reviewer identity or CI result remain unrecorded.
- Added `scripts/validate_artifact_bundle.py` to check member paths, JSON validity, checksum coverage and hashes. The validator does not replay the pipeline or authenticate a bundle.
- Verification: local full suite 110 passed; compileall passed. First CI run `43895817702` exposed a test assumption about absent GitHub environment variables; follow-up test commit `fc477903cef93db892057cb94ccc71e2c27d5103` covers both CI and non-CI metadata. [CI run 43896335329](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43896335329) passed on the final code checkpoint.
- Code commits: `27f556d7087466ca4c97663994077362fe51e6ff` and `fc477903cef93db892057cb94ccc71e2c27d5103`; latest feature ref matches `fc477903cef93db892057cb94ccc71e2c27d5103`. The P2 human experiment remains blocked externally.

## P8–P9 graph, interaction contracts and QAME trace — 2026-11-16

- Added graph schema 1.0.0 with an explicit UNKNOWN Integration layer, a deterministic editable Draw.io export/download, and endpoint/XML tests. Unknown layers are graph-policy placeholders, not system facts.
- Added versioned interaction contract/decision table; pipeline remains UNDECIDED unless a complete cited human decision passes the schema gate. The app has no interaction approval editor.
- Added six-part QAME scenario completeness, source-span/provenance checks and ISO/IEC 25010:2023 `UNMAPPED` status. Prepared fixture values not present in the cited quote remain `UNSUPPORTED`; no measurement is inferred.
- Verification: 104 tests pass; compileall, staged diff check and secret scan pass. [GitHub Actions run 43892678200](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43892678200) passed. Code commit `722c18245e0a7bd7f94674b2fd55c3174785613c` matches the remote feature branch. P2 live experiment remains externally blocked.

## P7 CP-SAT partition optimizer — 2026-11-16

- Added a classical CP-SAT backend for 9–50 responsibility IDs while retaining exhaustive enumeration through R8. The backend proves the objective minimum, reports a capped optimal subset, and marks whether optimum enumeration completed; it does not enumerate/count every feasible partition.
- Added oracle, transitivity, infeasibility explanation, deterministic setting, sensitivity, truncation and pipeline traceability tests. Added a Vietnamese mathematical description and updated capability/limitation reports. No runtime/quality benchmark or Tutor human decision is claimed.
- Verification: 19 focused optimizer tests and 97 full-suite tests pass; compileall, staged whitespace check and staged secret-pattern scan pass. [GitHub Actions run 43887720769](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43887720769) passed. Code commit `91b6b2e733bf7aa8ac36a400bda0123c9377cd44` is pushed and matches the remote branch ref.

## P6 versioned experimental policy evaluation — 2026-11-16

- Thay hai policy rời bằng catalog Tutor Support có catalog/rule version, provenance nội bộ, quality driver, assumptions, điều kiện abstain và chỉ cho phép soft constraints.
- Thêm rule-evaluation trace cho từng policy/evidence pair: `APPLIED`, `NOT_APPLICABLE`, hoặc `ABSTAINED` kèm lý do, source IDs, responsibility endpoints, versions và constraint ID. Explicit constraint override được ghi là catalog bị bypass; P0 không nhận field P2-only.
- Catalog được đánh dấu `NOT_INDEPENDENTLY_VALIDATED`; đây là rule nội bộ thử nghiệm, không phải tactic được xác nhận. UNKNOWN evidence và citation sai có test abstain.
- Verification: 78 tests pass; compileall và staged diff check pass; secret scan không có match; [GitHub Actions run 43882340244](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43882340244) success. Commit `ab26975b3bf9b8f2f8635ac825211a2a7a972ff6` đã push, remote SHA khớp.

## P2 reproducible experiment runner — 2026-11-16

- Bổ sung protocol lock v2 với timestamp timezone-aware và hash integrity cho metadata; ghi rõ identity và việc chưa tiếp xúc model là tự khai báo, không xác minh bên ngoài.
- Thêm CLI preflight để chỉ gọi Ollama khi có source-only lock hợp lệ, checkout sạch, đúng `qwen3:4b`, prompt/schema và metadata model; xuất proposal, structural audit, manifest, checksums và ZIP vào thư mục run mới.
- Structural audit chỉ kiểm tra ID/span, coverage, duplicate và lỗi định dạng; semantic correctness vẫn `NOT_MEASURED` khi thiếu nhãn độc lập. Không chạy inference vì chưa có annotator đủ điều kiện cung cấp lock.
- Verification: 72 tests pass; compileall và `git diff --check` pass; secret scan staged không có match; [GitHub Actions run 43849233685](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43849233685) success. Commit `1fe23ed7886e02b02e44e5ebb850e1b1e6dd6628` đã push và khớp remote branch SHA.

## Research completion capability audit — 2026-11-16

- Audited the actual feature-branch modules, schemas, docs, tests, CI and P0 tag against the research-completion prompt. Added a P0–P11 capability audit, implementation gap matrix and staged implementation plan under `docs/research/`.
- Confirmed the bounded current strengths: P0/P1 local flow and six-role partition oracle; P2 protocol/wiring tests; exhaustive optimizer up to R8; graph JSON, interaction hypotheses, QAME allocation and snapshot ZIP exports.
- Recorded gaps without relabeling them complete: actual independent Tutor experiment, versioned tactic catalog, CP-SAT path, six-part ISO-mapped scenario validation, measurement adapters, integration-layer graph, editable Draw.io, and full reproducibility manifest.
- Verification: relative links in the audit docs resolve; staged diff and secret/path checks pass. Commit `93c7edc06c25d9fd39cdf48355ca31377d5ec8d1` is on `feat/p1-semantic-validation`; [GitHub Actions run 43846206356](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43846206356) passed.

## P2 blind annotation and causal review protocol — 2026-11-16

- Tách source-only annotation khỏi post-lock model review, thêm checkpoint hash/thời gian trước inference, cardinality 0..N cho FR-role mapping, relation registry cố định và action `APPROVE/CORRECT/REJECT/DEFER`.
- Chỉ evidence relation đã qua human review, có implication kiến trúc riêng và responsibility pairs tường minh mới được policy đã khai báo chuyển thành soft optimizer constraint. Business ordering không tự sinh constraint.
- Thêm exact-citation checks, unknown-relation rationale gate, regression coverage, và hai artifact canonical `P2_BLIND_ANNOTATION.md` / `P2_MODEL_REVIEW.md`; giữ `HUMAN_REVIEW_WORKSHEET.md` là lối vào tương thích.
- Verification: 63 tests pass; compileall và staged diff/secret/path checks pass. Commit `1ec2c1b649901873a12cb43dba703bf7a723a411` được push lên `feat/p1-semantic-validation`; [GitHub Actions run 43841700612](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/43841700612) success.
- Case study thật vẫn chờ source-only annotation do người review cung cấp, inference `qwen3:4b` sau lock, model-review decisions và revision experiment. Test-only wiring không được trình bày như kết quả LLM; chưa có semantic metric.

## P2 Tutor Support initial prototype (pre-blind protocol) — 2026-11-16

- Added a new source-backed Tutor Support case, live local `qwen3:4b` extraction path, explicit review gate, policy-based evidence constraint derivation, optimizer input tracing, and downstream interaction/quality generation.
- Added the independent human-review worksheet and documented the actual live run, proposal limitations, provenance, and test-only before/after revision path. The actual case still awaits human decisions; no semantic metric is claimed.
- Verification before publish: 54 tests pass; compileall and staged diff checks pass. Commit `4bbdb03d419ab6b556e3447de0b2130dd3f95fdb` was pushed to `feat/p1-semantic-validation`; GitHub Actions run `43818037929` passed tests and compile.
- Historical v6 model output was unblinded and pre-protocol; its self-referential evidence was not accepted and the run produced zero accepted evidence-derived constraints. It is preserved as `UNBLINDED_EXPLORATORY_PRE_PROTOCOL`, not as a blind experiment. See the [P2 validation report](../p2/P2_VALIDATION_REPORT.md) and [source-only blind annotation](../p2/P2_BLIND_ANNOTATION.md).

## P1 semantic-validation branch — 2026-11-14

- Added an independent six-item partition oracle and negative validation tests for citation spans, evidence support, unknown references, and malformed project JSON.
- Added a provenance graph across inputs, model proposals, evidence, constraints, partitions, quality allocations, and human decisions; graph PASS is limited to structural checks.
- Added a labeled synthetic workshop fixture and an empty annotation worksheet; no expert labels or semantic metric claims were added.
- P1 verification: 44 automated tests pass, compileall passes, Streamlit AppTest has zero exceptions; one local qwen3:4b proposal run resolves exact spans and remains REVIEW_REQUIRED. See [P1 evaluation](../verification/P1_SEMANTIC_EVALUATION.md).
- Implementation commit `f14b534` was pushed to `feat/p1-semantic-validation`; GitHub SHA and private visibility are recorded in [publish log](GITHUB_PUBLISH_LOG.md).
- Added a read-only Ubuntu 24.04/Python 3.13 GitHub Actions workflow for pytest and compileall. Runs `43609423803`, `43609612692`, `43609850489`, and final run `43610739439` passed; latest run has 44 tests and compileall green.
- Browser walkthrough verified baseline → H4 conflict → H3 correction, graph refresh, ZIP with traceability/snapshots, and ten-step JSON report. UI status copy now accurately states that a human correction recomputes the full pipeline.

Các mục dưới đây ghi nhận thay đổi đã được kiểm tra, không phải kế hoạch.

## 14/11/2026 — Baseline P0

- Bảo toàn ứng dụng P0, regression tests, tài liệu và quy trình chạy cục bộ.
- Tạo .gitignore an toàn; thêm docs/verification/P0_BASELINE_VERIFICATION.md.
- Bằng chứng: 30 tests pass; compileall, AppTest và HTTP localhost pass; fixture 203/10; xung đột H3/H4 không có nghiệm; tắt H3 còn năm candidate.
- Commit: `3d517b1a39158e539239dc73d594bc0938649feb` — chore: establish verified P0 research MVP baseline.
- Push main và tag p0-demo-2026-11-14 đã xác minh trên repo Private. Xem GITHUB_PUBLISH_LOG.md.
## 14/11/2026 — Tài liệu kỹ thuật tiếng Việt

- Tạo hướng dẫn đọc, phạm vi RQ1–RQ4, giải thích nguồn thực tế của pipeline 10 bước, kiến trúc, schema/provenance, validation, human-in-the-loop, walkthrough PetClinic, demo và roadmap; thêm AGENTS.md.
- Làm README và tài liệu runtime/test/review hiện có nhất quán với code và kết quả P0. Đổi đường dẫn demo sang docs/08_MVP_DEMO_SCRIPT.md.
- Commit: 0dbd90675beb193c92d4fd06bd7ccf4bf95c61f3 — docs: explain implemented ten-step architecture pipeline.
- Kiểm tra: 30 tests pass (1.10s), compileall PASS, AppTest zero exceptions, 21 Markdown files không có relative link hỏng, localhost health/root HTTP 200; staged secret scan không có match.
- Push nhánh main được GitHub xác nhận cùng SHA; CI chưa có workflow.
## 19/11/2026 — Tutor unblinded demo run

- Connected the Tutor demo UI to the actual local qwen3:4b service and recorded run run-20261119T071904Z-ebd8fd64, its input/raw-response hashes, digest, prompt version, exact citation audit and all ten pre-review stage states.
- The model returned 6 responsibility proposals, 2 relation proposals and 1 boundary hypothesis. No reviewer decisions were entered, so 0 responsibilities and constraints reached the optimizer; 0 partitions were enumerated. The UI remains at Human Review.
- Corrected the validation report so a case without UNKNOWN evidence marks that assertion NOT_APPLICABLE instead of false. Added regression coverage; 139 tests and compileall passed.
- Code commit 4a8b1a41f0f8eadea37d56e49dc68c1570fb3847 was pushed; GitHub Actions run 44479878846 passed. The live run remains local and excluded from blind research.
