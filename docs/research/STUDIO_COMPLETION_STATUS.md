# Theo dõi hoàn thiện Quantum Studio

Mục tiêu đang thực hiện là hoàn thiện dự án theo mười gap trong [báo cáo ngày 26/11/2026](STUDIO_GAP_ANALYSIS_2026-11-26.md), với trích dẫn gắn đúng phạm vi phương pháp. Các mốc triển khai dưới đây phục vụ cùng một mục tiêu.

| Gap | Tiến độ triển khai | Điều kiện còn cần kiểm chứng |
|---|---|---|
| G1 · Ollama theo input hiện tại | Adapter gọi thật cho ISO/component, tương tác và bắt buộc tách. Có request, raw response, metadata và proposal chờ review. UI đã chạy requirement mới, sửa đề xuất và tái tính kết quả. | Còn mở rộng kiểm thử lỗi provider và phạm vi semantics ở G2. |
| G2 · Ngữ nghĩa và mệnh đề | Prompt riêng cho từng tác vụ, quote nguyên văn và danh mục kiểm lại trước khi áp dụng. Các lỗi đề xuất vẫn được giữ để sửa hoặc từ chối. | Cấu trúc mệnh đề, điều kiện, phủ định và đánh giá trên ca mới còn tiếp tục. |
| G3 · Mục tiêu trùng | Review chọn NFR gốc qua `duplicate_of`, ghi rationale và checkpoint. Scoring dùng một mục tiêu, giữ tất cả source IDs. Có kiểm paraphrase bất biến điểm, mục tiêu khác scope độc lập và sửa nguồn yêu cầu review lại. | Tính tương đương ngữ nghĩa do reviewer quyết định. Chưa có bộ nhãn độc lập đánh giá quyết định hợp nhất. |
| G4 · UNKNOWN và điều kiện | Khoảng chi phí theo mode, độ phủ khai báo, review hai đến bốn điều kiện và xếp hạng tùy chọn theo biên trên trên toàn bộ tập khả thi. Nguồn điều kiện đổi làm bằng chứng hết hiệu lực. | Tập mode là giả thuyết do reviewer khai báo. Chưa có xác suất, tương quan mode hay bằng chứng vận hành xác nhận tập điều kiện đầy đủ. |
| G5 · NFR và phép đo | Giữ `NOT_MEASURED`. | Structured scenario, adapter profile và bằng chứng đo hoặc dự đoán phù hợp. |
| G6 · Revision và tải lại | Checkpoint chứa input, proposal, quyết định trước–sau, thời điểm, rationale và trạng thái hiển thị. Sửa nguồn yêu cầu xác nhận lại. Đã tải lại phiên sau khi khởi động lại app và tái tạo P011/8 điểm cùng đặc tính trên sơ đồ. | Còn mở rộng kiểm thử các đường sửa khi bổ sung scenario, conditional interaction và policy. |
| G7 · Policy sửa hard constraint | Giữ bộ chẩn đoán và mô phỏng hiện có. | Quy tắc bảo vệ, ưu tiên sửa và áp dụng thay đổi qua revision. |
| G8 · Bằng chứng boundary | Giữ boundary ở mức ứng viên. | Hợp đồng lỗi/data ownership và mục tiêu vận hành có hệ thống chạy được để kiểm tra. |
| G9 · Backend lớn | Giữ giới hạn hiện tại của Studio. | Adapter objective tương đương, kiểm bộ nhỏ và benchmark backend lớn. |
| G10 · Đánh giá độc lập | Tách dữ liệu test và lần gọi thật trong báo cáo. | Bộ ca mới sau khi chốt prompt, reference labels độc lập và thí nghiệm có adjudication. |

## Mốc A — đầu vào thật, đề xuất và quyết định có lịch sử

- Giao diện **Phân tích yêu cầu hiện tại bằng Ollama** nhận tối đa tám requirement mỗi lần. Người dùng chọn tác vụ ISO/component, tương tác hoặc bắt buộc tách. Ba tác vụ có schema và hướng dẫn riêng. Model chạy qua client Ollama đã cấu hình trong repo.
- Input chưa duyệt giữ nguyên optimizer. Mỗi đề xuất có mã, source hash, catalog hash, quote, vấn đề cấu trúc và trạng thái. Người review có thể approve, correct, reject hoặc defer, với người thực hiện và rationale do phiên khai báo.
- Chỉ quyết định áp dụng được kiểm lại mới tạo allocation, sửa cạnh hoặc thêm quy tắc tách. Metadata không xác nhận danh tính người vận hành bằng cơ chế đăng nhập. Chữ trong nguồn và ý nghĩa của câu vẫn cần reviewer kiểm tra.
- Checkpoint dùng ID duy nhất, lưu parent cùng mô hình trước–sau và proposal. Có đường tải lại mô hình, trọng số, chế độ xếp hạng và bố cục. Nội dung hoặc scope requirement thay đổi làm allocation cũ bị xóa khỏi input hiện hành và proposal cũ thành `STALE`. Bản checkpoint cũ được giữ.
- Xác nhận ISO thủ công cũng có checkpoint. Quote rỗng cần rationale bổ sung. Đây là đường ghi quyết định kiến trúc của người vận hành khi văn bản nguồn chưa diễn đạt đủ.

## Nguồn và giới hạn áp dụng

| Nguồn | Phần được áp dụng | Phần cần được kiểm chứng riêng trong dự án |
|---|---|---|
| [Alturayeif, Ahmad và Hassine, TraceLLM, Requirements Engineering, 2026](https://doi.org/10.1007/s00766-026-00460-1) | Đề xuất link ứng viên theo ngữ cảnh và review, giữ cấu hình/nguồn để tái lập. | Prompt Studio, nhãn ISO và scope component là task riêng, cần tập đánh giá mới. Các điểm số trong bài không được dùng làm kết quả dự án. |
| [Femmer và cộng sự, Rapid Quality Assurance with Requirements Smells, JSS 123, 2017](https://wwwbroy.in.tum.de/~femmer/works/2016-requirements_smells-jss.pdf) | Hướng bổ sung cảnh báo nguồn có dấu hiệu cần đọc kỹ để hỗ trợ review. | Kiểm phủ định và mệnh đề tiếng Việt, lỗi báo nhầm và bỏ sót còn ở phần việc G2. |
| [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs) | Cung cấp schema JSON qua `format` và kiểm tra lại dữ liệu trả về. | Schema bảo đảm hình dạng, còn quote/ID và diễn giải được kiểm ở các bước riêng. |
| [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state) | Tải giá trị widget trong callback trước khi rerender phiên. | Checkpoint bền vững là thiết kế của repo, dùng lưu trữ local bên ngoài WebSocket session. |
| [Barr, Harman, McMinn, Shahbaz và Yoo, The Oracle Problem in Software Testing: A Survey, IEEE TSE 41(5), 2015, 507–525](https://discovery.ucl.ac.uk/id/eprint/1471263/1/06963470.pdf) | Kiểm quan hệ bất biến của chi phí sau một phép biến đổi đầu vào được định nghĩa trước. | Quan hệ `duplicate_of` và chính sách một mục tiêu là thiết kế của Studio. Test tổng hợp không xác nhận hai câu thực tế tương đương ngữ nghĩa. |

## Mốc B1 — danh tính mục tiêu chất lượng

`Review yêu cầu cùng mục tiêu` cho reviewer chọn NFR cần đối chiếu và NFR gốc đã có ánh xạ. Quyết định cần actor và rationale, tạo checkpoint `QUALITY_TARGET_MERGE`. Ánh xạ cũ của nguồn hợp nhất bị gỡ, mục tiêu dùng characteristic và component của bản gốc. Reviewer cần đối chiếu cả điều kiện tải, ngưỡng, actor và scope trước khi chọn. Mô hình không tự gộp theo sự giống nhau của văn bản.

Ví dụ tổng hợp trong `tests/test_studio_quality_targets.py` xác nhận Security cho Customer Profile ở NFR-03, rồi thêm DUP có cùng scope. Hai mục tiêu riêng làm tăng chi phí. Sau review hợp nhất DUP vào NFR-03, toàn bộ kết quả `Analysis` trùng trường hợp chỉ có NFR-03. Hồ sơ vẫn giữ `[NFR-03, DUP]` dưới nhãn `Security · NFR-03`, nên cả hai requirement truy vết tới component và Quantum. Mục tiêu có scope REPORT giữ nhãn riêng cho tới khi có quyết định review.

Tách mục tiêu tạo `QUALITY_TARGET_UNLINK` và yêu cầu xác nhận ánh xạ mới. Sửa nội dung hoặc scope của nguồn gốc/nguồn hợp nhất làm mất hiệu lực quan hệ liên quan. Validator chặn vòng lặp, liên kết thiếu, liên kết qua nhiều tầng và allocation riêng trên nguồn hợp nhất. Hợp nhất một bản gốc vào bản gốc khác chuyển các nguồn phụ thuộc cùng sang đích mới trong một revision. Đây là chính sách kiến trúc và biến đổi xác định được ghi nhận qua Human Review, chưa phải kết quả phân loại tự động của LLM.

Kiểm chứng mốc B1 đạt **168 tests**, bao gồm sáu test mới về scoring, scope độc lập, invalidation, liên kết hợp lệ và đường bấm review/lưu phiên. `compileall` hoàn tất. Không có lần inference mới phục vụ mốc hợp nhất.

## Mốc B2 — bất định của mode tương tác

Với phân hoạch cố định `P`, gọi `J_known(P)` là điểm năm trục hiện có, trong đó chỉ cạnh đã xác định SYNC/ASYNC góp chi phí mode. Đặt `M_e={SYNC,ASYNC}` cho cạnh UNKNOWN chưa có điều kiện được review. Nếu có tập điều kiện còn khớp source hash và quote, `M_e` là các mode trong tập đó. Với mỗi cạnh UNKNOWN, đóng góp giả thuyết là:

```text
c(P,e,m) = weight_e × [lambda_sync × I(m=SYNC và khác Quantum)
                      + lambda_async × I(m=ASYNC và cùng Quantum)]
L(P) = J_known(P) + sum_e min_{m thuộc M_e} c(P,e,m)
U(P) = J_known(P) + sum_e max_{m thuộc M_e} c(P,e,m)
```

Hai đầu mút chính xác cho một phân hoạch trong mô hình cho phép các mode trên mỗi cạnh thay đổi độc lập. Không gán xác suất cho SYNC/ASYNC. Các hard constraints được giữ nguyên. Khoảng có thể bảo thủ nếu các điều kiện giữa nhiều cạnh có tương quan mà mô hình chưa biểu diễn. Nếu tập mode giả định bỏ sót hành vi thật, khoảng cũng chưa bao phủ hành vi đó.

Giao diện hiển thị `[L,U]` trên thẻ và trong bảng. `Ưu tiên chi phí biên trên khi còn bất định` chọn `argmin U(P)` trên **mọi phân hoạch thỏa hard constraints**, với tie-break theo L, số Quantum và ID. Cách này tránh bỏ lỡ một phương án vốn bị trội khi chỉ xét chi phí mode đã rõ. Nhãn Pareto và ma trận năm trục vẫn mô tả chi phí đã xác định. Khi tắt lựa chọn biên trên, ba chế độ xếp hạng cũ dùng chi phí mode đã rõ, cùng cảnh báo và khoảng điểm để reviewer đánh giá phần chưa biết. Hồ sơ chọn phương án ghi chính sách xếp hạng và các khoảng tương ứng.

`Review tương tác theo điều kiện` nhận hai đến bốn nhánh. Mỗi nhánh có tên điều kiện, mode, requirement nguồn và quote nguyên văn. Quyết định có actor/rationale, source hash và checkpoint trước–sau. Chỉ áp dụng trên cạnh không có giao dịch cục bộ bắt buộc. Nguồn sửa làm tập điều kiện mất hiệu lực và quay về hai giả thuyết UNKNOWN. Reviewer có trách nhiệm xác nhận phạm vi bao phủ, tính loại trừ của các nhánh và quan hệ phụ thuộc giữa chúng. Độ phủ hiển thị là số cạnh có mode hoặc tập điều kiện còn hiệu lực trên tổng số cạnh, không phải semantic accuracy.

[Bertsimas và Sim, *The Price of Robustness*, Operations Research 52(1), 2004, 35–53, DOI 10.1287/opre.1030.0065](https://www.mit.edu/~dbertsim/papers/Robust%20Optimization/The%20price%20of%20Robustness.pdf) nghiên cứu tối ưu dưới dữ liệu bất định và mức bảo thủ. Studio dùng tập mode rời rạc và minimax theo biên trên như thiết kế riêng. Chưa triển khai mô hình bất định có ngân sách Γ của bài, nên chưa có bảo đảm xác suất hay kết quả tối ưu của bài chuyển trực tiếp sang dự án.

Kiểm định xác định trong `tests/test_studio_uncertainty.py` liệt kê đủ bốn tổ hợp của hai cạnh UNKNOWN, đối chiếu min/max với L/U cho từng phân hoạch. Test khác chứng minh phương án minimax có thể nằm ngoài biên Pareto của chi phí đã biết. Có test giữ hard rule, từ chối quote sai, giữ giao dịch cục bộ, invalidation khi sửa nguồn và đường bấm review/lưu hồ sơ trên UI. Đây là ca do dự án tạo cho kiểm thử thuật toán.

Regression mốc B2 đạt **174 tests**. `compileall` và kiểm cú pháp JavaScript qua. Browser 8501 nạp OC-09 ở chế độ oracle tổng hợp, hiện P031 `5–7`, P011 `6–8`, P029 `7–9`. Bật xếp theo biên trên vẫn chọn P031 vì biên trên 7 thấp nhất trong 37 nghiệm. Đây là kết quả giữ nguyên có lý do theo mô hình đã khai báo, không phải đề xuất mới của Ollama. Lượt browser không ghi Human Review cho dữ liệu oracle và đã quay lại sơ đồ người dùng.

## Bằng chứng chạy ngày 26/11/2026 cho mốc A

Ollama `0.40.18` với `qwen3:4b`, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`. Ba lời gọi qua adapter đã lưu dưới `runs/quantum-studio/extractions/`. Trong yêu cầu ISO cho OC-02/OC-03, model tạo một ánh xạ quote đúng và một quote lệch nguồn. Lượt tương tác OC-08/OC-10 trả cạnh ASYNC của OC-08, còn quote của OC-10 bị sửa lệch. Lượt tách cho OC-10 chọn đúng hai component nhưng dùng đoạn nói về giao dịch cục bộ, nên reviewer vẫn phải kiểm nghĩa của căn cứ.

Thử thêm `REQ-04` trực tiếp từ UI với nội dung “Khi khách hàng đăng nhập và gửi yêu cầu ở tải 300 lượt mỗi phút, luồng Customer Login và Ticket Creation phải trả mã tiếp nhận trong vòng 900 ms ở p95.” Lời gọi `studio-extraction-0ac9899209d24dad8f6f33fedf82b90b` trả 108 token, đề xuất Reliability cho LOGIN/CREATE và quote chứa `90:00 ms`. Kiểm tra chuỗi con phát hiện quote không khớp và chặn áp dụng bản gốc.

Lượt kiểm thử kỹ thuật dùng actor `AGENT_TECHNICAL_SMOKE_TEST`, chọn `CORRECT`, đổi sang Performance efficiency và quote nguyên văn `phải trả mã tiếp nhận trong vòng 900 ms ở p95`. Với xếp hạng theo trọng số mặc định, P031 có 5 điểm trước áp dụng. Sau áp dụng, P011 đứng đầu với 8 điểm. P031 chấm trên đầu vào mới có 11 điểm. Checkpoint `checkpoint-7e212d4b009645dc91b662c3e827e56c` ghi source hash, run ID, rationale và input trước–sau. Đây là bằng chứng kỹ thuật về truyền dữ liệu qua review, với nhãn độc lập và đánh giá chất lượng còn phải thực hiện theo G10.

Sau khi khởi động lại Streamlit, chọn checkpoint này trong lịch sử đã tái tạo P011/8 điểm và nhãn `Performance efficiency · REQ-04` trên sơ đồ. Regression suite tại mốc này đạt **162 tests**. Các phép test giả lập provider dùng dữ liệu ghi rõ `TEST_ONLY` và lưu dưới thư mục tạm của pytest.
