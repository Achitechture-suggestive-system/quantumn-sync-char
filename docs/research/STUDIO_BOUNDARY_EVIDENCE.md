# Hợp đồng boundary, ownership và kiểm thử lỗi cục bộ

## Bài toán và phạm vi bằng chứng

Một phân hoạch thỏa hard constraints chưa đủ để kết luận các Quantum triển khai độc lập. Cạnh ASYNC cần quy định ý nghĩa ACK, dữ liệu giữ khi bên nhận lỗi và cách retry. Kho dữ liệu đi qua nhiều Quantum cần quyết định ai được ghi, bất biến phải giữ và consistency mong muốn.

Studio bổ sung hai loại quyết định có nguồn và một harness thực thi có phạm vi giới hạn:

| Đầu ra | Nguồn/provenance | Kết luận được phép |
|---|---|---|
| Trích dẫn và scope requirement | Source requirement + kiểm span/hash xác định | Văn bản tham chiếu còn khớp revision. Chưa chứng minh diễn giải đúng. |
| Hợp đồng tự do/ownership đã review | Human decision hoặc Prepared fixture được chọn rõ | Quyết định đã được ghi cùng actor khai báo và rationale. Chưa có chứng minh vận hành. |
| Mode vào optimizer | Deterministic transformation từ hợp đồng được duyệt | Phân nhóm dùng SYNC/ASYNC hiện hành, giữ các hard rules. |
| Giao thức `OUTBOX_INBOX_V1`, dữ liệu và lịch gây lỗi | Prepared fixture | Mã tham chiếu tổng hợp `APPLY_EVENT`, chưa có nghiệp vụ Ticket/Tutor. |
| HTTP, SQLite, retry và trạng thái worker trong báo cáo probe | Deterministic transformation thu thập local runtime observation | Hành vi quan sát được trong lần chạy và lịch lỗi hữu hạn đó. |
| Ranh giới và hồ sơ ownership theo phương án | Deterministic transformation + architectural policy | Vị trí tương tác/kho qua Quantum và những bằng chứng còn thiếu. |

Phần này không phát sinh proposal từ LLM. Proposal Ollama vẫn qua luồng riêng; không được đổi dữ liệu mẫu thành `LLM_PROPOSAL`.

## Review và chuỗi nhân quả

Trong **Hợp đồng tương tác và quyền ghi dữ liệu**, chọn cạnh, các requirement căn cứ và đoạn trích nguyên văn. Điền operation, data dependency, request/response, versioning, consistency, latency budget, failure handling, retry, timeout và idempotency. Để **Lưu nháp** giữ mode hiện hành; muốn áp dụng phải xác nhận bên gọi cần chờ hoặc được phép trả sớm, bật duyệt, khai báo actor/rationale rồi lưu.

Hợp đồng đã duyệt cập nhật mode và bỏ tập điều kiện cũ được thay thế trong một checkpoint trước–sau. Không tự bỏ `local_transaction`, `KEEP_SHARED`, `keep_apart` hoặc policy bảo vệ. ASYNC không thể thay giao dịch cục bộ SYNC mà chưa có thay đổi policy riêng. Mode thay làm thay đổi chi phí crossing/async seam và có thể đổi thứ hạng. Bản nháp chưa có ảnh hưởng này.

Hợp đồng gắn **mọi** source digest/span, catalog digest, claim digest và fingerprint của các kho được chọn. Đổi nguồn phụ, mode, danh mục component hoặc membership/policy của kho khiến hợp đồng cũ thành cần review lại và chặn optimizer. Xác nhận lại chỉ binding của cạnh không bỏ được yêu cầu review hợp đồng nhiều nguồn. Có thể review lại đầy đủ, hoặc gỡ hợp đồng có actor/rationale: giữ mode và hard rules như giả định thiết kế được ghi nhận rõ, không còn gọi là hợp đồng đã được kiểm chứng.

Ownership có `SINGLE_WRITER` hoặc `PARTITIONED_WRITERS`, writer IDs, partition key khi cần, invariant, consistency và replication lag tùy chọn. `UNKNOWN` được giữ trong nháp. Bản được review cần writer hợp lệ, nguồn còn khớp và trường bắt buộc đầy đủ. Quyết định này không tự đổi chính sách kho. Khi nguồn/kho đổi, hồ sơ hiện `REVIEW_REQUIRED`; không dùng text invariant để suy ra một chứng minh hình thức. Lag khai báo vẫn là `NOT_MEASURED`.

Checkpoint và JSON so sánh chứa hợp đồng, ownership, provenance và boundary profiles của từng phương án. Chọn A/B/C cập nhật đúng boundary của sơ đồ đang xem. Profile dùng `REVIEWED_NOT_RUNTIME_VERIFIED`, `REVIEWED_INVARIANT_NOT_PROVEN` hoặc `REVIEW_REQUIRED`; deployability luôn `NOT_VERIFIED`.

## Chạy probe trên UI

1. Chọn cạnh CREATE→ROUTE, requirement làm căn cứ, actor/rationale và nguồn quyết định `PREPARED_FIXTURE` nếu đang demo kỹ thuật.
2. Chọn SYNC hoặc ASYNC, bật **Dùng giao thức mẫu để kiểm thử cục bộ**. Mười một trường chuyển sang giao thức mẫu có phiên bản. Đọc ý nghĩa ACK, timeout và dữ liệu trước khi duyệt.
3. Xác nhận tín hiệu mode, bật duyệt rồi **Lưu review hợp đồng**. Đầu vào được phân nhóm lại và lưu checkpoint.
4. Chọn phương án mà hai đầu nằm ở hai Quantum, ví dụ P011 của mẫu Ticket Support. Mở **Boundary: hợp đồng, ownership và chạy thử**, chọn cạnh và bấm **Chạy thử lỗi và xử lý trùng cục bộ**.
5. Đọc từng phép kiểm và tải báo cáo. Đổi input, hợp đồng hoặc phương án làm kết quả cũ hiện `STALE`. Probe không chạy trên phiên oracle hoặc hợp đồng tự do chưa có harness tương ứng.

Chuỗi thực thi gồm hai tiến trình Python HTTP ở loopback, mỗi tiến trình giữ file SQLite riêng. Producer ASYNC ghi command đã nhận và outbox trong cùng transaction rồi trả 202, không chờ receiver. Relay là thao tác `/dispatch` được kích hoạt rõ. Receiver ghi ID, payload và effect tổng hợp trong cùng transaction. SYNC chỉ trả 200 sau ACK đã commit; lỗi giao tiếp sau tối đa ba lần thử trả 503 và có thể còn kết quả commit chưa biết.

Lịch kiểm hữu hạn:

| Ca | Observation cần có |
|---|---|
| Receiver chưa chạy | ASYNC trả 202 và giữ một outbox pending; SYNC trả 503. |
| Retry khi receiver lỗi | Đúng tối đa ba attempt thất bại trong một invocation. |
| Restart producer | Command/outbox ASYNC đã commit vẫn còn. |
| Commit rồi mất ACK | Retry cùng event ID, receiver báo duplicate; chỉ một effect được giữ. |
| Lặp request, đổi payload cùng ID | Request giống nhau không thêm effect; payload khác trả 409 ở cả producer và receiver. |
| Restart receiver | Effect đã commit còn nguyên trong file riêng của receiver. |
| Commit rồi phản hồi chậm | Attempt đầu timeout 300 ms, attempt sau nhận duplicate, không thêm effect thứ hai cho cùng ID. |
| Version ngoài v1 | Trả 400, không thực thi effect. |
| Kết thúc luồng | ASYNC hết pending sau ACK; SYNC thấy hai effect tổng hợp đã commit trước response thành công. |

Mỗi run giữ `input.json`, `observations.json`, `report.json`, config, stderr và hai file SQLite trong `runs/quantum-studio/boundary-probes/probe-…/`. Report ghi PID, xác nhận dừng worker, Python/SQLite/platform, fingerprint model/contract/partition, hash artifact và hash mã harness. Không stage các run này vào Git.

Có thể tái chạy input đã lưu bằng CLI, thay đường dẫn và candidate theo model thực tế:

```powershell
.\.venv\Scripts\python.exe -m eqcr.studio_probe --model path\to\reviewed-model.json --candidate-id P011 --edge CREATE ROUTE --output-root runs\quantum-studio\boundary-probes
```

File `reviewed-model.json` là object Architecture, ví dụ trường `architecture` của checkpoint hay bản so sánh; không truyền toàn checkpoint cho `--model`. Không cần Ollama, credential hay server ngoài máy cho probe.

## Nguồn nghiên cứu và cách áp dụng

- Peter Bailis, Alan Fekete, Michael J. Franklin, Ali Ghodsi, Joseph M. Hellerstein, Ion Stoica. **Coordination Avoidance in Database Systems**, *PVLDB* 8(3), 185–196, 2014, trình bày tại VLDB 2015. Bài dùng operation và invariant để phân tích invariant confluence. Studio yêu cầu reviewer khai báo chúng, nhưng chưa triển khai phân tích I-confluence hay chuyển kết quả hiệu năng của bài vào dự án. [PDF tác giả/PVLDB](https://www.vldb.org/pvldb/vol8/p185-bailis.pdf)
- Jim Gray và Leslie Lamport. **Consensus on Transaction Commit**, *ACM TODS* 31(1), 133–160, 2006; bản MSR-TR-2003-96, tháng 01/2004. Bài mô tả 2PC/Paxos Commit cho quyết định commit. Studio giữ nguyên hard policy giao dịch cục bộ; prototype không thực thi 2PC/Paxos và không chứng minh commit nguyên tử qua Quantum. [Microsoft Research](https://www.microsoft.com/en-us/research/publication/consensus-on-transaction-commit/)
- Chris Richardson, **Transactional outbox**, Microservices.io, truy cập 27/11/2026. Mẫu ghi thay đổi và outbox trong một transaction, relay có thể gửi trùng. Studio dùng command/effect tổng hợp và relay được gọi thủ công; chưa có broker, đa producer hoặc bảo đảm ordering tổng quát. Đây là nguồn pattern thực hành, không phải một bài báo peer-reviewed. [Nguồn của tác giả](https://microservices.io/patterns/data/transactional-outbox.html)
- Chris Richardson, **Idempotent Consumer**, Microservices.io, truy cập 27/11/2026. ID đã xử lý và side effect cần cùng transaction. Receiver mẫu dùng unique event ID, giữ canonical payload để từ chối cùng ID khác body. Phạm vi là một file SQLite receiver, không suy ra exactly-once toàn hệ thống. [Nguồn của tác giả](https://microservices.io/patterns/communication-style/idempotent-consumer.html)
- SQLite, **Transactions** và **Atomic Commit**, tài liệu chính thức. Được dùng cho semantics transaction cục bộ của prototype, chưa kiểm power loss/filesystem/network storage hay multi-writer contention. [Transactions](https://www.sqlite.org/lang_transaction.html) · [Atomic Commit](https://www.sqlite.org/atomiccommit.html)

## Giới hạn còn giữ

### Sửa lỗi đọc readiness trên Windows — 28/11/2026

Một lần regression ASYNC thất bại ở `probe-f6eb25bbced445a7a85199c165290e7d` (pytest-380) vì PermissionError khi đọc file ready của producer vừa restart. File đọc được về sau; chưa đo được tác nhân gây khóa, không kết luận do antivirus hay giao thức nghiệp vụ. Report cũ chỉ có hai assertion và giữ FAILED. Trường `workers_stopped=true` của nó chỉ bao phủ worker đã đăng ký; kiểm hệ điều hành phát hiện launcher/child 30616/29860 của constructor bị lỗi còn sống. Hai tiến trình khớp đúng config lần chạy đã được dừng; không sửa report cũ.

Worker hiện chờ đọc lại khi file chưa có, đang bị khóa hoặc JSON chưa đủ, vẫn trong thời hạn khởi động 10 giây. Constructor thất bại sẽ stop worker trước khi ném lỗi; ready port phải là integer 1–65535. Không tăng timeout giao thức 300 ms, không đổi retry/atomicity hoặc bỏ assertion. Hash harness thay đổi làm bằng chứng cũ STALE đúng thiết kế.

Kiểm lại nhóm boundary/startup có **15 tests qua**, gồm hai mode thực thi bằng tiến trình thật và năm tests mới mô phỏng permission/partial JSON, hết hạn và port sai/dọn worker. Kiểm hệ điều hành sau đó không thấy tiến trình `eqcr.studio_probe_worker`. Trace lỗi giữ trong thư mục tạm của pytest, không stage. Đây là sửa độ tin cậy harness, không phải kết quả LLM hoặc quality PASS.

`PROTOTYPE_CONTRACT_CHECK_PASSED` chỉ nói về các assertion của giao thức mẫu và run cụ thể. Đây chưa phải triển khai Ticket/Tutor, chứng minh invariant nghiệp vụ, khả năng triển khai độc lập hay quality PASS. Chưa kiểm TLS, authentication, broker, schema migration, multi-writer, tải lớn hoặc mọi interleaving lỗi. Bounded retries và dispatch thủ công không chứng minh eventual delivery. Các thời gian attempt là observation của lần gây lỗi, chưa là benchmark hay latency SLO; `quality_measurement_status=NOT_MEASURED`.

Kiểm tra hồi quy, provenance, stale review, bảo toàn hard constraints, đường UI và hai mode thực thi nằm ở `tests/test_studio_boundaries.py`. Các label và quyết định trong tests là `PREPARED_FIXTURE`; không có semantic accuracy hoặc independent annotation mới trong mốc này.
