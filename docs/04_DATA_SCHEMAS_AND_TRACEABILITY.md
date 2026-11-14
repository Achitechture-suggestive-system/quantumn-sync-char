# 04 — Schema dữ liệu và khả năng truy vết

## Nguồn và SourceRef

SourceRef gồm source_id, quote, start, end. Requirement, workflow và scenario giữ reference này. run_pipeline kiểm tra source ID, giới hạn offset và so quote với đúng lát cắt start:end. Offset là vị trí ký tự Python. Kiểm tra chỉ xác nhận liên kết văn bản; không xác nhận nội dung trích dẫn chứng minh cách diễn giải.

Responsibility có requirement_ids/source_refs và review status. Evidence record có subject, predicate, object, status, provenance, refs, rationale và is_assumption. Constraint có hai đầu, relation, hardness, weight, quality_scenario_ids, optional evidence_ids, origin, enabled và rationale. evidence_ids mặc định rỗng; constraint chưa có link tường minh vẫn được lưu là chưa có bằng chứng liên kết, không tự suy diễn từ source_refs.

## Các artifact chính

| Artifact | Trường tiêu biểu | Ý nghĩa |
|---|---|---|
| raw_requirements | case/context, requirements[], workflows[], scenarios[] | Input cùng SourceRef. |
| context | IDs/counts, provenance, normalization proposal tùy chọn | Bản chiếu context; không thay thế nguồn. |
| responsibilities | items[] với R ID, operation, FR refs, review | Responsibility fixture/LLM/human có trạng thái review. |
| evidence | items[] và status có kiểu | PRESENT, SCOPED_ABSENT hoặc UNKNOWN. |
| constraints | items[], conflicts[] | Policy source/what-if/human và trạng thái enabled. |
| partitions | total/feasible/optimal candidates, J, conflicts | Kết quả enumerator cổ điển. |
| quanta | groups, assignment, membership counts, graph | Boundary proposal từ candidate dùng hiển thị. |
| interactions | edges[], options[], contract, selection | Các phương án Pet–Visit; có thể chưa được chọn. |
| quality_profiles | scenarios, refs, responsibilities/quanta, target, metric, measurement | Allocation và trạng thái đo; không phải kết quả benchmark. |
| decisions/revisions | actor, reason, source, before/after, impacts | Audit trail của review/correction. |
| traceability | nodes[], edges[], workflow_mappings[], constraints_without_evidence_links[], unresolved_issues[], assertions | Đồ thị liên kết theo ID, exact source span và dependency. Các nhãn ngoài phạm vi và lý do do người/model cung cấp được giữ rõ nguồn. |
| validation_report | status, steps[], assertions, applicability, limitations | Các gate chạy và phạm vi của chúng. |
| metadata | mode, fixture label/note, provenance | Bối cảnh thực thi. |

Artifact JSON đã lưu đều có artifact_metadata gồm provenance.kind, execution_mode/source_artifacts khi phù hợp, verification_status và verification_scope. Assertion chỉ kiểm tra sự hiện diện của metadata; nội dung scope giới hạn điều được kiểm chứng. review_request ban đầu null. UI gắn metadata khi tạo request; bundle Ollama có model, prompt_version, input_sha256.

## Chuỗi provenance

1. Nguồn đi vào requirements/workflow/scenario và SourceRef; context ban đầu có node riêng.
2. Responsibility và LLM proposal nối tới requirement/span; ứng dụng giải mã nguồn theo ID, không tin span model tự tạo.
3. Evidence nối tới subject/object; context-level `SCOPED_ABSENT` có thể trỏ tới khái niệm ngoài scope. UNKNOWN không bị chuyển thành false.
4. Constraint ghi links đến endpoints, explicit evidence IDs nếu được cung cấp, và candidate partitions thỏa constraint.
5. Quantum, interaction, quality profile nối với quanta/scenario/responsibilities liên quan.
6. Decision nối với đối tượng được review; revision lưu impact và artifacts bị ảnh hưởng.
7. Validation report ghi assertions; graph lưu unresolved references và source-span status.

`traceability.status=PASS` chỉ là cấu trúc graph: node ID/endpoints, links đã khai báo, spans, trạng thái review và candidate membership. `traceability.review_status` vẫn `REVIEW_REQUIRED`; graph không chứng minh semantic entailment, độ đúng của policy, chất lượng kiến trúc hay kết quả vận hành. Constraints H1–H3 của demo vẫn được nêu `NO_EXPLICIT_EVIDENCE_LINK` dù rationale trỏ tới ghi chú what-if.

Không có chuỗi hash mật mã bao trùm mọi artifact. input_sha256 dùng cho input của lời gọi Ollama, không phải chữ ký của cả run.

## Lưu trữ và export

eqcr/storage.py ghi JSON dưới runs/<run-id>/ và snapshots/vN.json. ZIP gồm artifacts của lần chạy và snapshots UI yêu cầu đưa vào. runs/ bị .gitignore loại khỏi Git để không đẩy log/snapshot thô. Nếu cần chia sẻ dữ liệu nghiên cứu, hãy tạo ví dụ đã khử thông tin và ghi provenance riêng.
