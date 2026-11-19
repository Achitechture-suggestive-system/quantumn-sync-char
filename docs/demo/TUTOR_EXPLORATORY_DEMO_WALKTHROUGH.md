# Chạy Tutor Exploratory Demo (unblinded)

## Giới hạn trước khi bắt đầu

Tutor demo hiện là `EXPLORATORY_UNBLINDED_DEMO`: model output được hiển thị cho người review, không có gold labels, không tính semantic score và luôn `EXCLUDED_FROM_BLIND_RESEARCH`. P2 blind path vẫn yêu cầu source-only annotation lock riêng; không dùng demo để tạo hoặc thay lock đó.

Case input là prepared Tutor Support package trong `eqcr/tutor_support.py`, gồm sáu FR, bốn WF và hai quality scenarios. Nó không phải yêu cầu được thu thập từ một tổ chức thật.

## Thao tác giao diện

1. Chạy `.\.venv\Scripts\python.exe -m streamlit run app.py` trong PowerShell.
2. Chọn **Load Tutor Support P2 case**. Màn hình source-only hiển thị FR, workflow và scenario; không thay đổi `main`/P0.
3. Chọn **Exploratory demo (unblinded; excluded from research)**. Đọc cảnh báo `EXPLORATORY_UNBLINDED_DEMO | NO_GOLD_LABELS | SEMANTIC_EVALUATION_NOT_PERFORMED`.
4. Người vận hành tự đánh dấu xác nhận unblinded rồi bấm **Check local Ollama models**. Nếu Ollama không chạy hoặc `qwen3:4b` chưa có, khởi động Ollama/cài model rồi thử lại. Không có offline fallback nào được gọi là live inference.
5. Chọn đúng `qwen3:4b` và bấm **Run local Ollama proposals**. Ứng dụng gửi source FR + workflow/scenario context tới Ollama cục bộ, lưu request metadata, model digest/version nếu có, thời gian inference và hash input. Không dùng câu trả lời cũ hoặc fixture proposal.
6. Ứng dụng hiển thị proposal, relation, boundary hypotheses và audit citation/duplicate/registry. `REVIEW_REQUIRED` giữ nguyên. Ở lần chạy này, trách nhiệm model chưa vào optimizer: stage 5 phải không có candidate cho tới khi người dùng review.
7. Mở **Human Review & Validation**. Duyệt từng responsibility/relation/boundary bằng `APPROVE`, `CORRECT`, `REJECT` hoặc `DEFER`; nhập lý do thật, nguồn và mã người vận hành thật. Với relation, chọn implication kiến trúc riêng và trách nhiệm R cụ thể. Không approve nếu nguồn không hỗ trợ hoặc cách hiểu mơ hồ.
8. Bấm **Apply demo stakeholder review & recompute all stages**. Chỉ responsibility và evidence relation được người review chấp nhận/correct mới đi vào pipeline. Catalog chính sách thử nghiệm có thể sinh soft co-location/separation preference; business ordering không sinh constraint.
9. Kiểm tra `partitions`, `quanta`, `interactions`, `quality_profiles`, `traceability`, `validation_report`, manifest/export. Hard constraints hiện có phải được thỏa; interaction mode vẫn `UNDECIDED` nếu thiếu contract review; quality vẫn `NOT_MEASURED` khi chưa có phép đo.
10. Trong **Revise an approved evidence relation**, xem lại FR/source span, sửa quan hệ hoặc endpoint nếu có căn cứ, nhập rationale và source. Nộp để chạy lại toàn pipeline. Revision audit lưu actor role `DEMO_STAKEHOLDER`, timestamp, old/new, source IDs, run/revision IDs, input/code/config/output hashes, snapshots và artifact diff.

Nếu người dùng chưa thực hiện bước 7 hoặc bước 10, trạng thái dừng ở `AWAITING_DEMO_REVIEW` hoặc sau review nhưng chưa có revision. Không ghi nhận quyết định thay người dùng.

## Cách đọc export

- Demo runs và snapshots được lưu riêng dưới `runs/demo-unblinded/<run-id>/`.
- Manifest và artifact metadata ghi mode và `EXCLUDED_FROM_BLIND_RESEARCH`.
- ZIP checksum xác nhận nội dung package không bị sửa sau export; không xác thực danh tính, semantic correctness hoặc run replay.
- Proposal citation map chỉ xác nhận ID/span trỏ vào source package. Điều đó không chứng minh trách nhiệm/relation được hiểu đúng.
- Partition là nghiệm của objective/policy khai báo. Đây là tối ưu toán học cho input đó, không chứng minh kiến trúc tốt hoặc deployable.

## Offline và blind workflow

PetClinic vẫn là deterministic `PRECOMPUTED` path không cần Ollama. Nếu Ollama không khả dụng, demo không được thay bằng PetClinic hay fixture outputs. Blind Tutor workflow ở mode `P2_BLIND_RESEARCH` tiếp tục khóa trước inference và chỉ dành cho source-only reviewer đủ điều kiện; người đã xem demo cần công khai exposure và không tự mô tả là blinded reviewer.
