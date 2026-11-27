# P7 — Mô hình và giới hạn phân hoạch

## Phạm vi

Optimizer tìm các phân hoạch của responsibility IDs theo tập hard/soft constraints đã được chuyển vào. Đây là tối ưu hóa cổ điển, xác định trên input; từ “Quantum” trong EQCR là tên candidate group, không phải máy tính lượng tử hoặc kết luận kiến trúc đúng.

Với mỗi cặp khác nhau `(i,j)`, CP-SAT tạo biến nhị phân `x_ij`, bằng 1 khi hai responsibility nằm cùng nhóm. Mỗi bộ ba `(i,j,k)` có ba bất đẳng thức tam giác `x_ij + x_jk - x_ik <= 1` và các hoán vị tương ứng. Chúng buộc quan hệ “cùng nhóm” có tính bắc cầu. Hard `MUST_LINK` đặt `x_ij=1`; hard `CANNOT_LINK` đặt `x_ij=0`. Hard constraint chỉ kiểm soát khả thi; code không xác nhận justification kiến trúc của chúng.

Hàm mục tiêu là:

```text
J(P) = Σ weight(c), cho mỗi enabled SOFT constraint c bị vi phạm trong partition P
```

Soft `MUST_LINK` bị vi phạm khi hai đầu ở hai nhóm; soft `CANNOT_LINK` bị vi phạm khi hai đầu ở cùng nhóm. Disabled constraints bị bỏ qua. Không có weight mặc định nào được coi là đã được chuyên gia xác nhận. Code lấy `Decimal(str(weight))` từ giá trị float đã parse rồi scale thành hệ số nguyên, không làm tròn thêm: tối đa 9 chữ số thập phân và tổng hệ số không vượt `2^60`; trường hợp vượt giới hạn bị từ chối. Do schema đang lưu weight dưới dạng float, bước parse JSON có thể đã chuẩn hóa số ban đầu; “exact” ở đây chỉ áp dụng cho decimal string của giá trị model đã parse. CP-SAT dùng hệ số nguyên theo API chính thức của [OR-Tools](https://developers.google.com/optimization/cp/cp_solver/).

## Backend và output

- `R1–R8`: Python exhaustive enumerator tiếp tục là backend mặc định, liệt kê toàn bộ Bell partitions, giữ mọi feasible và co-optimal candidates. CP-SAT test chéo với exhaustive và independent product-label oracle trên các trường hợp nhỏ.
- `R9–R50`: CP-SAT classical backend. Hiện code giải trước bài toán tối ưu, sau đó khóa objective ở optimum đã chứng minh và liệt kê nghiệm tối ưu. Output chỉ chứa `OPTIMAL_CANDIDATES_ONLY`; `feasible_candidate_count=null` nghĩa là tổng tập feasible không được đếm. Giới hạn mặc định báo cáo 200 optimum candidates. Khi enumeration chạm giới hạn hoặc timeout, `optimal_candidate_set_complete=false`; không suy luận rằng những optimum chưa báo cáo không tồn tại.
- Trên 50 responsibility IDs, CP-SAT adapter từ chối input. Giới hạn 50 là guardrail code, không phải tuyên bố benchmark hoặc hỗ trợ vận hành ở kích thước đó.
- Time limit hiện đặt riêng cho solve chứng minh optimum và solve enumerate co-optima, nên tổng thời gian solver có thể gần gấp đôi cấu hình; overhead Python không tính vào limit. Nếu không chứng minh được optimum, status là `REVIEW_REQUIRED` và không trả optimum.
- Kết quả infeasible trên CP-SAT có thể đưa ra shortest must-link path cộng cannot-link tương ứng, với các constraint IDs; scope `INCLUSION_MINIMAL_MUST_LINK_PATH_PLUS_CANNOT_LINK`.
- Exhaustive fallback (R1–R8) nếu không có direct same-pair conflict sẽ thử bỏ từng hard rule trong thứ tự ID xác định, dùng lại toàn bộ Bell partitions để kiểm tra. Output ghi `DELETION_MINIMAL_HARD_CONSTRAINT_CORE`: bỏ bất kỳ rule được liệt kê nào cũng làm xuất hiện ít nhất một partition khả thi. Đây là core tối tiểu theo phép bỏ từng phần tử, không đảm bảo core có số rule nhỏ nhất trên toàn bộ tập.
- Candidate được chọn là display tie-break (`FIRST_OPTIMAL`, `MAXIMUM_GROUPS`, hoặc preferred nếu candidate có trong tập đã báo cáo), không phải recommendation kiến trúc. Với enumeration bị cắt, preferred candidate có thể không nằm trong các candidate trả về.

## Tính tái lập và sensitivity

CP-SAT ghi package version, seed, single-worker setting, time limit, objective scale, và giới hạn candidate. Seed/worker làm solver run có cấu hình tái lập; chúng không bảo đảm cùng kết quả giữa mọi phiên bản thư viện hoặc nền tảng. Sensitivity API chỉ chạy các assignment weight do caller cung cấp cho enabled soft constraints; output đánh dấu `SCENARIO_COMPARISON_ONLY`. Khoảng weight trong test là dữ liệu synthetic để kiểm tra thuật toán, không phải range thực nghiệm hay chính sách miền Tutor.

## Phạm vi kiểm chứng hiện có

Test mới so sánh CP-SAT với independent brute-force product-label oracle trên 12 trường hợp seeded với 4 responsibility IDs; so sánh thêm trực tiếp với exhaustive backend, decimal objective, hard transitive conflicts, deterministic settings, cap/truncation, sensitivity và pipeline traceability. Regression mới kiểm core transitive cho exhaustive fallback và xác minh từng rule trong core là cần thiết; một rule không liên quan bị loại. Một stress fixture 9 IDs có `Bell(9)=21,147` partitions nhưng chỉ yêu cầu trả tối đa 20 optimum candidates; đây là synthetic algorithm test, không phải case study. Không có benchmark runtime, scale stress tới 50 IDs hoặc đánh giá chất lượng kiến trúc. Tutor case có sáu role và tiếp tục dùng exhaustive backend; P2 vẫn cần quyết định người review thật.

## Giới hạn

Pairwise Boolean variables tăng theo `O(n²)` và các ràng buộc transitivity theo `O(n³)`. Candidate cap bảo vệ output, nhưng không bảo đảm solve nhanh. CP-SAT tối ưu đúng hàm mục tiêu khai báo khi status chứng minh optimum; nó không xác nhận semantics của constraints, weights, boundaries, deployability, interactions, quality hay tính hữu ích của kiến trúc. Tất cả candidate vẫn cần human review và các quality profiles vẫn `NOT_MEASURED` khi không có đo lường.
