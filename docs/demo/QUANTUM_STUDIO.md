# Quantum Studio

## Demo trong 60 giây

1. Mở app và kéo component hoặc kho trong **Sơ đồ đầu vào**. Bấm component để sửa tập characteristics. Dùng **Nối** rồi chọn hai đầu để tạo cạnh. Bấm nhãn cạnh để đổi Sync/Async, mức ảnh hưởng và căn cứ. Dùng **Bắt buộc tách** để thêm cặp có ràng buộc.
2. Bấm **Phân tích sơ đồ**. Chọn phương án trong **Sơ đồ đầu ra**. Bấm component hoặc kho ở một bên để làm nổi phần tương ứng và Quantum ở bên còn lại. Cạnh nâu chấm nối các phần của kho cần đồng bộ.
3. Bấm **Ưu tiên tập trung đặc tính**. Màn hình giữ hai phương án đang so sánh và cập nhật thứ hạng. Bấm **Ưu tiên giữ dữ liệu** để quay lại bộ trọng số ban đầu.
4. Trong **Human Review**, bấm **Chọn A**, **Chọn B** hoặc nhập điều cần sửa rồi chọn **Yêu cầu chỉnh**. Quyết định lưu cùng đầu vào, trọng số, phương án và điểm tại thời điểm review. Có thể tải bản JSON và sửa mô hình để phân tích lại.

## Pipeline

| Bước | Dữ liệu và quyết định |
|---|---|
| 1. Nhập mô hình | Khai báo 1–8 component và các tập characteristics, cạnh có hướng SYNC/ASYNC/UNKNOWN, kho dùng chung và cặp bắt buộc tách. Mỗi chính sách giữ hoặc tách kho dùng chung có căn cứ. |
| 2. Loại vi phạm | Liệt kê mọi cách chia, mỗi component vào đúng một nhóm. Loại phương án tách giao dịch cục bộ, tách kho KEEP_SHARED hoặc gom cặp bắt buộc tách. Nếu hết phương án, báo INFEASIBLE. |
| 3. Tính trade-off | Tính tiền phạt theo bảng dưới. Cạnh UNKNOWN được giữ trong sơ đồ, với cảnh báo và trạng thái cần xác nhận. |
| 4. Xếp hạng | Tính biên Pareto theo năm chi phí. Phương án trên biên không có bộ chi phí khác tốt hơn hoặc bằng ở mọi tiêu chí và tốt hơn ở ít nhất một tiêu chí. Xếp điểm tăng dần theo trọng số, sau đó ưu tiên ít nhóm hơn và dùng ID để quyết định thứ tự ổn định. |
| 5. Review và lặp lại | Đổi trọng số để xếp hạng lại ngay. Chọn một phương án hoặc yêu cầu chỉnh. Nếu thay relation, characteristic hoặc chính sách dữ liệu thì lưu đầu vào và chạy lại bước 2–4. |

Kéo vị trí chỉ đổi bố cục. Khi bấm **Phân tích sơ đồ**, app lưu bố cục trong phiên làm việc và gửi riêng mô hình để giải. Khi sửa thuộc tính, kết quả trước vẫn xem được trong sơ đồ đầu ra với cảnh báo chờ cập nhật. Bảng trade-off và Human Review xuất hiện lại sau khi phân tích mô hình mới hợp lệ.

| Chi phí | Cách tính |
|---|---|
| SYNC qua ranh giới | Cộng mức ảnh hưởng của mỗi cạnh SYNC bị cắt. Giao dịch cục bộ tách ra sẽ bị loại từ bước 2. |
| Tách dữ liệu | Với từng kho SPLITTABLE, lấy mức ảnh hưởng nhân với số Quantum dùng kho trừ một. Khi tách, người thiết kế cần chốt quyền ghi, độ trễ dữ liệu và cách đối soát. |
| ASYNC giữ chung | Cộng mức ảnh hưởng của cạnh ASYNC có hai đầu ở cùng nhóm. Chi phí mô hình biểu diễn cơ hội tách chưa dùng. Đặt trọng số bằng 0 nếu không ưu tiên cơ hội này. |
| Một characteristic bị rải | Cộng số Quantum chứa characteristic đó trừ một, cho từng characteristic đã gắn. |
| Một Quantum trộn đặc tính | Cộng số characteristic khác nhau trong nhóm trừ một, cho các nhóm có characteristic. Nhóm chưa có characteristic được ghi riêng, nên chi phí 0 không mặc nhiên đạt ánh xạ 1:1. |

Điểm xếp hạng bằng tổng chi phí nhân với trọng số tương ứng. Hai chi phí về characteristic cùng dùng trọng số **Tập trung đặc tính**. Các con số là đơn vị ưu tiên thiết kế. Việc xác nhận latency, consistency hay khả năng triển khai cần dữ liệu vận hành.

Phần **Điểm phát sinh từ đâu** truy từng khoản điểm về cạnh, kho hoặc characteristic gốc và nêu Quantum liên quan. Các khoản này dùng cùng phép tính với bộ giải và có trong JSON review. Dropdown trên sơ đồ nhận ứng viên do bộ giải tìm từ dữ liệu đang nhập. Hai hình tham chiếu chỉ cung cấp cách minh họa ví dụ Ticket Support.

## Mẫu Ticket Support

Sáu component và ba kho dựa trên các hình. Kiểu tương tác, đặc tính, mức ảnh hưởng và yêu cầu tách LOGIN khỏi ROUTE là giả định demo có thể sửa. Yêu cầu tách này loại phương án gom toàn bộ Customer và Ticket vào cùng nhóm. Cạnh CREATE → ROUTE nét đứt được diễn giải là ASYNC để minh họa. Quy trình đồng bộ ở hình 3 liên quan dữ liệu giữa hai kho.

Trong cấu hình mẫu, bộ giải xét **203** cách chia, giữ **37** cách khả thi và tìm **2** phương án trên biên Pareto.

| Phương án | Quantum | Đánh đổi | Điểm giữ dữ liệu | Điểm tập trung đặc tính |
|---|---|---|---:|---:|
| P031 · Hình 2 | Login + Profile / Creation + Router + Completion / Reporting | Giữ nguyên Ticket DB. Luồng ASYNC còn chung nhóm, một đặc tính trải qua hai nhóm và một nhóm trộn hai đặc tính. | **5** | 9 |
| P011 · Hình 3 | Login + Profile + Creation / Router + Completion / Reporting | Cắt cạnh ASYNC, đạt ánh xạ đặc tính và Quantum 1:1. Tách Ticket DB và cần thiết kế đồng bộ dữ liệu. | 6 | **6** |

Hai sơ đồ được dựng từ nghiệm do bộ giải tìm. Thay đầu vào sẽ thay nghiệm. App dùng thông tin Sync/Async đã khai báo và chừa UNKNOWN cho các quan hệ còn thiếu căn cứ.

Review do thao tác trên UI được lưu cục bộ dưới `runs/quantum-studio/reviews/`. Mỗi bản ghi chứa hai phương án đã xem, trọng số, phương án xếp đầu mặc định và hiện tại, lựa chọn hoặc yêu cầu chỉnh, ghi chú và thời điểm. Kết quả review đánh dấu phương án ưu tiên để xem lại.
