# Quantum Studio · EQCR + QAME

Quantum Studio nhận component, characteristics, requirements, quan hệ Sync/Async và kho dữ liệu. Studio đề xuất ánh xạ NFR vào ISO/IEC 25010:2023 và các component có căn cứ trong văn bản. Sau khi xác nhận, người dùng so sánh và chọn ba phương án Quantum nếu có đủ nghiệm khả thi.

## Chạy nhanh (Windows / PowerShell)

Yêu cầu Python 3.11 trở lên:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.port 8501
```

Mở URL cục bộ mà Streamlit in ra. Màn đầu hiển thị mẫu Ticket Support. Kéo hoặc bấm component để chỉnh sơ đồ, rồi bấm **Phân tích sơ đồ**. Chọn phương án bên đầu ra và bấm một component để xem ánh xạ vào Quantum. Đổi ưu tiên và lưu quyết định trong **Human Review**. Xem [cách tính và kịch bản demo](docs/demo/QUANTUM_STUDIO.md).

## Bài toán Studio giải

Tình trạng các gap và bằng chứng hiện tại nằm trong [theo dõi hoàn thiện](docs/research/STUDIO_COMPLETION_STATUS.md). [Bảng nguồn nghiên cứu](docs/research/STUDIO_SOURCE_LEDGER.md) ghi metadata, DOI, phần áp dụng và giới hạn của từng nguồn.

Một phương án là một cách chia 1–8 component vào các Quantum. Đầu vào gồm sơ đồ component, kho và chính sách dữ liệu, cạnh `SYNC`/`ASYNC`/`UNKNOWN`, requirement và ánh xạ đặc tính đã được xác nhận. Với NFR, chuỗi truy vết là **đoạn nguồn → characteristic ISO → component → Quantum của phương án**. Ollama cung cấp đề xuất để review. Việc nạp văn bản nháp chỉ bổ sung nguồn; chi phí đặc tính phản ánh các ánh xạ đã đưa vào mô hình. [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) · [Bộ ca đánh giá và nguồn gốc dữ liệu](docs/demo/STUDIO_TRICKY_CASES_ORACLE.md)

| Ràng buộc cứng | Điều kiện để một cách chia hợp lệ |
|---|---|
| `local_transaction` | Hai component của giao dịch cục bộ nằm cùng Quantum. Một cạnh `SYNC` thông thường vẫn có thể qua ranh giới. |
| `KEEP_SHARED` | Tất cả component dùng kho đã khai báo giữ chung nằm cùng Quantum. |
| `keep_apart` | Hai component bắt buộc tách nằm ở hai Quantum khác nhau. |

Bộ giải Python duyệt các phân hoạch, loại phương án vi phạm ràng buộc cứng, rồi giữ biên Pareto theo năm trục **SYNC qua ranh giới**, **tách kho**, **ASYNC giữ chung**, **đặc tính rải nhiều Quantum** và **trộn nhiều đặc tính trong Quantum**. Ở chế độ trọng số mặc định, điểm là `3×SYNC + 6×tách kho + 1×ASYNC + 2×rải + 2×trộn`. Điểm thấp hơn được ưu tiên trong cùng bộ tiêu chí. Một cạnh `UNKNOWN` được giữ trong sơ đồ và chưa có điểm SYNC hoặc ASYNC. Điểm là thước đo đánh đổi thiết kế, còn độ trễ, độ tin cậy và các mục tiêu chất lượng cần phép đo riêng. [Bộ giải Studio](eqcr/quantum_tradeoff.py) · [SEI Architecture Tradeoff Analysis Method](https://sei.cmu.edu/library/atam-method-for-architecture-evaluation/)

## Review và so sánh khi mode còn bất định

Sau khi sửa requirement đã dùng để review tương tác hoặc quy tắc tách, Studio yêu cầu **Căn cứ nguồn của tương tác và quy tắc** trước khi chạy lại bộ giải. Chọn nguồn/quote hiện hành, kiểm nghĩa và ghi lý do xác nhận. Các hard constraints vẫn giữ cho tới khi có quyết định đổi policy; nguồn cũ không tiếp tục được dùng âm thầm.

Với cạnh `UNKNOWN`, thẻ phương án và bảng so sánh hiển thị khoảng chi phí theo hai giả thuyết SYNC/ASYNC. Mở **Review tương tác theo điều kiện** để khai báo mode cho từng điều kiện bằng quote nguồn, người review và rationale. Bật **Ưu tiên chi phí biên trên khi còn bất định** để chọn phương án có biên trên thấp nhất trên toàn bộ tập khả thi. Các ràng buộc cứng vẫn giữ nguyên. Khoảng này chưa có xác suất và giả định mode giữa các cạnh độc lập. [Công thức, nguồn nghiên cứu và giới hạn](docs/research/STUDIO_COMPLETION_STATUS.md#mốc-b2--bất-định-của-mode-tương-tác).

## Review mục tiêu trùng

Nếu hai NFR diễn đạt cùng một mục tiêu, mở **Review yêu cầu cùng mục tiêu**, chọn nguồn đối chiếu và bản gốc đã gán ISO, ghi lý do rồi lưu. Bộ giải dùng ánh xạ của bản gốc một lần, còn cả hai mã yêu cầu vẫn có trong truy vết. Chỉ hợp nhất sau khi đối chiếu ngưỡng, điều kiện và phạm vi component. Tách mục tiêu hoặc sửa nguồn sẽ cần review ánh xạ lại. Xem [tiến độ và bằng chứng hoàn thiện](docs/research/STUDIO_COMPLETION_STATUS.md).

## Quality scenario và dự đoán theo phương án

Mở **Quality scenario và dự đoán**, chọn NFR gốc, điền sáu phần scenario, scope chịu trách nhiệm và đường đi. Chọn adapter phản hồi tuần tự hoặc khôi phục toàn Quantum, nhập target theo quote nguồn và các bound thời gian đã gồm thời gian chờ. Ô trống giữ UNKNOWN. Phân biệt khai báo reviewer với dữ liệu chuẩn bị cho demo/kiểm thử.

Bấm **Xác nhận scenario và tính lại** để lưu revision. Nếu bật đưa scope ISO vào phân nhóm, optimizer dùng ánh xạ mới. **Quality Profiles theo phương án** hiển thị scope→Quantum, target, dự đoán có điều kiện và từng đóng góp thời gian. Chọn A/B/C để đối chiếu với sơ đồ. Thứ hạng năm tiêu chí thiết kế và dự đoán chất lượng được ghi riêng; chưa có phép đo thì vẫn `NOT_MEASURED`. [Công thức, ví dụ và giới hạn](docs/research/STUDIO_QUALITY_SCENARIOS.md).

## Xử lý `INFEASIBLE`

1. **Tìm chuỗi gây xung đột.** Giao dịch cục bộ và các kho `KEEP_SHARED` tạo đồ thị bắt buộc cùng nhóm. Tìm theo chiều rộng để lấy một đường ngắn nhất nối hai đầu của từng `keep_apart` bị mâu thuẫn. Ví dụ, nếu A phải cùng nhóm với B và B phải cùng nhóm với C, thì chính sách A phải tách khỏi C gây vô nghiệm. UI hiện tên component, loại ràng buộc và căn cứ gốc của từng bước.
2. **Tìm tập thay đổi tối thiểu.** Với mỗi phân hoạch `P`, lấy `V(P)` là tập quy tắc cứng mà `P` vi phạm. Nếu cho phép mô phỏng bỏ đúng các quy tắc trong `V(P)`, phân hoạch đó trở nên khả thi. Mọi cách sửa làm xuất hiện một phân hoạch đều phải chứa ít nhất một `V(P)`. Vì vậy, giữ các tập `V(P)` tối thiểu theo bao hàm sẽ tìm được toàn bộ tập sửa tối thiểu trong mô hình Studio. Một tập là tối thiểu theo bao hàm khi rút bất kỳ quy tắc nào ra khỏi tập sửa đó thì bài toán lại vô nghiệm. Cách này phù hợp với giới hạn tám component của Studio, tương ứng tối đa 4.140 phân hoạch.
3. **Tính tác động trong bản sao.** Bỏ yêu cầu tách chỉ gỡ `keep_apart`. Bỏ yêu cầu giao dịch cục bộ chỉ tắt `local_transaction`, giữ nguyên cạnh SYNC và mức ảnh hưởng. Cho phép tách kho đổi `KEEP_SHARED` thành `SPLITTABLE` và giữ trọng số chi phí tách. Bảng hiển thị số nghiệm từng cách sửa. Chọn phương án ở **Xem chi tiết mô phỏng** để chạy lại bộ giải trên bản sao và xem Quantum, thứ hạng và điểm theo ưu tiên hiện tại. Mô hình gốc vẫn hiển thị `INFEASIBLE`. Người review quyết định việc sửa thật trên sơ đồ.

Thuật toán hiển thị một đường chứng minh cho mỗi cặp bắt buộc tách bị xung đột. Danh sách cách sửa dùng toàn bộ các phân hoạch, nên vẫn tìm được các lựa chọn phải thay đổi nhiều quy tắc khi có nhiều xung đột độc lập. Các lựa chọn sắp theo số quy tắc thay đổi. Chi phí nghiệp vụ để sửa chính sách cần quyết định riêng. [Triển khai và mô phỏng](eqcr/studio_conflicts.py) · [Kiểm thử xung đột trực tiếp, bắc cầu và nhiều xung đột](tests/test_studio_conflicts.py)

### Chạy lại OC-10

1. Mở [Studio](http://127.0.0.1:8501/#studio-oracles), vào **Ca khó và oracle**, chọn **OC-10**, chọn **Áp dụng oracle** rồi bấm **Nạp ca vào sơ đồ**.
2. Chọn **Xem xung đột và các cách gỡ**. Hai đoạn nguồn yêu cầu Ticket Router và Ticket Completion cùng một giao dịch cục bộ, đồng thời phải nằm ở hai Quantum khác nhau.
3. Mở lần lượt M1 và M2 để đối chiếu kết quả trên cùng mẫu và trọng số mặc định.

| Bộ chính sách | Số nghiệm trong 203 phân hoạch | Xếp đầu |
|---|---:|---|
| Giữ cả giao dịch cục bộ và bắt buộc tách | **0** | `INFEASIBLE` |
| M1 · Bỏ yêu cầu tách, giữ giao dịch cục bộ | **10** | **P031 · 5 điểm**. Router và Completion cùng Quantum. |
| M2 · Giữ yêu cầu tách, bỏ giao dịch cục bộ và giữ SYNC | **27** | **P008 · 16 điểm**. Router và Completion ở hai Quantum khác nhau. |

Chế độ **Đầu ra Ollama đã lưu** của OC-10 cho 10 nghiệm vì phản hồi thực tế đã bỏ sót chính sách tách. Trong chế độ **Áp dụng oracle**, hai ràng buộc được giữ đầy đủ, còn kết quả 10 và 27 chỉ xuất hiện trong bảng mô phỏng. Đây là ca thử tổng hợp của Studio. [Nguyên văn OC-10, oracle và kết quả gọi Ollama](docs/demo/STUDIO_TRICKY_CASES_ORACLE.md)

### Cơ sở nghiên cứu

Trong **Review chính sách ràng buộc**, reviewer có thể bảo vệ từng quy tắc và đặt chi phí sửa. Bộ chẩn đoán chỉ đề nghị tập sửa không đụng quy tắc bảo vệ, xếp theo tổng chi phí sửa. Sau khi xem trước, dùng **Áp dụng cách sửa đã review** và ghi rationale để tạo revision mới. Nếu mọi cách sửa đều bị bảo vệ, trạng thái `INFEASIBLE` được giữ. Muốn bỏ bảo vệ cần quyết định policy riêng. [Chi tiết thuật toán và giới hạn](docs/research/STUDIO_COMPLETION_STATUS.md#mốc-d1--chính-sách-và-quyết-định-sửa-ràng-buộc).

| Nguồn | Cách liên hệ với triển khai |
|---|---|
| [Wagstaff và Cardie (2000), *Clustering with Instance-level Constraints*](https://www.cs.cornell.edu/home/cardie/papers/icml-2000.pdf) | Cơ sở biểu diễn quan hệ `must-link` và `cannot-link`. Studio dùng đồ thị để lấy đường dẫn bằng chứng và dùng bộ giải phân hoạch hiện có. |
| [Junker (2004), *QuickXplain*](https://cdn.aaai.org/AAAI/2004/AAAI04-027.pdf) | Tham chiếu cho giải thích xung đột tối thiểu bằng lời gọi kiểm tra khả thi. Studio hiện sinh đường chứng minh qua đồ thị của ba loại ràng buộc trên. QuickXplain là hướng mở rộng cho các loại constraint tổng quát hơn. |
| [Liffiton, Previti, Malik và Marques-Silva, *Fast, Flexible MUS Enumeration*](https://markliffiton.com/publications/constraints_liffiton_marco.pdf) | Cơ sở cho *minimal unsatisfiable subset* và *minimal correction set*. Studio tìm các tập sửa bằng cách liệt kê tập vi phạm trên các phân hoạch. MARCO là thuật toán tham khảo nếu chuyển sang phân tích tổng quát trên một bộ giải khác. |
| [Ansótegui, Bonet và Levy (2010), *A New Algorithm for Weighted Partial MaxSAT*](https://cdn.aaai.org/ojs/7545/7545-13-11075-1-2-20201228.pdf) | Hướng xếp hạng các cách sửa nếu có quy tắc được phép nới và chi phí sửa do người review cung cấp. Điểm kiến trúc hiện tại được tính trong từng kịch bản giả định. |
| [Gray và Lamport (2006), *Consensus on Transaction Commit*](https://www.microsoft.com/en-us/research/publication/consensus-on-transaction-commit/) | Nếu yêu cầu nghiệp vụ cho phép thay giao dịch cục bộ bằng commit qua ranh giới, bài báo mô tả cơ chế phối hợp các bên cùng commit hoặc abort. Đây là thay đổi thiết kế cần review riêng. |
| [Garcia-Molina và Salem (1987), *Sagas*](https://www.cs.princeton.edu/techreports/1987/070.pdf) | Tham khảo nếu nghiệp vụ chấp nhận trạng thái trung gian và có thao tác bù khi một bước thất bại. Áp dụng vào OC-10 cần xác định lại yêu cầu nguyên tử. |
| [Bailis và cộng sự, *Coordination Avoidance in Database Systems*](https://www.vldb.org/pvldb/vol8/p185-bailis.pdf) | Dùng bất biến nghiệp vụ và các phép cập nhật để phân tích khi nào có thể giảm điều phối. Studio để việc kiểm tra các bất biến vận hành ở bước đánh giá kiến trúc sau mô phỏng. |

## Chạy giao diện nghiên cứu lưu trữ

PetClinic, Tutor Support và các walkthrough nghiên cứu dùng entrypoint lưu trữ `research_app.py`.

```powershell
.\.venv\Scripts\python.exe -m streamlit run research_app.py --server.port 8502
```

- **Xác định/offline:** nạp fixture PRECOMPUTED tại eqcr/fixture.py và chạy pipeline cục bộ. Cùng đầu vào và revisions sẽ tạo cùng kết quả.
- **JSON có cấu trúc:** tải template, cung cấp raw_requirements, responsibilities, evidence và constraints; ứng dụng kiểm tra schema, tham chiếu và source spans. Các ý nghĩa vẫn cần review.
- **Tutor Exploratory Demo (unblinded):** chỉ mở sau khi người vận hành xác nhận unblinded; proposals chưa vào optimizer trước Human Review, run lưu dưới `runs/demo-unblinded/` và luôn `EXCLUDED_FROM_BLIND_RESEARCH`. Mode này không thay thế P2 blind experiment.
- **Tutor Blind Research:** vẫn lock-first, cần source-only annotation độc lập hợp lệ; thiếu lock thì model proposals bị khóa.
- **Ollama tùy chọn:** tạo đề xuất JSON cục bộ, kiểm tra schema rồi ánh xạ ID được trích dẫn vào spans chính xác của đầu vào. Mọi đề xuất vẫn REVIEW_REQUIRED; span khớp không đồng nghĩa ngữ nghĩa được duyệt.

Luồng offline không cần Ollama. Để dùng model-assisted mode, chạy Ollama và cài model cục bộ như qwen3:4b; sau đó chọn **Check local Ollama models** trong UI.

## Kết quả kiểm tra đã chạy

Rà soát ngày 26/11/2026 ghi nhận 158 bài kiểm tra đạt và mười khoảng trống còn lại. Ba phép đối chứng cho thấy paraphrase làm điểm P031 tăng 7→9, đổi target 900→9.000 ms vẫn cho cùng kết quả và chuyển cạnh sang UNKNOWN làm giảm điểm. Ưu tiên tiếp theo là nối đầu vào mới với Ollama và review theo phiên bản, hợp nhất mục tiêu trùng sau review, rồi đánh giá bất định và quality scenario. Báo cáo có dấu vết mã nguồn, nguồn bài báo và điều kiện hoàn thành cho từng gap. [Gap analysis và hướng hoàn thiện](docs/research/STUDIO_GAP_ANALYSIS_2026-11-26.md)

Mốc triển khai tiếp theo đã nối Ollama vào các requirement đang nhập. Mở **Phân tích yêu cầu hiện tại bằng Ollama**, chọn nguồn và tác vụ, rồi bấm **Phân tích bằng Ollama**. Mỗi đề xuất có đoạn nguồn, lỗi cấu trúc và các lựa chọn approve/correct/reject/defer. Quyết định áp dụng được lưu cùng input trước–sau. **Lịch sử và tải lại phiên Studio** khôi phục mô hình và ưu tiên từ checkpoint. Khi sửa nguồn, cần xác nhận lại allocation. [Tiến độ, hướng dẫn và bằng chứng từng gap](docs/research/STUDIO_COMPLETION_STATUS.md)

**Hợp đồng tương tác và quyền ghi dữ liệu** bổ sung review ACK, retry, timeout, idempotency, writer và invariant cho boundary. Hợp đồng được duyệt cập nhật mode rồi phân nhóm lại; nháp giữ nguyên optimizer. Từng nguồn, claim và kho liên quan đều gắn revision. Trong **Boundary: hợp đồng, ownership và chạy thử**, có thể chạy giao thức mẫu bằng hai tiến trình HTTP/SQLite riêng và đọc kết quả mất ACK, timeout, restart, gửi trùng. Mã và dữ liệu giao thức này là `PREPARED_FIXTURE`; observation được thu từ tiến trình thực tế, chưa phải kiểm chứng nghiệp vụ Ticket/Tutor hay deployability. [Cách bấm, tái lập, nguồn bài báo và giới hạn](docs/research/STUDIO_BOUNDARY_EVIDENCE.md)

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q app.py research_app.py eqcr tests
```

P0 baseline được kiểm tra ngày 14/11/2026 với 30 test đạt, cùng compileall, Streamlit AppTest và HTTP smoke. Nhánh P1 có 44 test đạt. Trạng thái của bản Studio hiện tại nằm trong [changelog](docs/development/CHANGELOG.md) và [nhật ký GitHub](docs/development/GITHUB_PUBLISH_LOG.md). Các phép kiểm xác minh hành vi code và dữ liệu thử. P2 blind case vẫn chờ independent annotation lock. [P2 validation](docs/p2/P2_VALIDATION_REPORT.md) · [P2 human worksheet](docs/p2/HUMAN_REVIEW_WORKSHEET.md) · [Demo acceptance matrix](docs/demo/DEMO_ACCEPTANCE_MATRIX.md)

## Tài liệu

[Đọc từ đây](docs/00_START_HERE.md) · [Vấn đề và phạm vi nghiên cứu](docs/01_RESEARCH_PROBLEM_AND_SCOPE.md) · [Pipeline 10 bước](docs/02_PIPELINE_01_TO_10.md) · [Kiến trúc và luồng dữ liệu](docs/03_ARCHITECTURE_AND_DATA_FLOW.md) · [Schema và truy vết](docs/04_DATA_SCHEMAS_AND_TRACEABILITY.md) · [Kiểm tra và giới hạn](docs/05_VALIDATION_AND_RESEARCH_LIMITS.md) · [Human-in-the-loop](docs/06_HUMAN_IN_THE_LOOP.md) · [Giải thích PetClinic](docs/07_CURRENT_SYSTEM_EXPLAINED_VI.md) · [P2 Tutor Support](docs/p2/NEW_CASE_STUDY.md) · [P1 semantic evaluation](docs/verification/P1_SEMANTIC_EVALUATION.md) · [P2 validation](docs/p2/P2_VALIDATION_REPORT.md) · [Lộ trình](docs/09_ROADMAP_AND_BACKLOG.md) · [Changelog](docs/development/CHANGELOG.md) · [Nhật ký GitHub](docs/development/GITHUB_PUBLISH_LOG.md).

Hướng dẫn và giới hạn riêng cho [Tutor exploratory demo](docs/demo/TUTOR_EXPLORATORY_DEMO_WALKTHROUGH.md), [logic pipeline tiếng Việt](docs/demo/CURRENT_MVP_LOGIC_VI.md), [so sánh demo với nghiên cứu mù](docs/demo/DEMO_VS_BLIND_RESEARCH.md), [kết quả E2E](docs/demo/TUTOR_E2E_DEMO_RESULT.md) và [acceptance matrix](docs/demo/DEMO_ACCEPTANCE_MATRIX.md).

## Giới hạn cần trình bày cùng demo

Trong fixture nghiên cứu PetClinic, Bell(6)=203 và mười phân hoạch đạt chi phí nhỏ nhất bằng 0 theo constraint đã cấu hình. Pet–Visit vẫn `UNRESOLVED` và `INSUFFICIENT_EVIDENCE`. Owner Search là `NOT_MEASURED`. Các giả thuyết Sync/Async và diễn giải của LLM cần review theo nguồn. [Giới hạn đánh giá](docs/05_VALIDATION_AND_RESEARCH_LIMITS.md)
