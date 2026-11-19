# Tutor demo unblinded và P2 blind research

| Thuộc tính | Tutor Exploratory Demo | Tutor Blind Research |
|---|---|---|
| Mục đích | Trình diễn model và tác động của quyết định stakeholder lên optimizer/QAME. | Đo lường extraction/review với independent source-only reference labels. |
| Inference gate | Người vận hành xác nhận unblinded; không tạo lock. | Valid source-only annotation lock phải bind đúng input, được xác nhận trước inference. |
| Người review | `DEMO_STAKEHOLDER`; có thể đã thấy model output. | Annotator độc lập, chưa thấy model output; attestation tự khai báo không xác minh identity. |
| Research eligibility | Luôn `EXCLUDED_FROM_BLIND_RESEARCH`. | Có thể bắt đầu blind workflow sau lock; semantic metrics vẫn chờ nhiều reviewer/adjudication theo protocol. |
| Model proposal | Local `qwen3:4b`, nếu người vận hành gọi model thật; không có fixture fallback giả làm inference. | Same pinned tag và lock-first `run_p2_experiment` path. |
| Human disposition | Decision thật của stakeholder demo; không phải gold label. | Reviewer decision sau inference, tách khỏi source-only annotation. |
| Optimizer | Sau human demo review, accepted/corrected evidence có thể sinh constraint theo internal soft policy. | Sau review/adjudication và evidence/policy gates; không được suy từ một reviewer đơn lẻ thành truth. |
| Semantic score | Không tính. | Chỉ sau independent labels, adjudication và matching rules khóa trước; hiện `NOT_MEASURED`. |
| Run storage | `runs/demo-unblinded/<run-id>/`. | Vị trí P2 experiment riêng, không nạp demo export làm blind input. |

Code chặn demo bundle khỏi `validate_p2_proposal_bundle` và `evaluate_p2_structure`. UI hiển thị cảnh báo liên tục, tách storage root, manifest có `EXCLUDED_FROM_BLIND_RESEARCH`, và lock blind vẫn bị từ chối sau khi session đã lộ output. Người đã exposure phải khai báo trung thực; ứng dụng không thể xác minh hoạt động ngoài session/browser.

`P2_BLOCKED_INDEPENDENT_ANNOTATION` vẫn là trạng thái scientific P2 cho tới khi có reviewer độc lập hoàn thành source-only annotation/lock. Dù demo có live inference, human review, candidate partitions và revision thật, những sự kiện đó vẫn không hoàn tất blind experiment hay tạo semantic accuracy score.
