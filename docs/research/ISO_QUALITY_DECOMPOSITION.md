# Phân rã Architectural Quantum theo chất lượng

## Audit đầu kỳ

Baseline kiểm tra tại `f041afb8bff756dd8c33b085459a9c9bdd79cdc0`. Repository có hai đường chạy. `research_app.py` dùng `eqcr.pipeline.run_pipeline`, trích xuất offline hoặc có review, optimizer exhaustive/CP-SAT, architecture graph, Draw.io và bundle. `app.py` là Studio so sánh ba phương án trên sơ đồ component do người dùng nhập. Hai đường chạy dùng dữ liệu và hàm điểm khác nhau.

| Yêu cầu | Baseline và khoảng trống | Thay đổi trong phạm vi |
|---|---|---|
| ISO và driver kiến trúc | `studio_quality` có chín nhãn; P9 giữ trạng thái `UNMAPPED`. | Registry đúng phiên bản, mã đến cấp dưới và driver ngoài ISO. |
| FR/NFR | `RawRequirements` nhận FR với mã cũ. Studio có nhãn FR/NFR và chuỗi gợi ý. | Báo cáo nguyên tử có span và review, qua package nghiên cứu tự chọn. |
| Kịch bản và P4 | P9 có sáu ô và trace theo scenario. P4 đã có FR, activity, operation và responsibility. | Giữ P4, mở rộng scope kịch bản, chất lượng và trace theo ứng viên. |
| P5/P6 | Evidence và relation audit giữ `PRESENT`, `SCOPED_ABSENT`, `UNKNOWN`. Policy hiện hữu chỉ sinh soft. | Phân loại chiều coupling và kiểm căn cứ hard trong luồng mới. |
| P7/P8 | Có hard feasibility, core mâu thuẫn, exhaustive/CP-SAT, hard và soft có chứng từ. Contract được áp dụng sau optimizer. | Áp dụng preference theo kịch bản và contract có căn cứ trước giải. Đánh giá theo nhiều trục trên tập ứng viên được solver trả về. |
| Sync/Async | Contract v1 có timing, consistency, retry, timeout, idempotency. Chưa phân biệt event/command và thiếu các field quyết định cụ thể. | Lớp quyết định opt-in có timing, freshness, atomicity, delivery, ordering và trạng thái unresolved. |
| Profiles và export | P9 là profile theo scenario của phương án đang xem. Graph P8 và Draw.io đã có. Studio đưa danh sách đặc tính vào từng hộp Quantum. | Profile theo từng Quantum và interaction, dùng export hiện hữu, chuyển chi tiết Studio sang panel riêng. |
| Human review | P2 cần independent source-only lock. Các fixture và run offline có phân loại provenance. | Giữ cổng P2 và bổ sung worked example định danh minh họa. |

## Nguồn phương pháp

- ISO/IEC 25010:2023 là taxonomy chất lượng sản phẩm. Căn cứ tên và cây phân cấp từ điều 3 và Hình 2. Diễn giải vận hành và phép kiểm trong registry do dự án viết. [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html)
- Kịch bản sáu phần mô tả tình huống có thể kiểm tra. Truy tình huống qua component và connector để nêu rủi ro hoặc đánh đổi. [SEI về quality attribute scenarios](https://insights.sei.cmu.edu/documents/734/2004_005_001_14396.pdf) · [ATAM](https://www.sei.cmu.edu/library/atam-method-for-architecture-evaluation/)

## Đặc tả triển khai

Một project JSON bật phân tích mới bằng object `quality_decomposition`. `source_documents` nhận văn bản, loại đã khai báo nếu có và provenance. `classification_reviews` tham chiếu ID nguyên tử và đúng span. Span dùng chỉ số ký tự Python, đầu bao gồm và cuối loại trừ. Kết quả giữ văn bản gốc và ghi rõ dấu hiệu dẫn đến từng loại FR, NFR, MIXED, ARCHITECTURAL_CONSTRAINT, DESIGN_DECISION hay UNKNOWN. Câu hỗn hợp được tách ở dấu phân cách hoặc liên từ khi nhận ra hai phần FR/NFR. Trường hợp chưa tách được vẫn MIXED. Khai báo từ tài liệu chuẩn bị mang `PREPARED_FIXTURE`. Tài liệu `LLM_PROPOSAL` vẫn là đề xuất, kể cả khi span resolve. Review kiến trúc phải dẫn lại nguồn thực.

Registry `1.0.0` gồm đúng 9 characteristics và 40 subcharacteristics. ID theo điều khoản, chẳng hạn `ISO25010-2023-3.2.1` cho Time behaviour. Ba driver `ARCH-DEPLOYABILITY`, `ARCH-TRANSACTIONAL-CONSISTENCY` và `ARCH-OBSERVABILITY` có ID riêng. ID ISO đã khai báo phải tồn tại. Ánh xạ giữ `PROPOSED` cho tới khi nhãn có trong nguồn đã khai báo hoặc có review. Các phép đo gợi ý trong registry có provenance `PROJECT_AUTHORED_GUIDANCE`.

Một NFR đã được xác nhận nguồn hoặc review có ít nhất một kịch bản. Thiếu mô tả cụ thể thì sáu trường là `UNKNOWN` và target là `MEASURE_MISSING`. Mỗi trường được điền có span thuộc NFR tương ứng. ID FR và responsibility nhiều-nhiều, với kiểm tra responsibility đi qua FR liên quan. Workflow và operation lấy từ bản ghi P4. Chỗ chưa có activity giữ `UNRESOLVED`. Ngân sách khai báo có thể gắn vào responsibility hoặc giao tiếp. Sổ ngân sách kiểm tổng phân bổ với trần ms có span. Phép so này là kiểm phân bổ số học; p95 của cả luồng phải đo trên luồng hoàn chỉnh.

Số đo hệ thống theo ms có thể nhập bằng bản ghi quan sát có review, ID lần chạy và nguồn `SUPPLIED_OBSERVATION`. Cổng kiểm metric, môi trường, đơn vị và ngưỡng từ nguồn riêng. `MEASURED_PASS`/`MEASURED_FAIL` chỉ áp dụng cho quan sát đó ở scope hệ thống. Quantum và tương tác vẫn giữ trạng thái đo lường riêng. Ví dụ minh họa dùng `NOT_MEASURED`.

### Ràng buộc và thứ hạng

Policy `EQCR-QUALITY-DECOMPOSITION@1.0.0` phân các predicate hiện hữu theo 12 chiều coupling và một chiều deployability riêng. Từng record giữ nguyên trạng thái và review. Scope chưa ghi tiếp tục `UNKNOWN`. Cổng hard rule yêu cầu FR hoặc architectural constraint đã xác nhận, đúng cặp responsibility và căn cứ đã review. Must-link chỉ dùng evidence giao dịch bất khả phân hoặc invariant đã xác nhận. Cannot-link cần bằng chứng phân tách bắt buộc. Cùng bảng, cùng characteristic hoặc bằng chứng thiếu quyết định review chỉ tạo câu hỏi hoặc preference khi được xác nhận phù hợp.

Với phân hoạch `P`, đặt `x_ij(P)=1` khi hai responsibility cùng nhóm. Hard must-link yêu cầu `x_ij=1`; hard cannot-link yêu cầu `x_ij=0`. Optimizer loại nghiệm vi phạm và trả core khi mâu thuẫn. Trên tập khả thi,

```text
J(P) = Σ w(c) × I[vi phạm soft constraint c]
```

Các trọng số là điểm chính sách do input/review khai báo. Kịch bản đã review có thể thêm preference trên cặp thuộc scope. Quyết định Sync hoặc Local đã review có thể thêm điểm ưu tiên giữ cặp, còn Async chỉ sinh điểm ưu tiên tách khi có căn cứ về tính sẵn sàng độc lập và trọng số do reviewer nhập. ISO ID tự thân không thêm hard rule.

Sau giải, bảng so sánh giữ vector `(J, scope NFR bị cắt, cạnh workflow đã duyệt bị cắt, cạnh Sync đã duyệt bị cắt, cặp chưa giải quyết hoặc chưa review qua ranh giới)`. Vector tách riêng các chiều, rồi dùng Pareto và tie-break từ trái sang phải, cuối cùng theo ID. Số Quantum, số cạnh đi qua ranh giới, cơ chế Async cần kiểm và giả định vận hành hiện riêng. Cặp chưa hề quan sát không tạo một phiếu chi phí cũng không được suy ra là vắng mặt. Bộ giải hiện hữu cho tối đa tám responsibility xuất toàn tập khả thi; CP-SAT 9–50 xuất tập co-optima đã báo cáo. Pareto trên CP-SAT giới hạn theo tập đó. Ba ứng viên là giới hạn shortlist, có thể ít hơn nếu pool nhỏ. Phương án ngoài Pareto có mã phương án trội hơn.

### Quyết định tương tác

| Mode | Căn cứ để đề xuất | Câu hỏi cần xác nhận |
|---|---|---|
| LOCAL | Có căn cứ về thay đổi atomically với nhất quán mạnh. Ứng viên đặt hai trách nhiệm chung một Quantum. | Hai thao tác thực tế có dùng cùng giao dịch? |
| SYNC_REQUEST_RESPONSE | Phải có kết quả hoàn tất trước khi bên gọi tiếp tục, với trường request/response, deadline, độ mới, timeout và xử lý lỗi. | Thử đo đường gọi, deadline, lỗi lan truyền. |
| ASYNC_EVENT | Bên gọi được kết thúc trước, nghiệp vụ cho phép độ trễ và message mô tả một sự kiện đã xảy ra. | Phải kiểm delivery, retry, idempotency, ordering và replay. |
| ASYNC_COMMAND | Điều kiện deferred tương tự, với message yêu cầu một hành động. | Phân biệt accepted với completed; kiểm xử lý thất bại và xử lý trùng. |
| UNRESOLVED | Thiếu span cho timing, consistency, atomicity hay freshness, thiếu deadline hoặc thiếu hợp đồng cần thiết. | Bổ sung chính xác trường còn thiếu trong matrix. |

Atomicity cùng với đề xuất phân tán cần protocol, bằng chứng được trích dẫn và quyết định review trước khi dùng phương án đó. Một giao dịch Local đi qua hai Quantum vẫn unresolved trong phương án đó. Profile giữ caller/callee, phương án dự phòng có điều kiện, lợi ích, rủi ro, cơ chế điều khiển và các căn cứ có thể thay đổi quyết định. Tầng tích hợp vẫn để UNKNOWN khi nguồn chưa mô tả hạ tầng.

## Ca minh họa đặt thiết bị

`FR-01`–`FR-05` nối `ACT-01`–`ACT-05` và các operations để tạo `R1` gửi yêu cầu, `R2` giữ thiết bị, `R3` hiển thị kết quả, `R4` công bố sự kiện và `R5` cập nhật báo cáo. Đây là các trách nhiệm chuẩn bị từ chức năng. Nhãn chất lượng bổ sung scope cho chúng.

- `NFR-RESERVATION.A01` → `QS-RESERVATION` → Time behaviour → `R1,R2,R3`. Tình huống có người mượn gửi yêu cầu ở tải cao, ba trách nhiệm xử lý và trả kết quả, mục tiêu p95 ≤ 400 ms. `SRC-BUDGET` ghi 120 ms cho R2, 40 ms cho giao tiếp I-RESERVE và caller deadline 160 ms. Phần còn lại chưa được phân bổ.
- `NFR-REPORT.A01` → `QS-RECOVERY` → Recoverability → `R5`. Cần dựng lại view sau khi worker restart. Độ dài thời gian phục hồi mang `MEASURE_MISSING`. Observability là driver riêng.
- `SRC-WAIT` dẫn đến đề xuất Sync của `I-RESERVE`. `SRC-EVENT` cho phép báo cáo cập nhật sau tối đa 5 phút. Hợp đồng đề xuất cho `I-REPORT` ghi delivery at least once, dùng ID và revision để xử lý trùng, chỉ áp dụng revision mới nhất. Hai lựa chọn có provenance quy tắc và trạng thái `PROPOSED`.
- `EV-REPORT-INDEPENDENCE` là `SCOPED_ABSENT` đối với cùng giao dịch đặt chỗ. `EV-DEPLOYABILITY-MISSING` là `UNKNOWN`. `SOFT-REPORT-ISOLATION` là giả định what-if có hai điểm ưu tiên tách R2/R5.

| Ứng viên | Nhóm | Vector | Trade-off từ đầu vào |
|---|---|---|---|
| P004 | R1 R2 R3 / R4 R5 | 0, 0, 0, 0, 1 | Giữ kịch bản đặt chỗ trong một nhóm, tách báo cáo khỏi thao tác giữ thiết bị. Khoảng trống deployability R2/R5 vẫn qua ranh giới. |
| P001 | R1 R2 R3 R4 R5 | 2, 0, 0, 0, 0 | Một Quantum tránh giao tiếp qua ranh giới đang chưa review. Báo cáo và giữ thiết bị cùng nhóm, chịu hai điểm policy. |
| P002 | R1 R2 R3 R4 / R5 | 0, 0, 0, 0, 2 | Tách worker báo cáo khỏi phát event. Cần review thêm hợp đồng qua ranh giới R4/R5. P004 trội theo vector đã khai báo. |

Exhaustive xét và giữ 52 phân hoạch. Tie-break di sản của optimizer chọn P002 trong các nghiệm `J=0`. Shortlist dùng vector chất lượng xếp P004 đầu. Sau khi bổ sung mệnh đề chờ và span vào `SRC-WAIT`, I-RESERVE đổi từ `UNRESOLVED` sang `SYNC_REQUEST_RESPONSE`. Nhóm, thứ tự shortlist và `J=0` giữ nguyên vì đề xuất chưa có trọng số review. Test cô lập kiểm tra riêng rằng một quyết định Async có trọng số hoặc thay đổi trọng số quality sẽ làm optimizer tái phân hoạch.

## Tái lập và định dạng báo cáo

```powershell
.\.venv\Scripts\python.exe -m scripts.run_quality_decomposition --output runs/quality-decomposition/replay
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run research_app.py --server.port 8502
```

CLI chạy lại cùng input và đối chiếu JSON, kiểm bundle ZIP và xuất hash. `quality-decomposition.json` chứa registry, classification, scenario matrix, trace P4, coupling P5/P6, partitions, interaction decisions và quality profiles. Mỗi ứng viên có file architecture JSON và Draw.io. `before-after.json` ghi hai trạng thái thử. `validation.json` và `reproducibility.json` ghi phạm vi kiểm tra. Thêm `--project <file.json>` để chạy project tự cấp.

Trong Research UI, chọn **Load ISO quality worked example** → **Run offline fixture** → **Quantum & Contracts**. Chọn ứng viên, Quantum hoặc connection để đọc profile và tải sơ đồ. Trong Studio, bấm mã Quantum trên sơ đồ hoặc chọn tương tác trong panel **Quality Profile**.

## Giới hạn nghiên cứu

- Rule classifier là đề xuất dựa trên dấu hiệu và cấu trúc câu. Cần kiểm tra trên tập tài liệu độc lập có adjudication trước khi báo độ chính xác. Các review qua project JSON cần được đối chiếu với danh tính và nguồn bên ngoài pipeline.
- 52 phân hoạch, vector, hợp đồng và ledger là kết quả mô hình minh họa. Baseline P4 do fixture cung cấp, các khẳng định về deployability, scalability và failure isolation cần bằng chứng riêng. Phép kiểm span xác nhận chữ và vị trí; ý nghĩa kỹ thuật cần người review.
- Evidence cho các chiều coupling còn phụ thuộc mức phủ nguồn. Kết quả CP-SAT profile xét các co-optima được báo cáo, chưa đánh giá toàn bộ nghiệm khả thi. Bộ kiểm số đo có scope hẹp là latency ms có nguồn thực nghiệm và điều kiện trùng khớp.
- Tutor Support tiếp tục `P2_BLOCKED_INDEPENDENT_ANNOTATION`. Ca thiết bị và test cô lập dùng provenance minh họa, tách khỏi P2 blind research.
