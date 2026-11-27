# Quantum Studio

## Demo trong 60 giây

1. Mở app và kéo component hoặc kho trong **Sơ đồ đầu vào**. Bấm component để sửa tập characteristics. Dùng **Nối** rồi chọn hai đầu để tạo cạnh. Bấm nhãn cạnh để đổi Sync/Async, mức ảnh hưởng và căn cứ. Dùng **Bắt buộc tách** để thêm cặp có ràng buộc.
2. Mở **Requirements** dưới sơ đồ đầu vào rồi bấm **+ Requirement**. Chọn loại **NFR**, ghi nội dung, chọn **Component phụ trách** và bấm **Phân tích sơ đồ**. Bạn cũng có thể gắn nguồn cho characteristic thủ công trong trình chỉnh component.
3. Trong **Ánh xạ NFR vào ISO/IEC 25010:2023**, chọn NFR và xem bảng **Tuyến ánh xạ component → Quantum** theo từng phương án. Sửa danh sách **Component ứng viên** rồi bấm **Xác nhận gán ISO** để tính lại cách phân nhóm. Chọn **Chia theo characteristics** để ưu tiên cách nhóm theo đặc tính. **Chia theo SYNC** là chế độ mặc định.
4. Ngay đầu vùng **So sánh phương án**, chọn ứng viên cho A/B/C rồi chọn ô cần vẽ ở **Phương án hiển thị trên sơ đồ**. Sơ đồ đầu ra và hồ sơ truy vết dùng chung lựa chọn đó. Mở **Ưu tiên phân nhóm và trọng số** để đổi cách xếp hạng. **Ma trận chi phí** bên dưới sơ đồ hiện số đơn vị của A/B/C và chênh lệch so với A.
5. Trong **Hồ sơ và truy vết**, mở thẻ **Quantum**, **Tương tác**, **Kho và ràng buộc** hoặc **Requirements**. Thẻ Requirements nối đặc tính với component và Quantum, đồng thời đánh dấu mã chưa gắn. Bạn cũng có thể bấm mã requirement ngay trên sơ đồ để mở nguồn.
6. Trong **Human Review**, bấm **Chọn A**, **Chọn B**, **Chọn C** hoặc nhập điều cần sửa rồi chọn **Yêu cầu chỉnh**. Biên bản hiện lựa chọn, thời điểm và ghi chú. Nút tải xuất hồ sơ JSON.

## Pipeline

Studio hỗ trợ 1–50 component. Các số liệu Bell/Pareto và ID Pxxx bên dưới mô tả luồng liệt kê ≤8. Từ 9–50, UI chuyển sang CP-SAT với thời hạn, ID CP-…, số phương án đã tìm và phạm vi Pareto trong pool. Chưa tìm hết không được đọc là vô nghiệm. [Công thức bảo toàn, cách sửa và benchmark](../research/STUDIO_LARGE_BACKEND.md). Protocol P2 vẫn giới hạn tám responsibility IDs.

| Bước | Dữ liệu và quyết định |
|---|---|
| 1. Nhập mô hình | Khai báo 1–50 component và các tập characteristics, requirement có mã và loại, cạnh SYNC/ASYNC/UNKNOWN, kho dữ liệu và cặp bắt buộc tách. Xác nhận ánh xạ NFR và component để thêm characteristic ISO vào đầu vào bộ giải. |
| 2. Loại vi phạm | Liệt kê mọi cách chia, mỗi component vào đúng một nhóm. Loại phương án tách giao dịch cục bộ, tách kho KEEP_SHARED hoặc gom cặp bắt buộc tách. Nếu hết phương án, báo INFEASIBLE. |
| 3. Tính trade-off | Tính tiền phạt theo bảng dưới. Cạnh UNKNOWN được giữ trong sơ đồ, với cảnh báo và trạng thái cần xác nhận. |
| 4. Xếp hạng | Tính biên Pareto theo năm chi phí. **Chia theo SYNC** so SYNC bị cắt, ASYNC giữ chung, rồi điểm trọng số. **Chia theo characteristics** so chi phí rải đặc tính, chi phí trộn đặc tính, rồi điểm trọng số. Hai nút ưu tiên so điểm trọng số ngay. Nếu hòa, ưu tiên ít nhóm hơn rồi theo ID. |
| 5. Phân bổ characteristics và luồng | Với mỗi Quantum, lấy hợp các characteristics của component trong nhóm và giữ các mã requirement theo từng component phụ trách. Đánh dấu mọi cạnh là nội bộ hoặc qua ranh giới theo Quantum ở hai đầu. |
| 6. Review và lặp lại | So sánh tối đa ba phương án phân hoạch khác nhau. Chọn một phương án hoặc yêu cầu chỉnh. Khi sửa quan hệ, characteristic, requirement hoặc chính sách dữ liệu, phân tích lại sơ đồ. |

Kéo vị trí chỉ đổi bố cục. Khi bấm **Phân tích sơ đồ**, app lưu bố cục trong phiên làm việc và gửi riêng mô hình để giải. Khi sửa thuộc tính, kết quả trước vẫn xem được trong sơ đồ đầu ra với cảnh báo chờ cập nhật. Bảng trade-off và Human Review xuất hiện lại sau khi phân tích mô hình mới hợp lệ.

Các characteristic trùng tên trên nhiều component được tính là cùng một đặc tính. Requirement lưu nội dung nguồn và liên kết do người dùng khai báo. Điểm phân nhóm dùng tập characteristics trên component. Khi đổi tên đặc tính, chọn lại mã requirement cho tên mới. Mô hình đã tạo trước khi có requirements vẫn chạy được và hiển thị **Chưa gắn requirement** ở các đặc tính thiếu liên kết.

Studio ưu tiên phạm vi component đã khai báo trong requirement. Nếu phạm vi để trống, Studio xét liên kết characteristic đã có rồi đến tên hoặc mã xuất hiện trong văn bản. Bảng xem trước đọc vị trí từ từng phân hoạch hiện tại. Sau khi xác nhận đặc tính, vị trí Quantum được tính lại từ mô hình mới. Đổi phạm vi trong trình chỉnh requirement cần xác nhận lại ánh xạ. Phạm vi này cũng nằm trong hồ sơ JSON.

### ISO/IEC 25010:2023 và cách phân tích NFR

- ISO/IEC 25010:2023 có chín **product-quality characteristics**. Đó là Functional suitability, Performance efficiency, Compatibility, Interaction capability, Reliability, Security, Maintainability, Flexibility và Safety. Chất lượng trong sử dụng có mô hình riêng ở ISO/IEC 25019:2023. ISO/IEC 25030:2019 mô tả khung khai thác, định nghĩa và quản trị quality requirements. [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) · [Bản xem trước qua SIST](https://cdn.standards.iteh.ai/sist-preview/78176/13ff8ea97048443f99318920757df124/ISO-IEC-25010-2023.pdf) · [ISO/IEC 25019:2023](https://www.iso.org/standard/78177.html) · [ISO/IEC 25030:2019](https://www.iso.org/standard/72116.html)
- **ADD** dùng yêu cầu chức năng chính, kịch bản chất lượng và ràng buộc để phân bổ trách nhiệm. Áp dụng vào Studio, component đến từ sơ đồ đã khai báo. Bộ đề xuất xác định component được nêu theo tên hoặc ID. Người review bổ sung các component khác khi luồng nghiệp vụ cho thấy chúng tham gia đáp ứng NFR. [Cervantes và Kazman, ADD 3.0](https://www.sei.cmu.edu/library/add-30-rethinking-drivers-and-decisions-in-the-design-process/)
- Các từ chỉ báo là một cách tạo đề xuất NFR đã được nghiên cứu. Studio dùng bộ quy tắc Việt/Anh có thể truy về đoạn chữ khớp. Một NFR có thể khớp nhiều nhãn. Khi thiếu dấu hiệu hoặc phạm vi không rõ, người review chọn nhãn và component. Chưa có tập nhãn độc lập để đánh giá độ chính xác của bộ quy tắc này. [Cleland-Huang và cộng sự, 2007](https://doi.org/10.1007/s00766-007-0045-1) · [Cleland-Huang và Vierhauser, thực nghiệm lặp lại năm 2026](https://link.springer.com/article/10.1007/s00766-026-00479-4)
- **ATAM** truy một quality scenario qua component và connector để tìm rủi ro và trade-off. Ví dụ `NFR-01` nêu artifact là luồng Ticket Creation → Ticket Router, môi trường là tải cao và mục tiêu là p95 không quá 200 ms. Cần định nghĩa tải, điểm bắt đầu và điểm kết thúc của phép đo trong review. Studio ghi chỉ số vận hành là `NOT_MEASURED`. [Kazman, Klein và Clements, ATAM](https://www.sei.cmu.edu/library/atam-method-for-architecture-evaluation/)

Ánh xạ ISO đã xác nhận được tính theo cặp **nhãn ISO + mã NFR**. Ví dụ `Performance efficiency · NFR-01` có phạm vi riêng, ngay cả khi một NFR khác cùng thuộc Performance efficiency. Cách tính này tránh ghép chung mọi component có cùng nhãn ISO cấp cao. Khi sửa nội dung hoặc loại requirement trong sơ đồ, Studio yêu cầu xác nhận lại ánh xạ. Luồng hiện tại ánh xạ ở cấp characteristic.

### So sánh ba phương án

Studio liệt kê hết phân hoạch trong phạm vi tám component, lọc ràng buộc cứng và so Pareto trên năm chi phí. Phương án bị trội có một phương án khác với tất cả chi phí bằng hoặc thấp hơn và ít nhất một chi phí thấp hơn. Ba lựa chọn mặc định ưu tiên biên Pareto, gồm ứng viên xếp đầu và ứng viên theo trọng số mặc định. Nếu biên có dưới ba ứng viên, Studio bổ sung từ tập khả thi và hiện rõ **Ngoài Pareto**, cùng mã phương án trội hơn. Nếu chỉ có một hoặc hai nghiệm khả thi thì hiện số đó. Nghiên cứu tối ưu đa mục tiêu trên mô hình kiến trúc dùng cùng nguyên tắc làm lộ các đánh đổi giữa mục tiêu. Nghiên cứu dưới đây dùng NSGA-II và các thước đo mô hình khác với năm chi phí của Studio. [Cortellessa và cộng sự](https://arxiv.org/abs/2301.09531)

| Chi phí | Cách tính |
|---|---|
| SYNC qua ranh giới | Cộng mức ảnh hưởng của mỗi cạnh SYNC bị cắt. Giao dịch cục bộ tách ra sẽ bị loại từ bước 2. |
| Tách dữ liệu | Với từng kho SPLITTABLE, lấy mức ảnh hưởng nhân với số Quantum dùng kho trừ một. Khi tách, người thiết kế cần chốt quyền ghi, độ trễ dữ liệu và cách đối soát. |
| ASYNC giữ chung | Cộng mức ảnh hưởng của cạnh ASYNC có hai đầu ở cùng nhóm. Trong chế độ chia theo SYNC, tiêu chí này được so sau SYNC. Trong chế độ xếp theo trọng số, đặt hệ số ASYNC bằng 0 để bỏ đóng góp vào điểm. |
| Một characteristic bị rải | Cộng số Quantum chứa characteristic đó trừ một, cho từng characteristic đã gắn. |
| Một Quantum trộn đặc tính | Cộng số characteristic khác nhau trong nhóm trừ một, cho các nhóm có characteristic. Nhóm chưa có characteristic được ghi riêng, nên chi phí 0 không mặc nhiên đạt ánh xạ 1:1. |

Điểm trọng số bằng tổng chi phí nhân với hệ số tương ứng. Hai chi phí về characteristic cùng dùng trọng số **Tập trung đặc tính**. Trong hai chế độ chia, điểm trọng số quyết định thứ hạng khi hai tiêu chí ưu tiên bằng nhau. Chế độ characteristics có thể chấp nhận thêm chi phí SYNC qua ranh giới để giảm rải hoặc trộn đặc tính. Điều kiện giao dịch cục bộ, kho giữ chung và cặp bắt buộc tách được áp dụng trước bước xếp hạng.

Phần **Điểm phát sinh từ đâu** truy từng khoản điểm về cạnh, kho hoặc characteristic gốc và nêu Quantum liên quan. Các khoản này dùng cùng phép tính với bộ giải và có trong JSON review. Bộ chọn A/B/C ở đầu vùng làm việc nhận ứng viên do bộ giải tìm từ dữ liệu đang nhập. Hai hình tham chiếu cung cấp bố cục minh họa cho ví dụ Ticket Support.

## Mẫu Ticket Support

Sáu component và ba kho dựa trên các hình. Kiểu tương tác, đặc tính, mức ảnh hưởng và yêu cầu tách LOGIN khỏi ROUTE là giả định demo có thể sửa. Yêu cầu tách này loại phương án gom toàn bộ Customer và Ticket vào cùng nhóm. Cạnh CREATE → ROUTE nét đứt được diễn giải là ASYNC để minh họa. Quy trình đồng bộ ở hình 3 liên quan dữ liệu giữa hai kho.

Trong cấu hình mẫu, bộ giải xét **203** cách chia, giữ **37** cách khả thi và tìm **2** phương án trên biên Pareto.

| Phương án | Quantum | Đánh đổi | Điểm giữ dữ liệu | Điểm tập trung đặc tính |
|---|---|---|---:|---:|
| P031 · Hình 2 | Login + Profile / Creation + Router + Completion / Reporting | Giữ nguyên Ticket DB. Luồng ASYNC còn chung nhóm, một đặc tính trải qua hai nhóm và một nhóm trộn hai đặc tính. | **5** | 9 |
| P011 · Hình 3 | Login + Profile + Creation / Router + Completion / Reporting | Cắt cạnh ASYNC, đạt ánh xạ đặc tính và Quantum 1:1. Tách Ticket DB và cần thiết kế đồng bộ dữ liệu. | 6 | **6** |

Hai sơ đồ được dựng từ nghiệm do bộ giải tìm. Thay đầu vào sẽ thay nghiệm. App dùng thông tin Sync/Async đã khai báo và chừa UNKNOWN cho các quan hệ còn thiếu căn cứ.

**Chia theo SYNC** xếp P011 đầu. Hai phương án đều có chi phí SYNC bằng 0. P011 chuyển cạnh ASYNC `CREATE → ROUTE` qua ranh giới Q1 → Q2, trong khi cạnh SYNC `ROUTE → COMPLETE` vẫn trong Q2. Đặc tính của Q1 là *Trải nghiệm khách hàng*, Q2 là *Nhất quán luồng ticket*, Q3 là *Cô lập tải báo cáo*. Đánh đổi là phải thiết kế đồng bộ Ticket DB giữa Q1 và Q2.

Mẫu có ba requirement `REQ-01` đến `REQ-03` và ba NFR minh họa. `NFR-03` yêu cầu mã hóa dữ liệu hồ sơ khi truyền. Phạm vi khai báo chọn Customer Profile, nên Studio đề xuất tuyến đến Q1 trong các phương án mặc định. Trong **Chia theo characteristics**, xác nhận đề xuất *Performance efficiency* của `NFR-01` cho Ticket Creation và Ticket Router. Kết quả xếp đầu đổi từ P011 sang P031. Bộ chi phí dưới đây theo thứ tự **SYNC, tách kho, ASYNC giữ chung, rải, trộn** với trọng số mặc định **3, 6, 1, 2, 2**.

| Phương án | Quantum | Chi phí | Điểm | Trade-off sau xác nhận NFR-01 |
|---|---:|---|---:|---|
| P031 | 3 | 0, 0, 1, 1, 2 | 7 | Q2 giữ chung Ticket Creation, Router và Completion, giữ cả hai component của NFR-01 và Ticket DB trong cùng nhóm. Luồng ASYNC ở nội bộ Q2, còn đặc tính Trải nghiệm khách hàng trải qua Q1 và Q2. |
| P011 | 3 | 0, 1, 0, 1, 2 | 12 | ASYNC tạo ranh giới giữa tiếp nhận và định tuyến. Ticket DB cần đồng bộ giữa Q1–Q2, và hai component hiện thực NFR-01 ở hai nhóm. |
| P029 | 2 | 0, 0, 1, 1, 3 | 9 | Gộp báo cáo vào nhóm tài khoản khách hàng. Số Quantum giảm một và chi phí trộn tăng một so với P031. Studio ghi **Ngoài Pareto**, P031 trội hơn. |

P031 và P011 hòa ở chi phí rải và trộn, dù đặc tính bị rải khác nhau. Điểm phân xử ở bước tiếp theo là 7 và 12. Giữ kho chung tiết kiệm 6 điểm trong cấu hình mặc định, còn giữ ASYNC nội bộ trả thêm 1 điểm. Các điểm này phản ánh mô hình thiết kế và trọng số do Studio dùng.

Review lưu cục bộ dưới `runs/quantum-studio/reviews/`. JSON chứa `architecture.requirements` với nội dung nguồn, `quality_allocations` đã xác nhận, `characteristic_requirements` theo Quantum và dữ kiện so sánh A/B/C. `quality_measurement_status` ghi `NOT_MEASURED`.

## Thử thêm đầu vào do Ollama tạo

Chọn **Requirement Ollama** ở thanh điều hướng, mở **Thêm requirement từ Ollama**, chọn dữ liệu rồi bấm **Nạp requirement đã chọn**. Ba gói gồm tải cao, gián đoạn và tích hợp, có thể nạp riêng hoặc cùng nhau. Tất cả đều nạp dưới dạng requirement nháp. Sau đó chọn mã `LLM-…` ở phần ánh xạ ISO để kiểm tra nhãn, đoạn trích và component, rồi tự xác nhận nếu phù hợp. [Thí nghiệm, nguồn gốc và kết quả](LLM_REQUIREMENT_EVALUATION.md)
