# Quantum Studio

## Demo trong 60 giây

1. Mở app và kéo component hoặc kho trong **Sơ đồ đầu vào**. Bấm component để sửa tập characteristics. Dùng **Nối** rồi chọn hai đầu để tạo cạnh. Bấm nhãn cạnh để đổi Sync/Async, mức ảnh hưởng và căn cứ. Dùng **Bắt buộc tách** để thêm cặp có ràng buộc.
2. Bấm **Phân tích sơ đồ**. Chọn phương án trong **Sơ đồ đầu ra**. Bấm component hoặc kho ở một bên để làm nổi phần tương ứng và Quantum ở bên còn lại. Cạnh nâu chấm nối các phần của kho cần đồng bộ.
3. **Chia theo SYNC** là chế độ mặc định. Xem mục **Characteristics và luồng theo Quantum** để biết component nào phụ trách mỗi đặc tính, cạnh SYNC nào nằm trong nhóm và cạnh ASYNC nào qua ranh giới. Bấm **Ưu tiên giữ dữ liệu** hoặc **Ưu tiên tập trung đặc tính** để thử cách xếp theo trọng số.
4. Trong **Human Review**, bấm **Chọn A**, **Chọn B** hoặc nhập điều cần sửa rồi chọn **Yêu cầu chỉnh**. Quyết định lưu cùng đầu vào, trọng số, phương án và điểm tại thời điểm review. Có thể tải bản JSON và sửa mô hình để phân tích lại.

## Pipeline

| Bước | Dữ liệu và quyết định |
|---|---|
| 1. Nhập mô hình | Khai báo 1–8 component và các tập characteristics, cạnh có hướng SYNC/ASYNC/UNKNOWN, kho dùng chung và cặp bắt buộc tách. Mỗi chính sách giữ hoặc tách kho dùng chung có căn cứ. |
| 2. Loại vi phạm | Liệt kê mọi cách chia, mỗi component vào đúng một nhóm. Loại phương án tách giao dịch cục bộ, tách kho KEEP_SHARED hoặc gom cặp bắt buộc tách. Nếu hết phương án, báo INFEASIBLE. |
| 3. Tính trade-off | Tính tiền phạt theo bảng dưới. Cạnh UNKNOWN được giữ trong sơ đồ, với cảnh báo và trạng thái cần xác nhận. |
| 4. Xếp hạng | Tính biên Pareto theo năm chi phí. **Chia theo SYNC** so lần lượt tổng mức ảnh hưởng SYNC bị cắt, tổng mức ảnh hưởng ASYNC giữ chung, rồi điểm trọng số. Hai nút ưu tiên còn lại so điểm trọng số ngay. Nếu hòa, ưu tiên ít nhóm hơn rồi theo ID. |
| 5. Phân bổ characteristics và luồng | Với mỗi Quantum, lấy hợp các tập characteristics của component trong nhóm và ghi component đóng góp cho từng đặc tính. Đánh dấu mọi cạnh là nội bộ hoặc qua ranh giới theo Quantum ở hai đầu. |
| 6. Review và lặp lại | Đổi cách xếp hạng hoặc trọng số. Chọn một phương án hoặc yêu cầu chỉnh. Nếu thay relation, characteristic hoặc chính sách dữ liệu thì phân tích lại sơ đồ. |

Kéo vị trí chỉ đổi bố cục. Khi bấm **Phân tích sơ đồ**, app lưu bố cục trong phiên làm việc và gửi riêng mô hình để giải. Khi sửa thuộc tính, kết quả trước vẫn xem được trong sơ đồ đầu ra với cảnh báo chờ cập nhật. Bảng trade-off và Human Review xuất hiện lại sau khi phân tích mô hình mới hợp lệ.

| Chi phí | Cách tính |
|---|---|
| SYNC qua ranh giới | Cộng mức ảnh hưởng của mỗi cạnh SYNC bị cắt. Giao dịch cục bộ tách ra sẽ bị loại từ bước 2. |
| Tách dữ liệu | Với từng kho SPLITTABLE, lấy mức ảnh hưởng nhân với số Quantum dùng kho trừ một. Khi tách, người thiết kế cần chốt quyền ghi, độ trễ dữ liệu và cách đối soát. |
| ASYNC giữ chung | Cộng mức ảnh hưởng của cạnh ASYNC có hai đầu ở cùng nhóm. Trong chế độ chia theo SYNC, tiêu chí này được so sau SYNC. Trong chế độ xếp theo trọng số, đặt hệ số ASYNC bằng 0 để bỏ đóng góp vào điểm. |
| Một characteristic bị rải | Cộng số Quantum chứa characteristic đó trừ một, cho từng characteristic đã gắn. |
| Một Quantum trộn đặc tính | Cộng số characteristic khác nhau trong nhóm trừ một, cho các nhóm có characteristic. Nhóm chưa có characteristic được ghi riêng, nên chi phí 0 không mặc nhiên đạt ánh xạ 1:1. |

Điểm trọng số bằng tổng chi phí nhân với hệ số tương ứng. Hai chi phí về characteristic cùng dùng trọng số **Tập trung đặc tính**. Với **Chia theo SYNC**, điểm trọng số quyết định thứ hạng khi hai tiêu chí đầu bằng nhau. Cạnh SYNC thường có thể đi qua ranh giới nếu bị buộc tách. Chỉ giao dịch cục bộ và các ràng buộc cứng đã khai báo bắt buộc giữ hoặc tách nhóm.

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

Review do thao tác trên UI được lưu cục bộ dưới `runs/quantum-studio/reviews/`. Mỗi bản ghi chứa cách xếp hạng, trọng số, phương án đã xem, nguồn từng characteristic, vị trí các cạnh, thao tác review, ghi chú và thời điểm.
