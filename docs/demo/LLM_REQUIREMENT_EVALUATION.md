# Đánh giá requirement Ollama trong Quantum Studio

## Cơ sở đánh giá

- ISO/IEC 25010:2023 cung cấp hệ phân loại chất lượng sản phẩm. Studio dùng tên characteristic để truy vết; điểm thiết kế vẫn theo năm trục của bộ giải hiện có. [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html)
- SEI mô tả quality scenario bằng nguồn kích thích, kích thích, môi trường, đối tượng, phản hồi và thước đo. Các brief cố định hướng model viết kịch bản cụ thể. Khi rà kết quả, một ngưỡng có số vẫn cần đơn vị, điều kiện tải, tập mẫu và ý nghĩa vận hành phù hợp. [Bachmann và cộng sự, CMU/SEI-2003-TR-004](https://insights.sei.cmu.edu/documents/704/2003_005_001_14213.pdf)
- ATAM dùng kịch bản để tìm rủi ro, điểm nhạy và chỗ đánh đổi. Thí nghiệm này dùng cùng ý tưởng khi đổi từng ánh xạ hoặc chính sách tách báo cáo và chạy lại. [Kazman, Klein và Clements, CMU/SEI-2000-TR-004](https://sei.cmu.edu/library/atam-method-for-architecture-evaluation/)
- Nghiên cứu thực nghiệm về dùng nhiều LLM để gợi mở yêu cầu đánh giá đề xuất với người phân tích và so độ phủ với dữ liệu đối chiếu. Báo cáo Studio chỉ đếm kiểm tra cấu trúc và thay đổi ở bộ giải. [Evaluating multi-LLM pipelines for early-stage software requirements elicitation](https://link.springer.com/article/10.1007/s10664-026-10981-6)

## Nguồn gốc và cách chọn

Ngày 2026-11-20, máy chạy Ollama `0.40.16` với model `qwen3:4b` có digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`. Ba lời gọi `/api/chat` của lượt cuối kết thúc với `done_reason=stop`, trả 21 mục. Prompt dùng schema JSON, seed `151/152/153`, temperature `0.2` và `think=false`. [Giao thức JSON có schema của Ollama](https://docs.ollama.com/capabilities/structured-outputs)

| Gói | Token đầu ra | SHA-256 nội dung phản hồi | Giữ lại |
|---|---:|---|---:|
| Tải cao `CAPACITY` | 549 | `2f83859a56339cc402987ae7053ee5e1780d1b9e86b51a910e9b1d9317545ca3` | 6 |
| Gián đoạn `RECOVERY` | 573 | `42df0c0c7ef9714e9344107880e90206e5fbcb4ec080054f33f458e0b9669b0f` | 5 |
| Tích hợp `CHANGE` | 440 | `697073474c50a70d785ad58d1d6651f878c94deaf2c67ff08039ff442ea21f69` | 4 |

| Thành phần | Provenance |
|---|---|
| Sáu component, sáu requirement ban đầu, tương tác, kho và ràng buộc | Fixture Ticket Support từ sơ đồ tham chiếu và giả định demo |
| Brief, chủ đề và vị trí FR/NFR trong schema | Thiết kế thí nghiệm |
| Câu requirement, mã component, nhãn và đoạn trích mới | Phản hồi Ollama giữ nguyên trường dữ liệu |
| Mã `LLM-<gói>-<vị trí>`, kiểm tra đoạn trích, tính phân hoạch và điểm | Chuyển đổi xác định |
| Chọn 15 câu để nạp và ghi nhận vấn đề | Rà soát kỹ thuật cho dữ liệu demo |
| Xác nhận gán ISO trong Studio | Quyết định của người vận hành ở phiên làm việc |

Lượt đầu gợi ý lại yêu cầu gốc và **0/15** đoạn trích khớp chữ. Lượt hai đạt **18/18** đoạn trích khớp nhưng sai tỷ lệ đã yêu cầu, chỉ tạo 3 FR và vẫn có câu lặp hoặc thiếu căn cứ. Lượt ba có **5/15** đoạn trích khớp và model chủ yếu chép lại tên chủ đề. Một lần bật thinking chạm giới hạn 5.000 token trước khi có đầu ra. Lượt cuối dùng các chủ đề tiếng Anh theo vị trí, để model tự viết câu tiếng Việt. Kết quả là 6 FR, 15 NFR, **9/15** NFR có đoạn trích nguyên văn. Những lần thay prompt đồng thời thay cách định dạng đầu vào, nên các số này chỉ mô tả các lần chạy quan sát được.

### Các đầu vào đưa lên giao diện

| Gói | Điểm kiểm tra | Các NFR đưa vào mô phỏng |
|---|---|---|
| Tải cao | `01` gửi lặp và `02` chuyển nhóm. `05` đề xuất giữ tốc độ tiếp nhận khi chạy báo cáo, nhưng quote thêm/bớt chữ so với câu. Loại `03` vì chỉ nêu mở rộng ngang và thiếu ngưỡng vận hành. | `04` thời gian gửi đến có nhóm ≤45 giây, CREATE/ROUTE. `06` khôi phục khi worker hoàn tất lỗi, COMPLETE. `07` tỷ lệ lỗi khi tạo/phân tuyến không vượt 1%, CREATE/ROUTE. |
| Gián đoạn | `01` phát lại và `02` xuất lịch sử. `04` nêu không lặp/bỏ sót trạng thái nhưng quote lệch. Loại `03` vì phạm vi có COMPLETE dù câu nói về phân công, và `05` vì cơ chế “đồng ý từ hệ thống” thiếu tiêu chí phân quyền. | `06` ticket tiếp tục hoàn tất khi báo cáo ngoại tuyến, ROUTE/COMPLETE. `07` từ tồn đọng định tuyến đến dashboard dưới 15 giây, ROUTE/REPORT. |
| Tích hợp | `01` đổi lịch và `02` lọc/xuất dữ liệu. `03` cần kiểm tra tương thích hợp đồng vì quote lệch. Loại `05` vì nhãn Functional suitability chưa giải thích nhu cầu kiểm thử/sửa đổi, `06` vì câu thiếu mốc 15 giây dù phần quote có, `07` vì câu thiếu điều kiện đo và nhãn cần phân biệt khả năng thích nghi với bảo trì. | `04` đăng nhập và gửi ticket chỉ bằng bàn phím, LOGIN/CREATE. |

Ba NFR giữ lại với đoạn trích lệch chỉ xuất hiện trong danh sách nháp để người dùng sửa hoặc xác nhận thủ công. Đoạn trích nguyên văn, nhãn trong danh mục và mã component hợp lệ là kiểm tra cấu trúc. Ví dụ, `CAPACITY-06` vẫn cần thời gian khôi phục, `CAPACITY-07` cần định nghĩa lỗi và cửa sổ đo, `CHANGE-04` cần tập tác vụ và cách kiểm tra bàn phím. Các phép chạy bên dưới dùng giả định tạm thời về nhãn và scope. Tất cả mục tiêu chất lượng là `NOT_MEASURED`.

## Phân hoạch và trade-off

Giữ nguyên sáu component, tương tác, kho và hard constraints. Chạy ba gói riêng và chạy gộp. Thứ tự vector là **SYNC bị cắt, tách kho, ASYNC giữ chung, đặc tính rải, đặc tính trộn**. Xếp trọng số mặc định dùng `(3,6,1,2,2)`. Tất cả lần chạy giữ **203** phân hoạch xét và **37** nghiệm khả thi thỏa ràng buộc cứng. Nạp bản nháp làm **0/37** vector thay đổi. Thử áp dụng các ánh xạ có quote khớp làm **37/37** vector thay đổi ở mỗi gói. Mỗi lần thử có **2** phương án Pareto.

| Đầu vào | Ánh xạ giả định | Xếp đầu theo SYNC | Xếp đầu theo characteristics | Xếp đầu theo trọng số mặc định | Vector xếp đầu theo trọng số |
|---|---:|---|---|---|---|
| Fixture | 0 | P011 · 6 | P011 · 6 | P031 · 5 | `(0,0,1,1,1)` |
| Tải cao | 3 | P011 · 20 | P031 · 11 | P031 · 11 | `(0,0,1,1,4)` |
| Gián đoạn | 2 | P010 · 12 | P010 · 12 | P030 · 11 | `(0,0,1,1,4)` |
| Tích hợp | 1 | P011 · 8 | P011 · 8 | P011 · 8 | `(0,1,0,0,1)` |
| Gộp ba gói | 6 | P010 · 28 | P030 · 23 | P030 · 23 | `(0,0,1,2,9)` |

- **Tải cao**. Với cùng dữ liệu mới và trọng số, P031 có 11 điểm còn P011 có 20. P031 giữ `CREATE/ROUTE` trong một Quantum và giữ Ticket DB liền khối. Đổi lại, seam ASYNC giữ chung và mất ranh giới nhận/phân tuyến.
- **Tích hợp**. Khi áp dụng mục bàn phím, P011 có 8 điểm còn P031 có 11. P011 giữ `LOGIN/CREATE` trong cùng Quantum, giữ `ROUTE/COMPLETE` nội bộ và phải đồng bộ Ticket DB qua ranh giới ASYNC. Giữ chung thành phần lập trình là một quyết định kiến trúc; kiểm thử bàn phím vẫn phải chạy trên luồng người dùng.
- **Gián đoạn và gộp**. Với trọng số mặc định, P030 gộp REPORT với CREATE/ROUTE/COMPLETE, giữ Ticket DB chung và giữ ASYNC nội bộ. Với SYNC-first, P010 đặt CREATE với LOGIN/PROFILE, giữ ROUTE/COMPLETE/REPORT cùng nhóm và chấp nhận tách kho. Khi chấm cùng dữ liệu gộp, P030 đạt 23 và P031 đạt 25. Điểm 5 của P031 trên fixture dùng ít đặc tính hơn nên thuộc bài toán trước khi bổ sung yêu cầu.

### Kiểm tra nguyên nhân và rủi ro báo cáo

| Thay đổi một yếu tố với trọng số mặc định | Khả thi | Xếp đầu | Điểm |
|---|---:|---|---:|
| Chỉ giả định áp dụng `LLM-RECOVERY-07` | 37 | P030 | 9 |
| Gộp đủ gói, trừ ánh xạ `LLM-RECOVERY-07` | 37 | P031 | 19 |
| Gộp đủ gói và giả định chính sách bắt buộc tách REPORT/ROUTE | 27 | P031 | 25 |

`LLM-RECOVERY-07` làm tăng chi phí rải khi ROUTE và REPORT ở hai Quantum. Đồng vị trí giảm điểm ở trục này và xung đột với mục tiêu cô lập tải báo cáo của fixture. Kiểm tra thêm chính sách bắt buộc tách cho thấy có thể giữ REPORT riêng nếu đây là yêu cầu bắt buộc của người dùng. Chính sách thử này chỉ có trong script đánh giá. Có thể đạt mục tiêu độ trễ bằng phương án dữ liệu đọc riêng hoặc luồng cập nhật bất đồng bộ nếu kiểm thử tải và độ tươi dữ liệu xác nhận được giả thuyết đó.

## Chạy lại

```powershell
.\.venv\Scripts\python.exe -m scripts.generate_studio_requirements
.\.venv\Scripts\python.exe -m scripts.evaluate_studio_requirements
.\.venv\Scripts\python.exe -m scripts.evaluate_studio_requirements --raw-run-dir runs/studio-llm-ticket-evaluation-v5
```

Lệnh đầu tạo lượt gọi mới. Lệnh thứ hai chạy lại các phân hoạch từ gói đã chọn trong repo. Lệnh cuối kiểm tra thêm SHA-256 của payload đã lưu và nội dung phản hồi, cùng từng trường LLM ở các mục đã chọn. Tệp request/response gốc của lượt cuối nằm trong `runs/studio-llm-ticket-evaluation-v5/` trên máy chạy. Các mẫu xem trong Studio lấy từ fixture dữ liệu đã chọn, nên xem và so sánh lại được khi Ollama đang tắt. Báo cáo là đánh giá đầu vào giả lập trong Studio, với nhãn độc lập và đo tải thực tế còn bỏ ngỏ.
