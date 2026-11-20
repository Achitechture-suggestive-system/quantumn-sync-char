# Quantum Studio

## Demo trong 60 giây

1. Mở app và kéo component hoặc kho trong **Sơ đồ đầu vào**. Bấm component để sửa tập characteristics. Dùng **Nối** rồi chọn hai đầu để tạo cạnh. Bấm nhãn cạnh để đổi Sync/Async, mức ảnh hưởng và căn cứ. Dùng **Bắt buộc tách** để thêm cặp có ràng buộc.
2. Bấm **Phân tích sơ đồ**. Chọn phương án trong **Sơ đồ đầu ra**. Mỗi nhóm có mục **Characteristics** ngay dưới mã Quantum. Mục này liệt kê các đặc tính, component phụ trách và các Quantum cùng phụ trách nếu có. Bấm component hoặc kho để truy vết. Cạnh nâu chấm nối các phần của kho cần đồng bộ.
3. **Chia theo SYNC** là chế độ mặc định. Xem mục **Characteristics và luồng theo Quantum** để biết component nào phụ trách mỗi đặc tính, cạnh SYNC nào nằm trong nhóm và cạnh ASYNC nào qua ranh giới. Bấm **Ưu tiên giữ dữ liệu** hoặc **Ưu tiên tập trung đặc tính** để thử cách xếp theo trọng số.
4. Xem **Độ nhạy với điểm characteristic** để thử lần lượt bỏ phần phạt rải hoặc phạt trộn. Nếu có Ollama, bấm **Phân tích trade-off với qwen3:4b** để xem lợi ích, đánh đổi và câu hỏi review có dẫn mã dữ kiện.
5. Trong **Human Review**, bấm **Chọn A**, **Chọn B** hoặc nhập điều cần sửa rồi chọn **Yêu cầu chỉnh**. Quyết định lưu cùng đầu vào, trọng số, phương án và điểm tại thời điểm review. Có thể tải bản JSON và sửa mô hình để phân tích lại.

## Pipeline

| Bước | Dữ liệu và quyết định |
|---|---|
| 1. Nhập mô hình | Khai báo 1–8 component và các tập characteristics, cạnh có hướng SYNC/ASYNC/UNKNOWN, kho dùng chung và cặp bắt buộc tách. Mỗi chính sách giữ hoặc tách kho dùng chung có căn cứ. |
| 2. Loại vi phạm | Liệt kê mọi cách chia, mỗi component vào đúng một nhóm. Loại phương án tách giao dịch cục bộ, tách kho KEEP_SHARED hoặc gom cặp bắt buộc tách. Nếu hết phương án, báo INFEASIBLE. |
| 3. Tính trade-off | Tính tiền phạt theo bảng dưới. Cạnh UNKNOWN được giữ trong sơ đồ, với cảnh báo và trạng thái cần xác nhận. |
| 4. Xếp hạng | Tính biên Pareto theo năm chi phí. **Chia theo SYNC** so lần lượt tổng mức ảnh hưởng SYNC bị cắt, tổng mức ảnh hưởng ASYNC được đánh dấu ưu tiên tách nhưng còn giữ chung, rồi điểm trọng số. Hai nút ưu tiên còn lại so điểm trọng số ngay. Nếu hòa, ưu tiên ít nhóm hơn rồi theo ID. |
| 5. Phân bổ characteristics và luồng | Với mỗi Quantum, lấy hợp các tập characteristics của component trong nhóm và ghi component đóng góp cho từng đặc tính. Đánh dấu mọi cạnh là nội bộ hoặc qua ranh giới theo Quantum ở hai đầu. |
| 6. Review và lặp lại | Đổi cách xếp hạng hoặc trọng số. Chọn một phương án hoặc yêu cầu chỉnh. Nếu thay relation, characteristic hoặc chính sách dữ liệu thì phân tích lại sơ đồ. |

Kéo vị trí chỉ đổi bố cục. Khi bấm **Phân tích sơ đồ**, app lưu bố cục trong phiên làm việc và gửi riêng mô hình để giải. Khi sửa thuộc tính, kết quả trước vẫn xem được trong sơ đồ đầu ra với cảnh báo chờ cập nhật. Bảng trade-off và Human Review xuất hiện lại sau khi phân tích mô hình mới hợp lệ.

| Chi phí | Cách tính |
|---|---|
| SYNC qua ranh giới | Cộng mức ảnh hưởng của mỗi cạnh SYNC bị cắt. Giao dịch cục bộ tách ra sẽ bị loại từ bước 2. |
| Tách dữ liệu | Với từng kho SPLITTABLE, lấy mức ảnh hưởng nhân với số Quantum dùng kho trừ một. Khi tách, người thiết kế cần chốt quyền ghi, độ trễ dữ liệu và cách đối soát. |
| ASYNC ưu tiên tách nhưng giữ chung | Chỉ cộng mức ảnh hưởng của cạnh ASYNC có hai đầu ở cùng nhóm khi người nhập bật **Ưu tiên tách ASYNC** và điền căn cứ. Ví dụ là hai bên cần triển khai độc lập và nghiệp vụ chấp nhận xử lý sau. Trường tùy chọn này mặc định tắt, kể cả khi nạp đầu vào được tạo trước đây. |
| Một characteristic bị rải | Cộng số Quantum chứa characteristic đó trừ một, cho từng characteristic đã gắn. |
| Một Quantum trộn đặc tính | Cộng số characteristic khác nhau trong nhóm trừ một, cho các nhóm có characteristic. Nhóm chưa có characteristic được ghi riêng, nên chi phí 0 không mặc nhiên đạt ánh xạ 1:1. |

Điểm trọng số bằng tổng chi phí nhân với hệ số tương ứng. Hai chi phí về characteristic cùng dùng trọng số **Tập trung đặc tính**. Với **Chia theo SYNC**, điểm trọng số quyết định thứ hạng khi hai tiêu chí đầu bằng nhau. Cạnh SYNC thường có thể đi qua ranh giới nếu bị buộc tách. Chỉ giao dịch cục bộ và các ràng buộc cứng đã khai báo bắt buộc giữ hoặc tách nhóm.

Phần **Điểm phát sinh từ đâu** truy từng khoản điểm về cạnh, kho hoặc characteristic gốc và nêu Quantum liên quan. Các khoản này dùng cùng phép tính với bộ giải và có trong JSON review. Dropdown trên sơ đồ nhận ứng viên do bộ giải tìm từ dữ liệu đang nhập. Hai hình tham chiếu chỉ cung cấp cách minh họa ví dụ Ticket Support.

### Căn cứ từ nghiên cứu và phạm vi điểm

- Kho tách và đặc tính rải dùng cách đếm số nhóm liên quan trừ một, tương ứng với [connectivity metric của KaHyPar](https://publikationen.bibliothek.kit.edu/1000152818). Phần giữ/tách cạnh tương ứng với [weighted correlation clustering](https://erikdemaine.org/papers/Clustering_TCS/) khi đã có căn cứ ưu tiên cho cạnh.
- Chi phí dữ liệu hiện dùng mức ảnh hưởng và số nhóm. Tần suất đọc/ghi, thời gian đồng bộ và độ trễ chạy thật có trạng thái `NOT_MEASURED`. Khi có số liệu, [Cromlech](https://cugola.faculty.polimi.it/Papers/cromlech_2024.pdf) là tham chiếu để tách chi phí đọc từ xa, ghi và đồng bộ bản sao.
- Bảng độ nhạy xếp lại toàn bộ tập khả thi với (R=0) hoặc (M=0) trong điểm trọng số. Ràng buộc và thứ tự ưu tiên của chế độ đang chọn tiếp tục áp dụng.

### Phân tích bằng Ollama

Nút LLM gửi dữ kiện của cặp A/B đang chọn, gồm chính sách xếp hạng, điểm, chênh lệch theo trục, các cạnh đổi vị trí và những khoản chi phí chính. Mô hình chọn mã dữ kiện cho một lợi ích, một đánh đổi và một câu hỏi review theo schema. Studio đối chiếu danh sách mã hợp lệ cho từng mục và dựng lời giải thích từ số liệu của bộ giải. Mỗi nhận xét dẫn mã dữ kiện gốc. Kết quả có trạng thái đề xuất cần review. [JSON schema của Ollama](https://docs.ollama.com/capabilities/structured-outputs)

Điểm, nhóm và đề xuất xếp hạng đến từ bộ giải. Tệp JSON lưu kết quả LLM với mã băm của cặp phương án và cấu hình đã dùng. Đổi phương án hoặc trọng số yêu cầu chạy lại trước khi dùng nhận xét mới. Nếu Ollama lỗi hoặc phản hồi không hợp lệ, app hiển thị lỗi bên cạnh kết quả từ bộ giải.

## Mẫu Ticket Support

Sáu component và ba kho dựa trên các hình. Kiểu tương tác, đặc tính, mức ảnh hưởng và yêu cầu tách LOGIN khỏi ROUTE là giả định demo có thể sửa. Yêu cầu tách này loại phương án gom toàn bộ Customer và Ticket vào cùng nhóm. Cạnh CREATE → ROUTE nét đứt được diễn giải là ASYNC để minh họa. Quy trình đồng bộ ở hình 3 liên quan dữ liệu giữa hai kho.

Trong cấu hình mẫu, bộ giải xét **203** cách chia, giữ **37** cách khả thi và tìm **2** phương án trên biên Pareto.

| Phương án | Quantum | Đánh đổi | Điểm giữ dữ liệu | Điểm tập trung đặc tính |
|---|---|---|---:|---:|
| P031 · Hình 2 | Login + Profile / Creation + Router + Completion / Reporting | Giữ nguyên Ticket DB. Luồng ASYNC còn chung nhóm, một đặc tính trải qua hai nhóm và một nhóm trộn hai đặc tính. | **5** | 9 |
| P011 · Hình 3 | Login + Profile + Creation / Router + Completion / Reporting | Cắt cạnh ASYNC, đạt ánh xạ đặc tính và Quantum 1:1. Tách Ticket DB và cần thiết kế đồng bộ dữ liệu. | 6 | **6** |

Hai sơ đồ được dựng từ nghiệm do bộ giải tìm. Thay đầu vào sẽ thay nghiệm. App dùng thông tin Sync/Async đã khai báo và chừa UNKNOWN cho các quan hệ còn thiếu căn cứ.

**Chia theo SYNC** xếp P011 đầu. Hai phương án đều có chi phí SYNC bằng 0. P011 chuyển cạnh ASYNC `CREATE → ROUTE` qua ranh giới Q1 → Q2, trong khi cạnh SYNC `ROUTE → COMPLETE` vẫn trong Q2. Đặc tính của Q1 là *Trải nghiệm khách hàng*, Q2 là *Nhất quán luồng ticket*, Q3 là *Cô lập tải báo cáo*. Đánh đổi là phải thiết kế đồng bộ Ticket DB giữa Q1 và Q2.

Review do thao tác trên UI được lưu cục bộ dưới `runs/quantum-studio/reviews/`. Mỗi bản ghi chứa cách xếp hạng, trọng số, phương án đã xem, nguồn từng characteristic, vị trí các cạnh, thao tác review, ghi chú và thời điểm.
