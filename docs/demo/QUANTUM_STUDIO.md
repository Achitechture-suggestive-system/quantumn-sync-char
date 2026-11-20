# Quantum Studio

## Demo trong 60 giây

1. Mở app và kéo component hoặc kho trong **Sơ đồ đầu vào**. Bấm component để sửa tập characteristics. Dùng **Nối** rồi chọn hai đầu để tạo cạnh. Bấm nhãn cạnh để đổi Sync/Async, mức ảnh hưởng và căn cứ. Dùng **Bắt buộc tách** để thêm cặp có ràng buộc.
2. Mở **Requirements** dưới sơ đồ đầu vào rồi bấm **+ Requirement**. Điền nội dung, bấm component và chọn mã ở dòng **Gắn requirement** của characteristic tương ứng. Một characteristic trên một component có thể dẫn nhiều nguồn.
3. Bấm **Phân tích sơ đồ**, rồi dùng **Chia theo characteristics** để ưu tiên gom các component cùng đặc tính. **Chia theo SYNC** là chế độ mặc định. **Ưu tiên giữ dữ liệu** và **Ưu tiên tập trung đặc tính** xếp theo điểm trọng số.
4. Trong **Sơ đồ đầu ra**, mỗi Quantum liệt kê characteristics, component phụ trách, mã requirement và các Quantum cùng phụ trách. Bấm mã để mở nội dung nguồn bên đầu vào. Mục **Truy vết requirement** liệt kê toàn bộ liên kết và các requirement chưa gắn cho phương án xếp đầu.
5. Trong **Human Review**, bấm **Chọn A**, **Chọn B** hoặc nhập điều cần sửa rồi chọn **Yêu cầu chỉnh**. Có thể tải bản JSON và sửa mô hình để phân tích lại.

## Pipeline

| Bước | Dữ liệu và quyết định |
|---|---|
| 1. Nhập mô hình | Khai báo 1–8 component và các tập characteristics, requirement có mã, cạnh có hướng SYNC/ASYNC/UNKNOWN, kho dùng chung và cặp bắt buộc tách. Kiểm tra mã requirement được trỏ tới và đặc tính đã gán trên đúng component. |
| 2. Loại vi phạm | Liệt kê mọi cách chia, mỗi component vào đúng một nhóm. Loại phương án tách giao dịch cục bộ, tách kho KEEP_SHARED hoặc gom cặp bắt buộc tách. Nếu hết phương án, báo INFEASIBLE. |
| 3. Tính trade-off | Tính tiền phạt theo bảng dưới. Cạnh UNKNOWN được giữ trong sơ đồ, với cảnh báo và trạng thái cần xác nhận. |
| 4. Xếp hạng | Tính biên Pareto theo năm chi phí. **Chia theo SYNC** so SYNC bị cắt, ASYNC giữ chung, rồi điểm trọng số. **Chia theo characteristics** so chi phí rải đặc tính, chi phí trộn đặc tính, rồi điểm trọng số. Hai nút ưu tiên so điểm trọng số ngay. Nếu hòa, ưu tiên ít nhóm hơn rồi theo ID. |
| 5. Phân bổ characteristics và luồng | Với mỗi Quantum, lấy hợp các characteristics của component trong nhóm và giữ các mã requirement theo từng component phụ trách. Đánh dấu mọi cạnh là nội bộ hoặc qua ranh giới theo Quantum ở hai đầu. |
| 6. Review và lặp lại | Đổi cách xếp hạng hoặc trọng số. Chọn một phương án hoặc yêu cầu chỉnh. Nếu thay relation, characteristic hoặc chính sách dữ liệu thì phân tích lại sơ đồ. |

Kéo vị trí chỉ đổi bố cục. Khi bấm **Phân tích sơ đồ**, app lưu bố cục trong phiên làm việc và gửi riêng mô hình để giải. Khi sửa thuộc tính, kết quả trước vẫn xem được trong sơ đồ đầu ra với cảnh báo chờ cập nhật. Bảng trade-off và Human Review xuất hiện lại sau khi phân tích mô hình mới hợp lệ.

Các characteristic trùng tên trên nhiều component được tính là cùng một đặc tính. Requirement lưu nội dung nguồn và liên kết do người dùng khai báo. Điểm phân nhóm dùng tập characteristics trên component. Khi đổi tên đặc tính, chọn lại mã requirement cho tên mới. Mô hình đã tạo trước khi có requirements vẫn chạy được và hiển thị **Chưa gắn requirement** ở các đặc tính thiếu liên kết.

| Chi phí | Cách tính |
|---|---|
| SYNC qua ranh giới | Cộng mức ảnh hưởng của mỗi cạnh SYNC bị cắt. Giao dịch cục bộ tách ra sẽ bị loại từ bước 2. |
| Tách dữ liệu | Với từng kho SPLITTABLE, lấy mức ảnh hưởng nhân với số Quantum dùng kho trừ một. Khi tách, người thiết kế cần chốt quyền ghi, độ trễ dữ liệu và cách đối soát. |
| ASYNC giữ chung | Cộng mức ảnh hưởng của cạnh ASYNC có hai đầu ở cùng nhóm. Trong chế độ chia theo SYNC, tiêu chí này được so sau SYNC. Trong chế độ xếp theo trọng số, đặt hệ số ASYNC bằng 0 để bỏ đóng góp vào điểm. |
| Một characteristic bị rải | Cộng số Quantum chứa characteristic đó trừ một, cho từng characteristic đã gắn. |
| Một Quantum trộn đặc tính | Cộng số characteristic khác nhau trong nhóm trừ một, cho các nhóm có characteristic. Nhóm chưa có characteristic được ghi riêng, nên chi phí 0 không mặc nhiên đạt ánh xạ 1:1. |

Điểm trọng số bằng tổng chi phí nhân với hệ số tương ứng. Hai chi phí về characteristic cùng dùng trọng số **Tập trung đặc tính**. Trong hai chế độ chia, điểm trọng số quyết định thứ hạng khi hai tiêu chí ưu tiên bằng nhau. Chế độ characteristics có thể chấp nhận thêm chi phí SYNC qua ranh giới để giảm rải hoặc trộn đặc tính. Điều kiện giao dịch cục bộ, kho giữ chung và cặp bắt buộc tách được áp dụng trước bước xếp hạng.

Phần **Điểm phát sinh từ đâu** truy từng khoản điểm về cạnh, kho hoặc characteristic gốc và nêu Quantum liên quan. Các khoản này dùng cùng phép tính với bộ giải và có trong JSON review. Dropdown trên sơ đồ nhận ứng viên do bộ giải tìm từ dữ liệu đang nhập. Hai hình tham chiếu chỉ cung cấp cách minh họa ví dụ Ticket Support.

## Mẫu Ticket Support

Sáu component và ba kho dựa trên các hình. Kiểu tương tác, đặc tính, mức ảnh hưởng và yêu cầu tách LOGIN khỏi ROUTE là giả định demo có thể sửa. Yêu cầu tách này loại phương án gom toàn bộ Customer và Ticket vào cùng nhóm. Cạnh CREATE → ROUTE nét đứt được diễn giải là ASYNC để minh họa. Quy trình đồng bộ ở hình 3 liên quan dữ liệu giữa hai kho.

Trong cấu hình mẫu, bộ giải xét **203** cách chia, giữ **37** cách khả thi và tìm **2** phương án trên biên Pareto.

| Phương án | Quantum | Đánh đổi | Điểm giữ dữ liệu | Điểm tập trung đặc tính |
|---|---|---|---:|---:|
| P031 · Hình 2 | Login + Profile / Creation + Router + Completion / Reporting | Giữ nguyên Ticket DB. Luồng ASYNC còn chung nhóm, một đặc tính trải qua hai nhóm và một nhóm trộn hai đặc tính. | **5** | 9 |
| P011 · Hình 3 | Login + Profile + Creation / Router + Completion / Reporting | Cắt cạnh ASYNC, đạt ánh xạ đặc tính và Quantum 1:1. Tách Ticket DB và cần thiết kế đồng bộ dữ liệu. | 6 | **6** |

Hai sơ đồ được dựng từ nghiệm do bộ giải tìm. Thay đầu vào sẽ thay nghiệm. App dùng thông tin Sync/Async đã khai báo và chừa UNKNOWN cho các quan hệ còn thiếu căn cứ.

**Chia theo SYNC** xếp P011 đầu. Hai phương án đều có chi phí SYNC bằng 0. P011 chuyển cạnh ASYNC `CREATE → ROUTE` qua ranh giới Q1 → Q2, trong khi cạnh SYNC `ROUTE → COMPLETE` vẫn trong Q2. Đặc tính của Q1 là *Trải nghiệm khách hàng*, Q2 là *Nhất quán luồng ticket*, Q3 là *Cô lập tải báo cáo*. Đánh đổi là phải thiết kế đồng bộ Ticket DB giữa Q1 và Q2.

Mẫu có ba requirement minh họa `REQ-01` đến `REQ-03` do Studio chuẩn bị. Để thấy hai chế độ chia cho kết quả khác nhau, đổi characteristic của Ticket Creation từ *Trải nghiệm khách hàng* thành *Nhất quán luồng ticket*, thêm `REQ-04` mô tả yêu cầu về trạng thái lúc tiếp nhận và định tuyến, rồi gắn mã vào characteristic mới. Sau khi phân tích, **Chia theo SYNC** xếp P047 đầu. **Chia theo characteristics** xếp P031 đầu, đưa Ticket Creation và `REQ-04` vào Q2 cùng Ticket Router.

Review lưu cục bộ dưới `runs/quantum-studio/reviews/`. JSON chứa `architecture.requirements` với nội dung nguồn và `characteristic_requirements` trong hồ sơ Quantum của phương án xếp đầu và cặp A/B, cùng điểm, trọng số và quyết định review.
