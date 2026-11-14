# 04 — Schema dữ liệu và khả năng truy vết

## Nguồn và SourceRef

SourceRef gồm source_id, quote, start, end. Requirement, workflow và scenario giữ reference này. run_pipeline kiểm tra source ID, giới hạn offset và so quote với đúng lát cắt start:end. Offset là vị trí ký tự Python. Kiểm tra chỉ xác nhận liên kết văn bản; không xác nhận nội dung trích dẫn chứng minh cách diễn giải.

Responsibility có requirement_ids/source_refs và review status. Evidence record có subject, predicate, object, status, provenance, refs, rationale và is_assumption. Constraint có hai đầu, relation, hardness, weight, quality_scenario_ids, origin, enabled và rationale.

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
| validation_report | status, steps[], assertions, applicability, limitations | Các gate chạy và phạm vi của chúng. |
| metadata | mode, fixture label/note, provenance | Bối cảnh thực thi. |

Artifact JSON đã lưu đều có artifact_metadata gồm provenance.kind, execution_mode/source_artifacts khi phù hợp, verification_status và verification_scope. Assertion chỉ kiểm tra sự hiện diện của metadata; nội dung scope giới hạn điều được kiểm chứng. review_request ban đầu null. UI gắn metadata khi tạo request; bundle Ollama có model, prompt_version, input_sha256.

## Chuỗi provenance

1. Nguồn đi vào requirements/workflow/scenario và SourceRef.
2. Responsibility trỏ tới requirement/span; ứng dụng giải mã nguồn theo ID, không tin span model tự tạo.
3. Evidence/constraint lưu origin và rationale; UNKNOWN không bị chuyển thành false.
4. Partitions ghi constraints/responsibilities tham gia.
5. Quantum, interaction, quality profile lưu predecessor/source phù hợp.
6. Decision ghi actor, reason, source, old/new value; revision lưu impact.
7. Validation report ghi assertions và limitations.

Không có chuỗi hash mật mã bao trùm mọi artifact. input_sha256 dùng cho input của lời gọi Ollama, không phải chữ ký của cả run.

## Lưu trữ và export

eqcr/storage.py ghi JSON dưới runs/<run-id>/ và snapshots/vN.json. ZIP gồm artifacts của lần chạy và snapshots UI yêu cầu đưa vào. runs/ bị .gitignore loại khỏi Git để không đẩy log/snapshot thô. Nếu cần chia sẻ dữ liệu nghiên cứu, hãy tạo ví dụ đã khử thông tin và ghi provenance riêng.
