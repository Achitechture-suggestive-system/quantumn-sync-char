# Studio CP-SAT cho 9–50 component

## Phạm vi và trạng thái đầu ra

Studio giữ enumerator Python cho tối đa tám component, tối đa Bell(8)=4.140 phân hoạch. ID Pxxx, điểm và biên Pareto của mẫu sáu component giữ nguyên. Từ 9 đến 50 component, `analyze` dispatch sang `studio_cpsat.py`. Adapter này mã hóa **năm trục Studio**, không gọi trực tiếp objective bất đồng MUST_LINK/CANNOT_LINK của pipeline nghiên cứu. Protocol P2 vẫn giới hạn tám responsibility IDs; không dùng mở rộng Studio để vượt gate nghiên cứu.

| Thông tin | ≤8 component | 9–50 component |
|---|---|---|
| Tìm kiếm | Liệt kê toàn bộ phân hoạch | CP-SAT có thời hạn và các seed hợp lệ |
| `enumerated` | Số phân hoạch đã xét | `null`; branches của CP không phải số phân hoạch |
| `feasible` / `pareto` trong bản so sánh | Tổng số đã liệt kê / Pareto toàn cục | `null`; dùng `feasible_found` / `pareto_in_found_pool` |
| Trạng thái tối ưu | Biên toàn cục trong mô hình khai báo | Chỉ chi phí chính của objective được yêu cầu khi solver báo OPTIMAL |
| Pareto/tie | Theo toàn bộ tập khả thi | Pareto, group/ID tie của lựa chọn UI chỉ xét tập đã tìm; `FOUND_POOL` |

`FEASIBLE` không phải chứng minh tối ưu. Nếu CP trả `UNKNOWN` hoặc chưa có thời gian chạy, Studio giữ seed đã kiểm hợp lệ, báo chi phí chưa chứng minh và giữ trạng thái CP riêng. Không chuyển timeout thành `INFEASIBLE`. Với các hard rules hiện hành, cùng-Quantum tạo equivalence classes; nếu một cặp khác-Quantum nằm trong cùng closure thì có chứng minh xung đột. Khi closure không xung đột, cho mỗi class một Quantum luôn tạo được ít nhất một phương án khả thi trong mô hình này.

Root `input_origin` ghi nguồn khai báo `PREPARED_FIXTURE`, `USER_SUPPLIED` hoặc `UNCLASSIFIED`. Metadata này không xác nhận ngữ nghĩa. Mẫu Ticket và các ca benchmark được đánh dấu fixture; input cũ thiếu trường giữ UNCLASSIFIED. Sửa một fixture vẫn có nguồn gốc từ fixture và có event/review riêng; không suy thành output LLM.

## Mã hóa bảo toàn hàm chi phí

Gộp trước các component bắt buộc cùng Quantum bởi LOCAL_TRANSACTION/KEEP_SHARED thành block. Ordinary SYNC vẫn là soft cost, không tự gộp cứng. Các biến nhãn `g_i` của block dùng restricted-growth sequence: `g_0=0`, `g_i ≤ max(g_0…g_(i−1))+1`. Nhãn này bỏ các hoán vị tên nhóm tương đương mà giữ các phân hoạch. KEEP_APART buộc hai nhãn khác nhau.

Đặt `s_ij=[g_i=g_j]`, `u_dq=[kho d có thành viên ở nhóm q]`, `t_lq=[target/characteristic l có owner ở q]` và `a_q=[nhóm q có ít nhất một label]`. Label lấy nguyên từ `component_profiles`, bao gồm canonical NFR và phạm vi đã review:

```text
C_SYNC   = sum_(e.mode=SYNC)  weight_e × (1 − s_e)
C_data   = sum_d weight_d × (sum_q u_dq − 1)
C_ASYNC  = sum_(e.mode=ASYNC) weight_e × s_e
C_spread = sum_l (sum_q t_lq − 1)
C_mix    = sum_q (sum_l t_lq − a_q)
J        = dot(Preferences.vector, [C_SYNC,C_data,C_ASYNC,C_spread,C_mix])
```

Một kho KEEP_SHARED không thể bị cắt vì hard closure; kho SPLITTABLE chịu cùng công thức `số nhóm−1` như enumerator. Target đã hợp nhất dùng đúng danh tính root hiện có, không đếm lại alias. Nhãn thủ công và ISO allocation có cách biểu diễn giống bộ nhỏ.

UNKNOWN không tự có điểm mode trong vector đã biết. Objective biên trên thêm các đóng góp đúng với `score_bounds`: với tập `{SYNC,ASYNC}`, `U_e=weight_e×(lambda_SYNC×(1−s_e)+lambda_ASYNC×s_e)` và `L_e=0`. Tập mode chỉ có một giá trị dùng cùng đóng góp cho L/U. Đây là bound rời rạc của Studio, không có xác suất hay hiệu chuẩn vận hành.

Mục tiêu chính theo thứ tự:

- WEIGHTED: `J`.
- SYNC_FIRST: `C_SYNC`, rồi `C_ASYNC`, rồi `J`.
- CHARACTERISTIC_FIRST: `C_spread`, rồi `C_mix`, rồi `J`.
- Conservative: `U`, rồi `L` theo trọng số.

CP còn ưu tiên số nhóm khi chi phí chính hòa. Tuple được mã hóa bằng radix từ upper bounds nguyên chính xác, từ chối nếu vượt miền an toàn `2^60`; không làm tròn hoặc đổi trọng số. Gap limits đặt bằng 0. Vector, hard rules và L/U của **mọi nghiệm CP trả về** được đối chiếu lại với hàm Python. `best_bound_numeric` là số bound của solver, không dùng float đó thay vector nguyên hoặc số đo chất lượng.

Với trọng số bằng 0, nhiều vector có thể cùng chi phí chính. Do không liệt kê Pareto toàn cục ở cỡ lớn, không tuyên bố chọn đúng cùng group/ID tie của enumerator trên toàn miền. Test kiểm hàm chi phí và giá trị chi phí chính, không giả định tập nhỏ tìm được chính là toàn bộ frontier.

## Tạo các phương án để so sánh

Các seed được biến đổi xác định từ input: mỗi hard block một nhóm; một số gộp hợp lệ; gộp theo tập characteristic; affinity SYNC hoặc kho; gộp thô còn tuân KEEP_APART. Các seed **không phải LLM proposal và không mặc nhiên tối ưu**. Mỗi seed được tính lại chi phí và kiểm hard rules.

CP tìm objective chính, objective theo trọng số mặc định và lần lượt năm endpoint chi phí trong một ngân sách. Seed và nghiệm khác nhau tạo pool, deduplicate theo phân hoạch. ID `CP-…` là hash nhóm canonical, không giả là số thứ tự trong Bell(n). Khi có ít nhất ba cách chia hợp lệ, các seed gộp cặp đã tạo được ít nhất ba phương án; một hoặc hai cách hợp lệ không bị nhân bản thành ba.

UI ghi “khả thi đã tìm”, “không trội trong tập đã tìm”, status, thời gian và giới hạn. A/B/C vẽ đúng phân hoạch được chọn; chọn lại từ pool đã cache không gọi lại solver cho cùng model/weights/policy/budget. Thay input/trọng số/chế độ/budget tính lại. Checkpoint lưu thời hạn tìm cùng ưu tiên. Mô hình lớn có vùng cuộn riêng, nút sắp xếp vị trí và nhóm owner dài có thể mở để truy vết.

## Sửa xung đột lớn

≤8 vẫn liệt kê chính xác MCS và số phân hoạch sau sửa. >8 dùng CP tối thiểu hóa tổng `change_cost`, rồi số rule sửa, giữ mọi rule protected. Tập sửa tìm được còn được kiểm tối thiểu theo bao hàm bằng closure xác định; từng rule được khôi phục thử để xác nhận cần thiết. Tối đa ba tập sửa trong thời hạn, loại mỗi tập và các supersets khi tìm tiếp.

Mỗi tập có status và cờ chứng minh chi phí riêng. OPTIMAL của lượt sau chỉ nói về miền còn lại sau khi loại tập đã tìm trước. Khi hết giờ vẫn có thể trả một tập sửa từ seed đã kiểm, với cost chưa chứng minh. Không đếm toàn bộ nghiệm sau sửa nên `feasible=None`. Nếu chính protected subset đã mâu thuẫn, không có cách sửa tuân policy. Xem trước và áp dụng vẫn cần review/rationale; không tự nới hard rules.

## Đối chứng và benchmark

`tests/test_studio_cpsat.py` kiểm toàn bộ nghiệm CP của các ca nhỏ so với enumerator, từng vector/L/U, ba kiểu xếp hạng, trọng số 0, mode sets đã review, min-cost repair có protected rules, timeout UNKNOWN, chặn overflow, UI pool counts và snapshot scope. Ca chín component được đối chiếu chi phí chính với Bell(9)=21.147 phân hoạch Python.

Hai họ input PREPARED_FIXTURE: `chain` có quality scope/affinity thuận nhau; `pressure` tạo cạnh/kho và scope xen kẽ, cùng một hard isolation. Allocation benchmark được chuẩn bị sẵn, không phải annotation chuyên gia hoặc do LLM trích xuất. Chạy:

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_studio_backend.py --seconds 6
```

Mỗi run lưu input/result riêng cho từng cỡ, phiên bản Python/OR-Tools/platform, arguments, hash mã và report ở `runs/quantum-studio/scale/`. Các run không stage vào Git. Đây là đo thời gian/solver status của workload tổng hợp trên máy hiện tại, không phải semantic accuracy, latency nghiệp vụ hay benchmark đại diện mọi hệ thống.

Lượt `scale-a1a437974cf24fc9975b825cc51a9367` ghi ngày 28/11/2026 giờ Việt Nam (27/11 UTC), Python 3.13.13, Windows 11 build 26200 và OR-Tools 9.15.6755; một worker, seed 611, thời hạn sáu giây cho mỗi input. Thời gian dưới đây gồm overhead, có thể nhỉnh hơn thời hạn solver. Một lượt mỗi workload chưa cho phân bố runtime.

| Họ fixture | Component | Giây thực tế | Trạng thái objective chính | Khả thi đã tìm | Điểm trọng số tốt nhất đã tìm |
|---|---:|---:|---|---:|---:|
| chain | 9 | 0,161 | OPTIMAL | 6 | 0 |
| chain | 12 | 0,227 | OPTIMAL | 6 | 0 |
| chain | 20 | 0,597 | OPTIMAL | 6 | 0 |
| chain | 50 | 5,956 | OPTIMAL | 6 | 0 |
| pressure | 9 | 0,378 | OPTIMAL | 10 | 22 |
| pressure | 12 | 1,814 | OPTIMAL | 10 | 24 |
| pressure | 20 | 6,002 | FEASIBLE | 12 | 37 |
| pressure | 50 | 6,014 | FEASIBLE | 8 | 84 |

Mọi ứng viên của tám ca đều thỏa hard constraints; mọi vector được tính lại bằng Python. Số ứng viên là cận dưới, gồm seed xác định và nghiệm CP. Hai ca pressure lớn chưa có chứng minh tối ưu. Input/allocation là PREPARED_FIXTURE, phân hoạch và điểm là DETERMINISTIC_TRANSFORMATION theo ARCHITECTURAL_POLICY; không có inference hoặc nhãn ngữ nghĩa độc lập trong benchmark này.

Browser 8501 tải checkpoint fixture `checkpoint-1f1e4873e00347f48c167ce2e9866b40`, actor `AGENT_TECHNICAL_SMOKE_TEST`, với 50 component, 17 kho và bốn target Reliability. UI tìm tám ứng viên, sáu không trội trong pool. A=`CP-c412388d7faced86` có ba Quantum, vector `(8,1,44,2,3)`, điểm 84. B=`CP-39431e668fae7536` có hai Quantum, vector `(1,1,72,1,3)`, điểm 89. C=`CP-bb0df79c3700a8ef` có bốn Quantum, vector `(49,1,0,0,0)`, điểm 153: scope theo target gọn hơn nhưng cắt nhiều SYNC hơn. Bấm C đổi đúng output; 67 nút đầu vào nằm trong bounds sau sắp xếp; owner dài mở được. Khổ 400 px có `scrollWidth=clientWidth=400`, không exception ứng dụng. Các lỗi mạng telemetry của Streamlit được phân biệt với exception của app. Ảnh và checkpoint giữ local. Mẫu sáu component được khôi phục sau smoke.

## Nguồn nghiên cứu và ranh giới áp dụng

- Laurent Perron, Frédéric Didier, Steven Gay. **The CP-SAT-LP Solver (Invited Talk)**, CP 2023, LIPIcs 280, 3:1–3:2, DOI `10.4230/LIPIcs.CP.2023.3`, 22/09/2023. Tài liệu hai trang mô tả solver CP/SAT/LP. Studio dùng OR-Tools; cách mã hóa năm trục, seed và radix là thiết kế của repo, không phải công thức đánh giá kiến trúc đã được bài này hiệu chuẩn. [Nhà xuất bản Dagstuhl](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CP.2023.3)
- Google OR-Tools **v9.15**, `cp_model.proto` và tài liệu model/channeling. Trạng thái FEASIBLE/UNKNOWN/OPTIMAL được đọc đúng phạm vi bài toán đang giải; một lần tối ưu không liệt kê mọi nghiệm. Studio không bật gap tolerance khác 0. [Định nghĩa status chính thức](https://github.com/google/or-tools/blob/v9.15/ortools/sat/cp_model.proto) · [Modeling](https://github.com/google/or-tools/blob/v9.15/ortools/sat/docs/model.md) · [Channeling](https://github.com/google/or-tools/blob/v9.15/ortools/sat/docs/channeling.md)
- Cortellessa, Di Pompeo, Stoico, Tucci, **Many-objective optimization of non-functional attributes based on refactoring of software models**, IST 157, 107159, 2023, DOI `10.1016/j.infsof.2023.107159`. Tham khảo phân biệt nhiều mục tiêu kiến trúc và mô hình đánh giá. Studio không chạy NSGA-II/LQN của bài và không chuyển kết quả cải thiện sang các ca tổng hợp này. [Bản tác giả](https://vstoico.gitlab.io/pdfs/cortellessa2023optimization.pdf)
- MCS và weighted repair tiếp tục theo phạm vi nguồn S05/S06 trong [source ledger](STUDIO_SOURCE_LEDGER.md). Chưa triển khai MARCO hoặc WPM2; closure, model partition và thuật toán bounded pool là phần triển khai riêng.
