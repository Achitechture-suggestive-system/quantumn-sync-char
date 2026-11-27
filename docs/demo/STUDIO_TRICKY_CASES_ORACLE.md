# Quantum Studio — 12 ca khó và oracle kiểm thử

**Kết quả ngày 21/11/2026.** `qwen3:4b` khớp toàn bộ oracle ở **0/12 ca** khi dùng chung một prompt. Tách đầu vào NFR và tương tác, giới hạn trường đầu ra bằng schema và viết lại hướng dẫn giúp lượt thử thứ hai đạt **4/12 ca**. Cả bốn là NFR. Lượt hai vẫn bỏ sót ràng buộc bắt buộc tách trong ca mâu thuẫn. Nếu chỉ áp dụng phần giao dịch mà model giữ lại, bộ giải trả 10 phương án khả thi, trong khi hai ràng buộc đầy đủ cho **0 nghiệm**.

## Chạy trên Quantum Studio

1. Mở [Quantum Studio](http://127.0.0.1:8501/), chọn **Ca khó và oracle** ở đầu trang và bấm **Chạy cả 12 ca**. Bảng tính lại kết quả từ mã bộ giải đang chạy và đối chiếu với các giá trị kỳ vọng của từng ca.
2. Chọn một ca và **Chỉ nạp nguồn** để xem requirement nháp với sơ đồ gốc, hoặc chọn **Áp dụng oracle** để mô phỏng các ánh xạ, mode và ràng buộc tương ứng. Bấm **Nạp ca vào sơ đồ** để xem kết quả cùng các lựa chọn A/B/C. Trọng số ban đầu của phiên thử là `(3, 6, 1, 2, 2)`.
3. Với **OC-10**, chọn thêm **Đầu ra Ollama đã lưu** để phát lại phần cấu trúc từ phản hồi cục bộ đã ghi nhận ở lượt tách. Ba chế độ cho lần lượt **37**, **0** và **10** nghiệm khả thi. Phiên này không gọi lại Ollama và không ghi biên bản Human Review.
4. Bấm **Quay lại sơ đồ của tôi** để lấy lại mô hình, bố cục và ưu tiên trước khi mở ca. Nếu đang chỉnh mô hình, bấm **Phân tích sơ đồ** trước khi đổi phiên.

Mốc **12/12** trong bảng chỉ đo kết quả bộ giải khi nhận đầu vào theo oracle. Bảng chấm `qwen3:4b` trong phần 3 dùng phản hồi thực tế của hai lượt gọi đã lưu.

## 1. Thiết kế đánh giá

Oracle là đáp án kỳ vọng của ca kiểm thử. Tài liệu này dùng 12 văn bản tổng hợp mới trên danh mục Ticket Support. Mỗi ca có oracle về trạng thái, ánh xạ ISO và component, quan hệ hoặc chính sách tách nếu có, đoạn làm căn cứ và tác động dự kiến lên bộ giải. Các oracle do người thực hiện thí nghiệm soạn và khóa trước lần gọi đầu tiên, dùng để kiểm thử kỹ thuật. Chưa có bộ nhãn chuyên gia độc lập. [Barr và cộng sự, The Oracle Problem in Software Testing](https://discovery.ucl.ac.uk/id/eprint/1471263/)

| Bước | Kiểm tra |
|---|---|
| Đầu vào | Danh mục `LOGIN` = Customer Login, `PROFILE` = Customer Profile, `CREATE` = Ticket Creation, `ROUTE` = Ticket Router, `COMPLETE` = Ticket Completion, `REPORT` = Operations Reporting. Cùng fixture gốc và cùng bộ 12 ca cho cả hai lượt. |
| LLM | Gửi `id`, `kind`, `text`, `context` và danh mục component cho Ollama. Mỗi lượt gồm ba lời gọi. Không gửi đáp án hay kết quả phân hoạch mong đợi. Đây là phép thử trích xuất ngoại tuyến. Studio hiện dùng quy tắc từ khóa và dữ liệu LLM nhập sẵn để đề xuất ánh xạ trong UI. |
| Chấm đầu ra | So trạng thái, mã trùng, tập ánh xạ `(nhãn, tập component)`, tập cạnh `(nguồn, đích, mode, giao dịch cục bộ)`, và chính sách tách. Đoạn trích phải xuất hiện nguyên văn và chứa cụm bằng chứng ghi sẵn cho đúng ánh xạ hoặc cạnh. Ca đạt toàn bộ khi mọi trường đều khớp, kể cả những trường phải rỗng. |
| Kiểm tra Studio | Nạp từng ca nháp và đối chiếu toàn bộ nghiệm với fixture. Sau đó dùng ánh xạ và chính sách từ oracle trong phiên giả định có kiểm soát để kiểm tra bộ giải. Chỉ những ca LLM khớp toàn bộ mới được dùng thêm làm phép đối chiếu end-to-end ngoại tuyến. Không ghi quyết định review cho người dùng. |

Nhãn characteristic dùng ISO/IEC 25010:2023. Kiểm tra kiến trúc tập trung vào thay đổi phương án, điểm nhạy và xung đột chính sách. Tất cả mục tiêu tải, thời gian và tỷ lệ thành công vẫn là `NOT_MEASURED`. [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) · [SEI Architecture Tradeoff Analysis Method](https://sei.cmu.edu/library/atam-method-for-architecture-evaluation/)

**Cách đọc đáp án.** `PROPOSE` cho phép đưa ra đề xuất để review. `CLARIFY` giữ lại câu hỏi về phạm vi hoặc cơ chế. `DUPLICATE` dẫn đến requirement đã có. `OUT_OF_SCOPE` dùng khi component được nêu rõ nhưng chưa tồn tại. `CONFLICT` giữ đồng thời các chính sách xung đột để bộ giải kiểm tra. Với NFR, các trường cạnh và chính sách tách rỗng. Với đầu vào tương tác, trường ánh xạ ISO rỗng. Trạng thái chưa rõ hoặc ngoài danh mục có ánh xạ ISO rỗng. `duplicate_of` chỉ có giá trị ở OC-05.

## 2. Bộ đầu vào, oracle và quan sát

### OC-01 · Mục tiêu độ trễ xuyên component

- **Đầu vào** “Trong chiến dịch cao điểm, p95 từ lúc Customer Login xác thực đến lúc Ticket Creation trả mã tiếp nhận phải không quá 900 ms ở 300 lượt/phút; phạm vi đo gồm cả hai bước.”
- **Oracle** `PROPOSE`. *Performance efficiency* → `LOGIN, CREATE`. Đoạn căn cứ chứa `không quá 900 ms`. Mục tiêu đo qua hai bước chưa xác định một lời gọi SYNC giữa chúng.
- **Quan sát** Lượt chung gán đúng ISO nhưng tự thêm `LOGIN → CREATE SYNC`. Lượt tách đạt. Khi áp dụng ánh xạ đúng trong mô phỏng, phương án xếp đầu theo trọng số đổi từ P031 sang P011.

### OC-02 · NFR có ngưỡng bị phủ định

- **Đầu vào** “Operations Reporting không phải đáp ứng mốc 150 ms. Sau khi tiến trình xử lý bị dừng, Operations Reporting phải tự khôi phục trong vòng 90 giây.”
- **Oracle** `PROPOSE`. *Reliability* → `REPORT`. Đoạn căn cứ chứa `khôi phục trong vòng 90 giây`.
- **Quan sát** Lượt chung gán đúng ISO và tự thêm cạnh tự trỏ `REPORT → REPORT SYNC`. Lượt tách đạt. Quy tắc từ khóa trong UI mặc định chọn *Performance efficiency* từ `150 ms`. Chưa bấm xác nhận thì ánh xạ vẫn rỗng.

### OC-03 · Hai characteristic trong cùng requirement

- **Đầu vào** “Customer Profile phải mã hóa trường định danh trước khi truyền. Khi worker báo cáo bị dừng, Operations Reporting phải khôi phục trong 3 phút.”
- **Oracle** `PROPOSE`. *Security* → `PROFILE` với `mã hóa trường định danh`. *Reliability* → `REPORT` với `khôi phục trong 3 phút`. Hai phạm vi tách riêng.
- **Quan sát** Lượt chung tìm đủ hai ánh xạ nhưng thêm cạnh `PROFILE → REPORT SYNC`. Lượt tách bỏ cạnh thừa và bỏ sót *Reliability*. Khi xác nhận tuần tự hai ánh xạ trong AppTest, P031 hiển thị *Security* ở Q1 và *Reliability* ở Q3.

### OC-04 · Biệt danh component chưa ánh xạ

- **Đầu vào** “Sau sự cố điện, thành phần cầu nối phải khôi phục trong 3 phút. Cụm từ ‘thành phần cầu nối’ chưa được ánh xạ vào danh mục component.”
- **Oracle** `CLARIFY`. Hỏi người dùng “thành phần cầu nối” là ID nào. Giữ danh sách ánh xạ rỗng.
- **Quan sát** Lượt chung trả `PROPOSE` với scope rỗng và tự thêm cặp tách `COMPLETE/ROUTE`. Lượt tách trả `OUT_OF_SCOPE` nhưng vẫn tự gán `COMPLETE`. Trong AppTest, scope rỗng làm nút xác nhận ISO bị vô hiệu hóa.

### OC-05 · Requirement trùng ý dưới mã khác

- **Đầu vào** “Khi thông tin cá nhân đi qua mạng, Customer Profile phải bảo vệ danh tính bằng mã hóa trên đường truyền.” Ngữ cảnh `PREV-01`: “Customer Profile phải mã hóa thông tin cá nhân khi gửi qua mạng.”
- **Oracle** `DUPLICATE`, `duplicate_of = PREV-01`. Dẫn về yêu cầu đã có và giữ ánh xạ mới rỗng.
- **Quan sát** Cả hai lượt đều đề xuất *Security* mới. Lượt chung còn thêm cạnh `PROFILE → LOGIN SYNC`. Nếu xác nhận cả hai bản dưới hai ID, bộ giải đếm hai đặc tính theo ID và điểm P031 tăng từ 7 lên 9.

### OC-06 · Component ngoài danh mục, mục tiêu có số

- **Đầu vào** “Khi lệnh hoàn tiền được gửi, Payment Gateway phải trả mã kết quả trong 200 ms. Payment Gateway là component mới, chưa có trong danh mục kiến trúc hiện tại.”
- **Oracle** `OUT_OF_SCOPE`. Chờ khai báo Payment Gateway, ánh xạ rỗng.
- **Quan sát** Lượt chung trả `PROPOSE` và gán `PROFILE`. Lượt tách nhận đúng `OUT_OF_SCOPE` nhưng vẫn gán `PROFILE`. Schema Studio chặn ID `PAYMENT_GATEWAY` chưa khai báo. Một ID có thật nhưng gán sai chủ thể có thể vượt qua kiểm tra danh mục.

### OC-07 · Component cung cấp bối cảnh và component chịu mục tiêu

- **Đầu vào** “Ticket Creation là nguồn sự kiện, chỉ cung cấp ngữ cảnh. Operations Reporting phải đọc được cả hai phiên bản hợp đồng v1 và v2 với bộ kiểm thử hợp đồng đạt đủ 40/40 mẫu.”
- **Oracle** `PROPOSE`. *Compatibility* → `REPORT`, căn cứ chứa `đọc được cả hai phiên bản hợp đồng v1 và v2`. `CREATE` không thuộc phạm vi mục tiêu.
- **Quan sát** Lượt chung gán đúng ISO và thêm cạnh `REPORT → CREATE SYNC`. Lượt tách đạt. Quy tắc từ khóa Studio thấy tên của cả hai component nhưng không gợi ý nhãn *Compatibility* cho cách viết này.

### OC-08 · ASYNC và SYNC cùng xuất hiện

- **Đầu vào** “Ticket Creation trả mã tiếp nhận sau khi lưu và không đợi Ticket Router; Ticket Router xử lý sau. Ticket Router phải chờ Ticket Completion trả phiên bản trạng thái trước khi phản hồi. Hai bước này không yêu cầu giao dịch cục bộ.”
- **Oracle** `PROPOSE`. `CREATE → ROUTE ASYNC` với `không đợi Ticket Router`. `ROUTE → COMPLETE SYNC` với `phải chờ Ticket Completion`. Cả hai `local_transaction=false`.
- **Quan sát** Lượt chung trả hai cạnh SYNC. Lượt tách sửa được cạnh ASYNC và bỏ sót cạnh SYNC. Nhập đúng hai cạnh, giữ mức ảnh hưởng 1 và 2 của fixture, bảo toàn toàn bộ điểm và phân hoạch.

### OC-09 · Thứ tự nghiệp vụ thiếu bằng chứng chờ

- **Đầu vào** “Bước định tuyến Ticket Router xảy ra trước bước Ticket Completion. Tài liệu chỉ mô tả thứ tự nghiệp vụ, chưa nói bên nào phải đợi phản hồi.”
- **Oracle** `CLARIFY`. `ROUTE → COMPLETE UNKNOWN`, `local_transaction=false`. Căn cứ chứa `chưa nói bên nào phải đợi phản hồi`.
- **Quan sát** Lượt chung suy ra SYNC và thêm *Safety*. Lượt tách trả đúng cạnh `UNKNOWN` nhưng vẫn ghi `PROPOSE`. Khi người kiểm thử đặt cạnh thành `UNKNOWN`, chi phí SYNC của phương án P006 giảm từ 2 xuống 0. Cảnh báo thiếu dữ liệu vẫn cần được giữ khi trình bày điểm.

### OC-10 · Giao dịch cục bộ xung đột với bắt buộc tách

- **Đầu vào** “Ticket Router gọi Ticket Completion và bắt buộc chúng ghi trạng thái trong cùng một giao dịch cục bộ nguyên tử. Chính sách cách ly cũng bắt buộc Ticket Router và Ticket Completion nằm ở hai Quantum khác nhau.”
- **Oracle** `CONFLICT`. `ROUTE → COMPLETE SYNC`, `local_transaction=true`, căn cứ chứa `cùng một giao dịch cục bộ nguyên tử`. Thêm chính sách tách `ROUTE/COMPLETE`. Cùng nhóm và khác nhóm đồng thời dẫn đến `INFEASIBLE`.
- **Quan sát** Lượt chung tìm được cả giao dịch và cặp tách nhưng thêm cạnh ASYNC đối nghịch, hai nhãn *Safety* và ghi `PROPOSE`. Lượt tách giữ giao dịch, làm mất cặp bắt buộc tách và vẫn ghi `PROPOSE`. Đưa đủ hai chính sách vào bộ giải cho 0 nghiệm. Chỉ đưa vào giao dịch thì còn 10 nghiệm.

### OC-11 · Một cặp, hai chế độ theo loại ticket

- **Đầu vào** “Ticket Creation phải chờ Ticket Router khi xử lý ticket ưu tiên. Với ticket thông thường, Ticket Creation trả mã tiếp nhận trước và không chờ Ticket Router. Hai chế độ đều đang áp dụng.”
- **Oracle** `CLARIFY`. Lược đồ Studio hiện có một mode cho mỗi cặp. Giữ cả hai điều kiện trong ghi chú và biểu diễn cạnh `CREATE → ROUTE UNKNOWN` cho tới khi có cách mô hình hóa hai chế độ. Căn cứ chứa `Với ticket thông thường`, `local_transaction=false`.
- **Quan sát** Lượt chung nhận ra cả hai mode nhưng tạo hai cạnh trùng cặp và ánh xạ *Safety* thừa. Lượt tách chỉ giữ SYNC nên làm mất quy tắc cho ticket thông thường. Studio chặn hai cạnh cùng cặp. Nếu nhập `UNKNOWN` trong thử nghiệm, chi phí ASYNC giữ chung của P031 giảm từ 1 xuống 0.

### OC-12 · Thành phần lỗi và thành phần chịu trách nhiệm khác nhau

- **Đầu vào** “Trong 15 phút kể từ lúc Operations Reporting bị ngắt, Ticket Completion phải duy trì tỷ lệ hoàn tất thành công ít nhất 99,5%. Việc báo cáo có thể phục hồi sau.”
- **Oracle** `PROPOSE`. *Reliability* → `COMPLETE`. Căn cứ chứa `tỷ lệ hoàn tất thành công ít nhất 99,5%`. Gián đoạn báo cáo là điều kiện của kịch bản.
- **Quan sát** Lượt chung gán nhầm cho `REPORT`. Lượt tách đạt. Mô phỏng ánh xạ đúng đưa *Reliability* đến Q2 của P031, điểm của P031 đổi từ 5 lên 7.

## 3. So sánh hai lượt gọi Ollama

| Phép kiểm trên 12 ca | Prompt chung | Prompt/schema tách theo loại |
|---|---:|---:|
| Trạng thái đúng | 6/12 | 7/12 |
| Tập ánh xạ ISO–component khớp, kể cả tập rỗng | 5/12 | 8/12 |
| Tập quan hệ và thuộc tính giao dịch khớp, kể cả tập rỗng | 2/12 | 10/12 |
| Tập chính sách bắt buộc tách khớp, kể cả tập rỗng | 11/12 | 11/12 |
| Đoạn trích nguyên văn trong các đoạn model xuất ra | 27/27 | 12/12 |
| Đoạn trích gắn đúng mục và chứa cụm bằng chứng oracle | 7/27 | 8/12 |
| Khớp toàn bộ | **0/12** | **4/12** |

Bốn ca đạt ở lượt tách là **OC-01, OC-02, OC-07 và OC-12**. Khi dùng đúng ánh xạ và đoạn trích từ bốn phản hồi này trong mô phỏng, kết quả bộ giải khớp toàn bộ với phép chạy bằng oracle tương ứng. **0/4 ca tương tác** đạt toàn bộ. Trong sáu ca cần giữ lại, phát hiện trùng hoặc báo xung đột, lượt tách chỉ đúng trạng thái ở OC-06; ca này vẫn lọt một ánh xạ sai ngay trong phản hồi. Lượt hai thay đồng thời prompt, cách chia lô và schema, sau khi quan sát lượt đầu. Các tỷ lệ là kết quả trên chính bộ ca đã thiết kế, chưa có mẫu dành riêng để ước lượng độ chính xác tổng quát.

## 4. Bộ giải, Human Review và tác động đo được trong mô hình

Fixture gốc có **203** phân hoạch được xét và **37** khả thi. Xếp theo trọng số `(3, 6, 1, 2, 2)` có P031 đứng đầu với 5 điểm. Vector theo thứ tự `(SYNC bị cắt, tách kho, ASYNC giữ chung, đặc tính bị rải, đặc tính bị trộn)`. **12/12 ca ở trạng thái nháp** bảo toàn tập nghiệm, năm trục chi phí và thứ hạng. Thử thay đầu vào đã xác nhận theo oracle cho kết quả sau.

| Ca | Phép đối chiếu | Kết quả |
|---|---|---|
| OC-01 | Hai phương án chấm cùng đầu vào mới | P031 `(0,0,1,2,3)` = **11** điểm. P011 `(0,1,0,0,1)` = **8** điểm. P011 giữ `LOGIN/CREATE` cùng nhóm và chấp nhận tách Ticket DB. |
| OC-02, OC-07, OC-12 | Thêm từng characteristic vào đúng component | P031 vẫn xếp đầu, 5 → 7. Ca OC-02 áp nhầm *Performance efficiency* với quote phủ định cũng ra 7 điểm, nên điểm không phân biệt đúng sai ngữ nghĩa. |
| OC-03 | Xác nhận riêng từng scope | P031 `(0,0,1,1,3)` = 9. AppTest gửi đúng Q1/`PROFILE` và Q3/`REPORT` đến sơ đồ A, truy vết hiển thị cùng phương án. |
| OC-04, OC-05, OC-06 | Giữ ở nháp | 37 nghiệm giữ nguyên. Ba ca này cần xác nhận chủ thể, hợp nhất bản trùng hoặc cập nhật danh mục trước khi có ánh xạ. |
| OC-08 | Thay bằng hai mode có căn cứ, giữ mức ảnh hưởng | Kết quả trùng toàn bộ fixture. |
| OC-09 | Cập nhật cạnh chưa đủ căn cứ thành `UNKNOWN` | 37 nghiệm. P006 có SYNC 2 → 0 và điểm 18 → 12. Mức giảm đến từ trục chi phí đã bỏ qua cạnh đang thiếu bằng chứng. |
| OC-10 | Giữ đồng thời hai chính sách cứng | Xét 203 cách chia, **0 khả thi**. Bỏ riêng chính sách tách trong lượt đối chứng thu được **10** nghiệm, tất cả giữ `ROUTE/COMPLETE` cùng nhóm. Nạp trực tiếp các trường model giữ lại vào bộ giải ngoại tuyến cũng trả 10 nghiệm. |
| OC-11 | Giữ hai điều kiện trong nguồn, nhập một cạnh `UNKNOWN` | 37 nghiệm. P031 có ASYNC giữ chung 1 → 0, điểm 5 → 4. Mô hình không đủ để kết luận mọi loại ticket đều đi theo một mode. |

**Kiểm tra biên có chủ đích**

| Dữ liệu đưa vào qua validator | Kết quả thực tế |
|---|---|
| Quote `900 ms` trong OC-02, vốn không xuất hiện trong ca | Bị từ chối. |
| Quote `150 ms` trong OC-02, xuất hiện trong câu phủ định | Được chấp nhận nếu ép ánh xạ thủ công. Đây là lỗi ngữ nghĩa mà kiểm tra chuỗi con không bắt được. |
| `PAYMENT_GATEWAY` chưa đăng ký và hai cạnh `CREATE → ROUTE` | Hai phép thử đều bị từ chối. |
| Hai bản diễn đạt tương đương OC-05 và PREV-01, mỗi bản có ID riêng | Đều qua kiểm tra cấu trúc. Khi gắn cả hai, điểm P031 tăng 7 → 9 dù mục tiêu nghiệp vụ không đổi. |

AppTest kiểm tra thêm ba thao tác thực tế trên `app.py`: OC-02 hiện đề xuất mặc định sai nhưng chưa có allocation, OC-04 vô hiệu hóa nút xác nhận với scope rỗng, OC-03 cho phép sửa scope và xác nhận riêng từng nhãn trước khi dựng truy vết. Các thao tác xác nhận được mô phỏng trong phiên kiểm thử.

## 5. Cách demo và cải thiện quy trình

1. **Demo rủi ro ngữ nghĩa với OC-02.** Thêm NFR trong Requirements, chọn `REPORT`, bấm **Phân tích sơ đồ**. Studio tự cấp mã `REQ-…`; chọn NFR theo nội dung OC-02. Đọc câu phủ định, đổi nhãn sang *Reliability*, rồi xác nhận. Chọn P031 ở vùng A/B/C để xem nhãn *Reliability* cùng mã nguồn vừa tạo ở Q3.
2. **Demo phân quyền đặc tính với OC-03.** Nhập nguyên văn NFR. Trong ISO, chọn *Security* cho `PROFILE` và *Reliability* cho `REPORT`, xác nhận từng nhãn. Chọn phương án P031 để kiểm tra cả Q1 và Q3. Đổi sang phương án khác để kiểm tra truy vết dùng đúng Quantum của phương án đang vẽ.
3. **Demo hard constraint với OC-10.** Bấm cạnh `ROUTE → COMPLETE`, giữ SYNC, khai báo giao dịch cục bộ và căn cứ từ câu đầu. Dùng **Bắt buộc tách** cho cùng hai component, ghi căn cứ từ câu thứ hai và chạy lại. Sơ đồ phải báo `INFEASIBLE`. Ca này kiểm tra Studio giữ mâu thuẫn thay vì tự nới chính sách.

Khi đưa LLM vào luồng tự động, thêm kiểm tra theo loại đầu vào, kiểm tra `status` nhất quán với nội dung, và lọc cạnh tự trỏ hoặc trùng. Giữ các mục chưa rõ scope, hai mode theo điều kiện và kết quả phát hiện trùng ở trạng thái cần review. Với một yêu cầu ghép nhiều mục tiêu, kiểm riêng từng nhãn, chủ thể và đoạn làm căn cứ. Ca OC-10 cần kiểm tra độ đầy đủ của chính sách trước khi đưa vào optimizer: một cạnh SYNC đúng vẫn có thể tạo tập nghiệm sai nếu thiếu `keep_apart`. Các thay đổi này là đề xuất từ kết quả thử; tài liệu không thay đổi hành vi ứng dụng.

## 6. Dấu vết lần chạy

- Môi trường: Ollama `0.40.16`, model cục bộ `qwen3:4b`, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`. Sáu phản hồi từ `/api/chat` kết thúc với `done_reason=stop`, `temperature=0`, `think=false`, seed `611–613` mỗi lượt, `num_ctx=6144`, `num_predict=2500`. Oracle khóa lúc `08:34:13` ngày 21/11/2026 theo giờ Việt Nam. SHA-256 của `oracle.lock.json` là `2f923aca020db61a50cc4c004f541adba9d7454abbf72582c0c41b5413d8e8e5`.
- Lượt chung trả `730 / 699 / 865` token. SHA-256 nội dung ba phản hồi lần lượt là `60147a942627d7990b9a3434d45974cc3eb7b8501db211a134600812ac558521`, `00557cce96ebf6002dea25a9369f174726b28556e33c7f2533c37b66ce83f3a1`, `ef3c1e4c91e74183eda6f15f620f83548dd43a8ba7bbe92f19e1330224b9eb9a`.
- Lượt tách trả `544 / 530 / 488` token. SHA-256 nội dung ba phản hồi lần lượt là `ff9f67f7ad3cd2f3b2bcab3c65c373fc59a72fd88a8b311526e300e7804dd712`, `35f1bb1f08a8bff97c6f9842bf34aaa328bd14094b1d43262e4e871a26b84cc7`, `0a61ba779b5cb85c5054098ef2571e5448bdbd342c623449f64a7d2568616e65`.
- Trên máy chạy, mở `runs/studio-llm-oracle-2026-11-21/` và thư mục con `routed/` để xem prompt, JSON phản hồi, hash request, kết quả chấm từng trường và vector chi phí. Kiểm tra đã đối chiếu hash với dữ liệu thô và xác nhận prompt chỉ chứa dữ liệu đầu vào. Các bản chạy thô được giữ cục bộ theo quy ước repo.
- Kết quả toàn bộ regression suite: **154 bài đạt**. Các ca chuyên biệt, bộ chấm và AppTest của tài liệu là kiểm tra riêng chạy trên mã Studio hiện tại.
