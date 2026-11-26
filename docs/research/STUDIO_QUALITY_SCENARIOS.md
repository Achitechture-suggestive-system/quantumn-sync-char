# Quality scenario và dự đoán có điều kiện trong Studio

Tài liệu mô tả mốc C1, ngày 27/11/2026. Mô hình dự đoán là thiết kế của dự án, với các giới hạn và giả định được công khai. Chưa có phép đo chất lượng của hệ thống triển khai thực tế.

## Cơ sở và biểu diễn

[Bachmann, Bass và Klein, *Deriving Architectural Tactics: A Step Toward Methodical Architectural Design*, CMU/SEI-2003-TR-004](https://www.sei.cmu.edu/library/deriving-architectural-tactics-a-step-toward-methodical-architectural-design/) trình bày sáu phần scenario và liên hệ tham số của mô hình chất lượng với quyết định kiến trúc. Studio dùng schema `Scenario` hiện có của pipeline nghiên cứu, bổ sung scope chịu trách nhiệm, đường đi, target, giả định thời gian và quyết định review. Các công thức cộng bound bên dưới là lựa chọn mô hình của repo, không phải thuật toán hoặc kết quả thực nghiệm được lấy nguyên từ báo cáo SEI. [PDF, mục 2.1 và phần mô hình hóa ở chương 3–4](https://www.sei.cmu.edu/documents/704/2003_005_001_14213.pdf).

| Phần | Nội dung | Nguồn của giá trị |
|---|---|---|
| Nguồn kích thích | Actor hoặc hệ thống gây kích thích | `SOURCE_REQUIREMENT` nếu nguyên văn nằm trong quote, `HUMAN_DECISION` nếu reviewer bổ sung |
| Kích thích | Sự kiện cần xử lý | Cùng quy tắc trên |
| Môi trường | Tải và điều kiện hoạt động | Cùng quy tắc trên |
| Đối tượng bị tác động | Artifact chịu kích thích | Cùng quy tắc trên |
| Phản hồi | Hành vi cần đạt | Cùng quy tắc trên |
| Thước đo phản hồi | Đại lượng và mục tiêu đánh giá | Cùng quy tắc trên |

Ô trống giữ `UNKNOWN`. Reviewer có thể lưu scenario chưa đủ sáu phần, metric chưa có adapter hoặc target chưa biết. Các trường hợp đó giữ `INSUFFICIENT_EVIDENCE` và không sinh giá trị dự đoán. Quote/span và hash chỉ xác nhận nhất quán với bản nguồn đã review, không chứng minh diễn giải đúng.

Target thời gian dùng một số dương và đơn vị ms/s/min. Đoạn `scenario.target` phải nằm trong SourceRef và chứa đúng cặp số–đơn vị trước khi đối chiếu. Kiểm số không tìm bằng chuỗi con, nên target 9 không khớp quote 900 ms. Dấu so sánh, phủ định, phạm vi p95 và ý nghĩa của mục tiêu vẫn cần reviewer kiểm.

## Đầu vào được review

- Scope chịu trách nhiệm được khai báo riêng với đường đi tuần tự. Component bối cảnh trên đường đi không tự nhận characteristic.
- Nếu bật **Đưa characteristic và scope chịu trách nhiệm vào phân nhóm**, quyết định scenario thay ánh xạ cùng characteristic của NFR gốc bằng scope đang chọn. `component_profiles` đưa ánh xạ vào năm trục chi phí hiện có, rồi optimizer tính lại phân hoạch.
- NFR đã hợp nhất theo `duplicate_of` dùng bản gốc. Scenario lưu source hash và catalog hash. Sửa nguồn, đổi catalog hoặc xóa component làm dự đoán cũ mất hiệu lực.
- Mỗi timing parameter là một **giới hạn trên giả định đã gồm thời gian chờ** tại môi trường/tải của scenario. Giá trị không có giữ `null`; không tự điền 0. `HUMAN_DECISION` và `PREPARED_FIXTURE` được ghi riêng. Dữ liệu fixture phục vụ kiểm thuật toán, không trở thành observation.
- Actor, rationale, mô hình trước–sau và lựa chọn có gán ISO được ghi trong checkpoint `QUALITY_SCENARIO_REVIEW`. Gỡ scenario tạo `QUALITY_SCENARIO_REMOVED`; ánh xạ ISO đã review vẫn được giữ cho đến khi có quyết định gỡ ánh xạ riêng.

## Adapter phản hồi tuần tự

Đường đi là danh sách component có thứ tự, không lặp. Mỗi cặp kề nhau phải có tương tác đã khai báo. Mode chưa rõ hoặc tập điều kiện có nhiều mode làm adapter giữ chưa đủ căn cứ. Mô hình chưa tự chọn một nhánh có điều kiện để tạo dự đoán thuận lợi.

Với `b_c` là bound riêng của component, `r` là RTT SYNC qua Quantum và `d` là bound chờ/giao nhận ASYNC:

```text
B_business(P) = sum(b_c trên đường đi)
                + sum(r cho mỗi SYNC qua Quantum)
                + sum(d cho mỗi bước ASYNC)
```

Overhead SYNC nội bộ được giả định đã nằm trong bound component. Bound ASYNC bao gồm hàng đợi và giao nhận cho bước tương ứng, áp dụng theo giả định đã khai báo. Các bound phải phù hợp với retry, trạng thái và tải mà reviewer muốn mô hình hóa; adapter không suy ra chúng từ sơ đồ.

Nếu mốc đo là **Trả phản hồi cho bên gọi**, adapter dừng tại cạnh ASYNC đầu tiên, cộng bound ghi nhận hàng đợi và không cộng xử lý component đích/phía sau. Nếu mốc là **Hoàn tất nghiệp vụ**, adapter tính cả các bước đó. Dừng sớm chỉ đúng dưới giả định caller thực sự được trả sau khi ghi nhận hàng đợi; mode ASYNC của một cạnh tự nó chưa chứng minh hợp đồng nghiệp vụ này.

Không cộng các quantile riêng thành p95 của toàn luồng. Đây là phép cộng các bound giả định. Nếu tất cả bound và cách ghép đều có hiệu lực thì tổng là bound có điều kiện cho đường đi; chưa có bằng chứng rằng các bound nhập vào mô tả hệ thống thực tế.

## Adapter khôi phục tuần tự toàn Quantum

Reviewer chọn một component bị tác động. Với `Q(P,c)` là Quantum chứa component này:

```text
B_recovery(P,c) = detection_bound + sum(recovery_bound_i cho i thuộc Q(P,c))
```

Đây là policy mô hình **toàn Quantum khởi động lại tuần tự**, không phải suy luận tự động về failure domain của production. Recovery bound từng component phải gồm phục hồi trạng thái/phụ thuộc cần thiết. Nếu thiếu bound của một component cùng Quantum, dự đoán giữ chưa đủ căn cứ. Chưa mô hình hóa khôi phục song song, shared infrastructure hoặc lỗi lan qua nhiều Quantum. G8 còn cần hợp đồng và bằng chứng vận hành.

## Đầu ra và cách đọc

Profile ghi source/span, scope→Quantum, sáu phần scenario, model version, provenance của giả định, từng đóng góp thời gian, target và các vấn đề còn thiếu.

| Trường | Ý nghĩa |
|---|---|
| `prediction_status=PREDICTED_UPPER_BOUND` | Đủ đầu vào cho mô hình đã khai báo, tính được bound có điều kiện |
| `UPPER_BOUND_WITHIN_TARGET` | Bound giả định nằm trong ngưỡng nguồn đã review |
| `UPPER_BOUND_EXCEEDS_TARGET` | Bound giả định vượt ngưỡng; chưa chứng minh thời gian thực tế sẽ vượt |
| `INSUFFICIENT_EVIDENCE` / `UNKNOWN` | Chưa đủ đầu vào hoặc căn cứ không còn hiệu lực |
| `measurement_status=NOT_MEASURED`, `measurement=null` | Chưa có quan sát vận hành |

Ngưỡng số hiện thay đổi đối chiếu profile, chưa là một trục hay ràng buộc cứng mới của optimizer. Scope ISO được xác nhận vẫn đi vào bộ giải. Người review dùng profile cùng điểm thiết kế để chọn phương án. Không diễn giải điểm thấp hoặc bound trong target thành quality PASS hay deployability.

## Đối chứng tổng hợp

`tests/test_studio_scenarios.py` dùng input và timing parameters ghi `PREPARED_FIXTURE`:

- Bound CREATE=250 ms, ROUTE=350 ms, RTT=400 ms cho 600 ms khi cùng Quantum và 1.000 ms khi SYNC qua Quantum. Với target 900 ms, hai phương án có kết quả đối chiếu khác nhau.
- Đổi target nguồn 900→9.000 ms làm scenario cũ mất hiệu lực. Sau review lại, bound 1.000 ms giữ nguyên nhưng chuyển sang nằm trong target mới.
- Với ASYNC và bound enqueue=10 ms, delivery=80 ms, phản hồi caller là 260 ms; hoàn tất nghiệp vụ là 680 ms.
- Recovery REPORT=100.000 ms, LOGIN=PROFILE=300.000 ms, detection=5.000 ms cho 105.000 ms khi REPORT riêng và 705.000 ms khi chung Quantum với hai component khách hàng, so với target 10 phút.
- Thiếu một phần scenario, thiếu bound, UNKNOWN mode, target không khớp hoặc adapter chưa có đều không tạo dự đoán. AppTest kiểm review→allocation→optimizer→profile→lưu lựa chọn và gỡ profile có checkpoint.

Các giá trị trên kiểm phép tính và truy vết trên ca do dự án tạo. Không phải kết quả Ollama hoặc phép đo trên kiến trúc triển khai. Đánh giá ngữ nghĩa độc lập và đo vận hành vẫn cần thực hiện riêng.
