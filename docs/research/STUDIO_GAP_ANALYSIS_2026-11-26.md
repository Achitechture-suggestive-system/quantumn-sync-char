# Quantum Studio — khoảng trống và hướng hoàn thiện

Ngày rà soát 26/11/2026. Mã được kiểm tra tại `ce7be443e5d6211016cc2e939e775b939774a278`, nhánh `feat/quantum-tradeoff-workbench`. Phạm vi chính là entrypoint `app.py` và các module `studio_*`, `quantum_tradeoff.py`. Các chức năng của `research_app.py` được đối chiếu để xác định phần có thể tái sử dụng. Số liệu bên dưới là kiểm tra trên dữ liệu tổng hợp của repo.

Studio đã có phân hoạch chính xác trong giới hạn tám component, truy vết đặc tính theo từng phương án, Human Review chọn phương án, chẩn đoán xung đột và mô phỏng tập sửa tối thiểu. Khoảng trống lớn nhất nằm ở việc tạo đầu vào có căn cứ từ yêu cầu mới, quản lý quyết định ánh xạ, xử lý thông tin chưa rõ và liên hệ điểm thiết kế với mục tiêu chất lượng.

## 1. Luồng nhân quả đang chạy

| Bước | Studio hiện thực hiện | Phần cần bổ sung |
|---|---|---|
| Nhập requirements và workflow | Nhập câu có mã, loại và component phụ trách trong sơ đồ. Component đã được khai báo sẵn. | Đề xuất nhiều trách nhiệm từ yêu cầu mới và đánh giá đầy đủ các mệnh đề, kể cả phủ định và điều kiện. |
| Phân tích ISO/component | `quality_suggestions` dùng regex, `component_mentions` tìm tên hoặc ID. Gói LLM đã lưu cung cấp câu, component và một đề xuất nhãn để review. | Gọi Ollama trực tiếp cho yêu cầu hiện tại, tách tác vụ và lưu trạng thái từng đề xuất. |
| Evidence và Human Review | Kiểm ID, schema, quote nằm trong câu. Bấm xác nhận sẽ tạo `quality_allocations`. | Quyết định approve/correct/reject/defer theo từng mệnh đề, nguồn và phiên bản, cùng căn cứ khi reviewer bổ sung cách diễn giải. |
| Tương tác và chính sách | Mode và mức ảnh hưởng của cạnh được nhập trên sơ đồ. Ba kiểu hard constraint dùng chung biểu diễn giữa bộ giải và chẩn đoán. | Hợp đồng tương tác có điều kiện, lỗi, retry, idempotency, độ nhất quán và chính sách bảo vệ các quy tắc bắt buộc. |
| Phân hoạch và điểm | Liệt kê các phân hoạch, lọc hard constraint, giữ Pareto rồi xếp hạng theo chế độ. | Đánh giá độ nhạy, độ phủ bằng chứng, bất định và tác động của việc thay đổi yêu cầu. |
| Quantum và chất lượng | Sơ đồ và thẻ hiển thị các đặc tính, component, ID yêu cầu và routing của phương án chọn. `quality_measurement_status` là `NOT_MEASURED`. | Quality scenario có thước đo và môi trường, cùng bằng chứng kiểm thử hoặc mô hình dự đoán theo từng phương án. |

`app.py` hiện không gọi client Ollama hoặc `run_pipeline` khi phân tích sơ đồ. Việc gọi Ollama cho các gói tổng hợp nằm ở `scripts/generate_studio_requirements.py`. Pipeline nghiên cứu có biểu diễn evidence, scenario và CP-SAT riêng. Hai đường chạy cần adapter và kiểm tra tương đương nếu kết nối. [Studio](../../app.py) · [Client Ollama](../../eqcr/ollama.py) · [Pipeline nghiên cứu](../../eqcr/pipeline.py)

## 2. Các phép kiểm chạy lại

Ngày 26/11/2026, toàn bộ regression suite đạt **158 tests** trong 24,71 giây ở máy kiểm tra. Chạy thêm các phép đối chứng qua API Python của Studio cho kết quả sau. Không có lần inference mới trong đợt rà soát này.

| Phép đối chứng | Kết quả quan sát | Kết luận có thể rút ra |
|---|---|---|
| OC-02 chứa “không phải đáp ứng mốc 150 ms” và yêu cầu khôi phục | Regex đề xuất cả *Performance efficiency* từ `150 ms` và *Reliability* từ `khôi phục`. | Dấu hiệu chữ chưa xác định phạm vi phủ định. |
| Ép ánh xạ Performance efficiency vào REPORT với quote `150 ms` của OC-02 | Validator chấp nhận, P031 đạt 7 điểm. | Chuỗi trích xuất có thật vẫn có thể diễn giải sai. |
| Xác nhận Reliability cho REPORT với quote rỗng | Validator chấp nhận, P031 đạt 7 điểm. | Luồng cho phép xác nhận chưa có trích dẫn, cần ghi rõ nguồn quyết định bổ sung. |
| Gắn hai câu mã hóa cùng nghĩa với hai ID khác nhau | Điểm P031 lần lượt 7 và 9, topology giữ nguyên. | Mỗi cặp ISO–NFR được tính riêng nên paraphrase có thể làm tăng chi phí. |
| OC-01 đổi mục tiêu p95 từ 900 ms thành 9.000 ms và cập nhật quote tương ứng | Cả hai đầu vào đều xếp P011 đầu, vector `(0,1,0,0,1)`, 8 điểm. | Bộ giải tiêu thụ phạm vi đặc tính, chưa tiêu thụ độ chặt của ngưỡng. |
| OC-09 đổi ROUTE→COMPLETE từ SYNC thành UNKNOWN | P006 từ 18 xuống 12 điểm. | Bỏ đóng góp của cạnh thiếu bằng chứng làm điểm giảm. |
| OC-11 đổi CREATE→ROUTE từ ASYNC thành UNKNOWN | P031 từ 5 xuống 4 điểm. | Ranh giới điều kiện chưa được mô hình hóa có thể tạo lợi thế về điểm. |
| OC-10 giữ nguyên hai hard constraints mâu thuẫn | 0 nghiệm. Mô phỏng bỏ tách cho 10, mô phỏng bỏ giao dịch cục bộ cho 27. | Cơ chế vô nghiệm và mô phỏng hiện có hoạt động trên mô hình đã khai báo. |

Các phép đối chứng không thay mô hình demo hay lịch sử review của người dùng. Dữ liệu chạy cục bộ được lưu ở `runs/studio-gap-audit-2026-11-26/findings.json`. Nguồn của các câu thử là bộ oracle tổng hợp đã có. [12 ca gốc và kết quả Ollama ngày 21/11](../demo/STUDIO_TRICKY_CASES_ORACLE.md)

## 3. Khoảng trống có thứ tự ưu tiên

### G1 — Đề xuất Ollama chưa đi từ input hiện tại vào một phiên review thống nhất

**Hiện trạng.** Studio nạp đề xuất từ gói JSON đã chọn. Client đang có hỗ trợ prompt, thông tin model và dữ liệu phản hồi trong luồng nghiên cứu, còn `app.py` chủ yếu dùng regex cho câu nhập mới. Một gói LLM chạy được chưa kiểm chứng cơ chế trích xuất cho câu người dùng mới nhập. [Gói hiện tại](../../eqcr/studio_cases.py) · [Script sinh dữ liệu](../../scripts/generate_studio_requirements.py)

**Hướng hoàn thiện trước.** Thêm một adapter cho input Studio, tái sử dụng cơ chế gọi và lưu metadata của `eqcr/ollama.py`. Tách đầu ra đề xuất ISO/component, quan hệ có điều kiện và chính sách cứng. Mỗi đề xuất có trạng thái `PROPOSED`, `REVIEW_REQUIRED` hoặc `REJECTED`, kèm source ID/span và phiên bản input. Nạp đề xuất giữ nguyên tập phân hoạch hiện hành cho tới khi người dùng quyết định áp dụng. Khi nguồn sửa, trạng thái áp dụng cần được đối chiếu lại với hash nguồn.

**Điều kiện hoàn thành.** Một yêu cầu mới nhập từ UI tạo ra phản hồi Ollama có request/response và model digest lưu được. Tắt Ollama có thông báo lỗi thực tế và cho tiếp tục review thủ công. Đề xuất chưa duyệt giữ nguyên vector điểm của mọi phương án. Nguồn thay đổi làm quyết định cũ hiện rõ cần review lại.

### G2 — Chưa kiểm đầy đủ nghĩa, mệnh đề và quan hệ nhân quả của requirement

**Hiện trạng.** OC-02 có phủ định, OC-03 có hai mục tiêu riêng, OC-07 và OC-12 phân biệt component bối cảnh với component chịu trách nhiệm. Các lỗi này vượt ra ngoài kiểm ID và chuỗi con. Một lần model tự kiểm lại cũng cần bằng chứng đối chiếu.

**Hướng hoàn thiện trước.** Biểu diễn từng mệnh đề với chủ thể, hành vi, mục tiêu, điều kiện và phạm vi phủ định. Hiển thị cả câu nguồn bên cạnh mệnh đề để người review kiểm tra phần bị bỏ sót. Giữ quote chính xác và cho phép reviewer bổ sung quyết định với lý do rõ ràng khi nguồn chưa diễn đạt đủ. Kiểm sự nhất quán giữa trạng thái và nội dung, ví dụ `OUT_OF_SCOPE` đi kèm ánh xạ có component phải được giữ lại để xử lý.

**Điều kiện hoàn thành.** Đầu vào OC-02 không tự áp dụng mốc phủ định, OC-03 giữ đủ hai mệnh đề, OC-07 và OC-12 giữ đúng chủ thể. Đánh giá từng loại lỗi trên ca mới dành riêng sau khi chốt prompt. Nghiên cứu TraceLLM nhấn mạnh đánh giá prompt với chia dữ liệu và các liên kết ứng viên để con người review. Việc áp dụng cấu trúc mệnh đề ở đây là thiết kế đề xuất cho Studio. [TraceLLM, Alturayeif, Ahmad và Hassine, 2026](https://doi.org/10.1007/s00766-026-00460-1)

Các cảnh báo từ khóa nên giúp reviewer tìm đoạn cần đọc kỹ. Femmer và cộng sự nghiên cứu *Requirements Smells* để đưa phản hồi sớm về dấu hiệu lỗi yêu cầu và bổ trợ review. Có thể thử cùng nguyên tắc cho phủ định, đại từ chưa rõ chủ thể và mục tiêu thiếu đơn vị, rồi đo các trường hợp báo nhầm và bỏ sót trên tiếng Việt. [Femmer, Méndez Fernández, Wagner và Eder, Journal of Systems and Software 123, 2017](https://www.sciencedirect.com/science/article/pii/S0164121216000789)

### G3 — Một mục tiêu có thể bị tính nhiều lần vì cách diễn đạt và mã nguồn

**Hiện trạng.** `component_profiles` dùng `characteristic + requirement.id` làm danh tính đặc tính. Cách này giữ được scope riêng cho các mục tiêu khác nhau, nhưng cùng một mục tiêu được diễn đạt lại cũng tạo thêm khoản chi phí. [Cách dựng profile](../../eqcr/quantum_tradeoff.py)

**Hướng hoàn thiện trước.** Thêm danh tính quality scenario và quan hệ `duplicate_of`/`refines` được review. Giữ nhiều câu nguồn trỏ vào một mục tiêu đã hợp nhất. Chỉ hợp nhất sau khi kiểm actor, điều kiện, component, đơn vị, ngưỡng và phạm vi đo. Hai câu cùng thuộc *Performance efficiency* vẫn có thể là hai mục tiêu độc lập.

**Điều kiện hoàn thành.** Thêm paraphrase của OC-05 giữ nguyên vector điểm. Hai mục tiêu p95 khác scope vẫn truy vết và đánh giá riêng. Chạy thêm ca hai câu giống chữ nhưng khác điều kiện tải để kiểm việc hợp nhất quá mức. Pipeline nghiên cứu có audit duplicate cấu trúc để tái sử dụng phần kiểm định ID/span, còn paraphrase cần thêm quyết định ngữ nghĩa. [Audit evidence hiện có](../../eqcr/evidence_audit.py)

### G4 — UNKNOWN và các chế độ có điều kiện chưa có cách chấm đủ thông tin

**Hiện trạng.** Một cặp source–target có một `mode`. Các cạnh `UNKNOWN` được cảnh báo nhưng chưa góp vào điểm. Điểm giảm 18→12 và 5→4 trong hai phép đối chứng cho thấy cần đọc điểm cùng độ phủ bằng chứng.

**Hướng hoàn thiện trước.** Giữ `UNKNOWN` và thêm độ phủ các cạnh có căn cứ vào phần so sánh. Với tập giả thuyết nhỏ đã được reviewer cho phép, tính điểm từng phương án dưới các kịch bản SYNC và ASYNC, ghi khoảng điểm và mức thay đổi thứ hạng. Sau đó mới mở rộng schema cho nhiều chế độ theo điều kiện hoặc bước nghiệp vụ. Cần thống nhất điều kiện loại trừ nhau và policy gộp điểm trước khi dùng hợp đồng có điều kiện trong optimizer.

**Điều kiện hoàn thành.** Đổi cạnh từ biết rõ sang UNKNOWN làm độ phủ giảm và hiện khoảng ảnh hưởng. Thay đổi điểm phải truy về đúng giả thuyết chưa xác nhận. OC-11 giữ đủ hai điều kiện ưu tiên/thường trong nguồn và hiển thị cả hai trong review.

Lý thuyết tối ưu robust cung cấp cách tiếp cận dữ liệu bất định và mức bảo thủ. Với Studio, kịch bản rời rạc là bước phù hợp để thử trước. Công thức robust tuyến tính của Bertsimas–Sim cần mô hình hóa lại nếu muốn dùng trực tiếp cho mode phân loại. [Bertsimas và Sim, *The Price of Robustness*, Operations Research 52(1), 2004](https://pubsonline.informs.org/doi/10.1287/opre.1030.0065)

### G5 — Điểm characteristic chưa đo khả năng thỏa NFR

**Hiện trạng.** Mục tiêu 900 ms và 9.000 ms có cùng nhãn, cùng scope nên tạo cùng phương án, cùng điểm. Các nhãn nghiệp vụ nhập tự do và nhãn ISO theo NFR đều góp vào chi phí rải/trộn. Việc giảm trộn chưa cho biết component có đạt ngưỡng vận hành hay có mức gắn kết chức năng phù hợp.

**Hướng hoàn thiện.** Biểu diễn quality scenario gồm nguồn kích thích, kích thích, môi trường, đối tượng, phản hồi và thước đo. Lưu metric, đơn vị, cửa sổ đo và target tách khỏi observation. Tái sử dụng các trường scenario và trạng thái đo đã có ở `eqcr/pipeline.py` qua adapter. Giữ từng khoản của điểm thiết kế và bổ sung bằng chứng dự đoán/đo cho phương án khi có target system.

**Điều kiện hoàn thành.** Mỗi NFR có thước đo và cách kiểm. Mỗi kết quả chất lượng có trạng thái `NOT_MEASURED`, `PREDICTED` hoặc `MEASURED` cùng căn cứ tương ứng. Khi có mô hình dự đoán hợp lệ, đổi ngưỡng làm đổi đánh giá đáp ứng theo cùng điều kiện đo. Trước đó, ngưỡng chỉ là specification.

SEI mô tả sáu phần để làm rõ quality scenario. Nghiên cứu của Cortellessa và cộng sự tối ưu nhiều mục tiêu dựa trên mô hình hiệu năng, độ tin cậy, antipattern và khoảng cách kiến trúc. Bài báo cung cấp cách thiết kế nghiên cứu và baselines, trong khi năm trục của Studio cần đánh giá riêng trên mục tiêu của Studio. [Bachmann và cộng sự, CMU/SEI-2003-TR-004](https://www.sei.cmu.edu/documents/704/2003_005_001_14213.pdf) · [Cortellessa và cộng sự, Information and Software Technology 157, 2023](https://arxiv.org/abs/2301.09531)

### G6 — Quyết định ở mức allocation chưa có lịch sử tương ứng

**Hiện trạng.** `QualityAllocation` chỉ có characteristic, component IDs và quote. Biên bản chọn phương án có thời điểm, note và mô hình tại thời điểm review. Bấm xác nhận ISO chỉ cập nhật session state. Bản ghi lựa chọn phương án không tự thay thế lịch sử approve/correct/reject cho từng allocation. [Biểu diễn allocation](../../eqcr/quantum_tradeoff.py) · [Lưu review](../../eqcr/storage.py)

**Hướng hoàn thiện trước.** Ghi quyết định allocation với nguồn/hash, giá trị trước–sau, người thực hiện do phiên khai báo, thời điểm và rationale. Khi thay đổi scope hoặc nội dung, lưu revision thay vì chỉ có trạng thái hiện hành. Tạo đường tải lại mô hình và replay quyết định. Tái sử dụng cơ chế snapshot/revision ở pipeline nghiên cứu, bảo toàn metadata của dữ liệu cũ.

**Điều kiện hoàn thành.** Một lần sửa component được tải lại sau khi khởi động app, dựng được cùng input bộ giải và cùng vector kết quả. Có thể truy từ Quantum về quyết định và từ quyết định tới các phương án bị ảnh hưởng. Review mô phỏng được gắn nguồn riêng trong record.

### G7 — Các tập sửa INFEASIBLE thiếu ưu tiên và vòng xác nhận thay đổi

**Hiện trạng.** Thuật toán tìm tập sửa tối thiểu theo bao hàm cho ba loại hard constraints hiện tại. Mỗi quy tắc đều được xem xét để mô phỏng. Bảng sắp theo số quy tắc cần sửa, còn phần chi tiết chấm kiến trúc theo trọng số. Chưa có thuộc tính quy tắc được phép sửa, chi phí sửa nghiệp vụ hoặc tác động đến các quality scenario.

**Hướng hoàn thiện.** Thêm policy do người review khai báo cho từng quy tắc, gồm bảo vệ bắt buộc, khả năng sửa và mức ưu tiên. Chỉ tạo các phương án áp dụng được theo policy. Giữ kết quả mâu thuẫn nếu mọi cách sửa đụng quy tắc bảo vệ. Sau khi người dùng chọn một cách sửa, hiện diff nguồn và hậu quả rồi lưu revision khi áp dụng. Số quy tắc bị gỡ và điểm kiến trúc cần hiển thị thành hai thước đo riêng.

**Điều kiện hoàn thành.** OC-10 với cả hai quy tắc bảo vệ vẫn báo xung đột và lý do. Nếu chỉ một quy tắc được phép sửa, hệ thống chỉ đưa ra đường sửa theo policy đó. Thử nhiều xung đột độc lập để tránh sửa một chỗ nhưng để lại chỗ khác.

MCS/MUS và Weighted Partial MaxSAT cung cấp cơ sở cho tìm và xếp hạng sửa đổi. QuickXplain phù hợp để mở rộng giải thích khi bổ sung loại constraint ngoài quan hệ cùng/tách nhóm. Bộ chẩn đoán Studio hiện đã dùng đồ thị và liệt kê phân hoạch trong giới hạn nhỏ. [Liffiton và cộng sự, *Fast, Flexible MUS Enumeration*](https://markliffiton.com/publications/constraints_liffiton_marco.pdf) · [Ansótegui, Bonet và Levy, AAAI 2010](https://cdn.aaai.org/ojs/7545/7545-13-11075-1-2-20201228.pdf) · [Junker, AAAI 2004](https://cdn.aaai.org/AAAI/2004/AAAI04-027.pdf)

### G8 — Phân hoạch còn thiếu bằng chứng vận hành cho ranh giới Quantum

**Hiện trạng.** Studio nhận component, data store và hai loại coupling từ sơ đồ. Tách `SPLITTABLE` tính chi phí dữ liệu theo số nhóm, nhưng chưa sinh quyền ghi, ownership, replication lag, retry, idempotency hoặc điều kiện lỗi để chứng minh hai nhóm vận hành độc lập. Giao dịch cục bộ được mã hóa thành cùng Quantum là policy của mô hình.

**Hướng hoàn thiện.** Thêm giả định và bằng chứng về build/deploy, phụ thuộc runtime, schema migration, data ownership và giao thức lỗi cho mỗi boundary. Dùng một luồng có target system để kiểm chứng phương án. Nếu cần phân tán giao dịch, người review lựa chọn semantic commit hoặc bù theo bất biến nghiệp vụ trước khi tạo hypothesis kiến trúc.

**Điều kiện hoàn thành.** Có thể chỉ ra cách triển khai và kiểm thử lỗi của một boundary cụ thể, với các bằng chứng thiếu giữ ở trạng thái rõ ràng. Phần coupling của architecture quantum cần xem cả static, dynamic và communication coupling. Khung này là tham khảo thực hành bổ sung cho các bài báo trong báo cáo. [Neal Ford, O’Reilly, *Software Architecture Trade-Off Analysis*](https://www.oreilly.com/live/event-detail.csp?event=0642572219260&series=0642572007899)

### G9 — Giới hạn bộ giải Studio và độ tương đương với CP-SAT

**Hiện trạng.** Schema Studio giới hạn tám component, tối đa 4.140 phân hoạch. `eqcr/pipeline.py` dispatch CP-SAT cho 9–50 responsibility IDs với objective constraint riêng. Năm trục, biên Pareto và chẩn đoán sửa của Studio chưa có cùng backend CP-SAT. Chuyển lời gọi sang backend đang có có thể làm đổi bài toán tối ưu.

**Hướng hoàn thiện sau.** Định nghĩa adapter bảo toàn cả năm trục và policy, rồi kiểm tra với enumerator trên cùng ca ≤8 component. Đánh giá runtime, trạng thái tối ưu, timeout và độ đầy đủ của tập nghiệm. Nếu dùng tìm kiếm heuristic ở kích thước lớn, công bố độ phủ và baseline theo cùng objective.

**Điều kiện hoàn thành.** Các vector và hard constraints đồng nhất trên bộ ca nhỏ. Ca lớn có thời hạn chạy và trạng thái rõ ràng về chứng minh tối ưu, tập Pareto và các phương án đã tìm. Quy mô nên tăng sau khi các quyết định đầu vào và mục tiêu đã được kiểm chứng.

### G10 — Bộ đánh giá còn phụ thuộc các ca đã dùng để chỉnh prompt

**Hiện trạng.** Kết quả ngày 21/11 là 0/12 rồi 4/12 trên cùng bộ ca thiết kế. Lượt thứ hai thay prompt, schema và chia lô sau khi quan sát lỗi. Kết quả 12/12 của nút oracle kiểm hành vi bộ giải khi nhận đáp án chuẩn bị sẵn. Phản hồi LLM và manifest đầy đủ của các lần gọi giữ cục bộ dưới `runs/`. Gói dữ liệu trên Git đã chọn một phần để demo.

**Hướng hoàn thiện trước khi có claim nghiên cứu.** Chốt protocol và một tập phát triển, tạo tập đánh giá mới với nhãn độc lập và tách theo case/document để tránh paraphrase xuất hiện ở hai phía. Giữ prompt cố định khi chấm tập mới. So regex, LLM, LLM có review và oracle dưới cùng đầu vào. Theo dõi lỗi từng mệnh đề, bỏ sót policy cứng, lượng sửa của reviewer và thời gian thao tác. Chạy ablation đổi từng yếu tố và công bố manifest, dependency versions, raw output theo quyền chia sẻ dữ liệu.

**Điều kiện hoàn thành.** Chỉ báo cáo precision/recall/F1 khi có reference labels độc lập và cách ghép prediction–label công bố. Có số ca, nguồn, tỷ lệ abstain, lỗi policy và kết quả downstream cùng mẫu số. P2 Tutor vẫn cần reviewer phù hợp theo protocol hiện hành.

Khung kiểm oracle và các quan hệ bất biến giữa hai đầu vào giúp kiểm bộ giải khi chưa có nhãn ngữ nghĩa. Các phép thử như thêm paraphrase, đổi thứ tự ID và nạp proposal chưa duyệt cần được định nghĩa theo hành vi kỳ vọng trước khi chạy. Tổng quan của Barr và cộng sự trình bày nhiều nguồn oracle, gồm specification và metamorphic testing. [Barr và cộng sự, *The Oracle Problem in Software Testing: A Survey*, IEEE TSE, 2015](https://discovery.ucl.ac.uk/id/eprint/1471263/)

TraceLLM công bố cách chia dữ liệu và replication package. Curto, Semini và Marques-Neto lưu ý tác động của cấu hình nhiều LLM còn cần ablation và đánh giá thêm từ con người. Vì vậy, đổi prompt hoặc schema trên ca lỗi đã biết là bước phát triển cần thiết, sau đó cần ca mới để kiểm độ khái quát. [TraceLLM, Requirements Engineering, 2026](https://doi.org/10.1007/s00766-026-00460-1) · [Curto và cộng sự, Empirical Software Engineering, 2026](https://doi.org/10.1007/s10664-026-10981-6)

## 4. Trình tự hoàn thiện đề xuất

| Đợt | Việc chính | Chứng cứ cần có khi kết thúc |
|---|---|---|
| A | G1, G2, G6. Một đường source→Ollama→proposal→review→allocation có revision | Requirement mới từ UI, call thật lưu được, phản hồi chưa duyệt không đổi optimizer, sửa nguồn vô hiệu hóa quyết định cũ, tải lại tái tạo được mô hình. |
| B | G3, G4. Danh tính mục tiêu và bất định | Paraphrase không làm tăng điểm, hai mục tiêu khác scope được giữ, UNKNOWN có khoảng ảnh hưởng và độ phủ, hai mode theo điều kiện được review rõ. |
| C | G5, G8. Quality scenario và bằng chứng kiến trúc | Mỗi target có điều kiện đo, một boundary có ownership và hợp đồng lỗi, một phép đo hoặc mô hình dự đoán được đối chiếu với mục tiêu. |
| D | G7, G9. Policy sửa và khả năng mở rộng | Quy tắc bảo vệ được giữ, cách sửa có revision, backend lớn tương đương bộ nhỏ và có trạng thái tối ưu/timeout. |
| Xuyên suốt | G10. Protocol và dữ liệu đánh giá | Tập phát triển tách khỏi tập đánh giá mới, nhãn độc lập, ablation, before/after trên cùng input và manifest tái lập. |

Đợt A và B cần thực hiện trước khi mở rộng số model, số component hoặc thay bộ giải. Các kỹ thuật và điều kiện hoàn thành trong phần này là đề xuất cho bước tiếp theo. Phần code đã có được xác nhận bằng đọc nguồn, các phép đối chứng và regression suite nêu ở phần 2.

## 5. Đọc bài báo theo vấn đề cần giải

| Ưu tiên đọc | Nguồn và đóng góp | Áp dụng đầu tiên trong Studio |
|---|---|---|
| 1 | Alturayeif, Ahmad, Hassine. *TraceLLM*, Requirements Engineering, 2026. Quy trình đánh giá liên kết trace với cách chia dữ liệu và thiết kế prompt. | G1/G2/G10, dùng làm khung đánh giá link ứng viên, giữ human review và không chuyển số liệu trong bài sang task của Studio. |
| 2 | Bachmann và cộng sự. *Deriving Architectural Tactics*, CMU/SEI-2003-TR-004. Làm rõ quality scenario và chiến thuật kiến trúc. | G5, biến nhãn ISO thành kịch bản có điều kiện và phép đo. |
| 3 | Cortellessa, Di Pompeo, Stoico, Tucci. *Many-Objective Optimization of Non-Functional Attributes based on Refactoring of Software Models*, IST 157, 2023. Tối ưu nhiều mục tiêu có mô hình đánh giá chất lượng và chi phí thay đổi. | G5/G9, định nghĩa objectives và baselines trước khi chọn thuật toán tìm kiếm lớn. |
| 4 | Bertsimas, Sim. *The Price of Robustness*, Operations Research 52(1), 2004. Điều chỉnh mức bảo thủ dưới bất định dữ liệu tối ưu. | G4, thử các kịch bản nhỏ đã được review và đo độ ổn định phương án. |
| 5 | Liffiton và cộng sự. *Fast, Flexible MUS Enumeration*. Phân tích các tập xung đột và tập sửa. | G7, phân biệt tập sửa tối thiểu theo bao hàm với phương án sửa có chi phí nhỏ nhất. |
| 6 | Curto, Semini, Marques-Neto. *Evaluating multi-LLM pipelines for early-stage software requirements elicitation*, EMSE, 2026. Thực nghiệm có đánh giá từ con người và giới hạn về khả năng quy nguyên nhân. | G10, thêm ablation theo từng thay đổi và giữ cấu hình chấm cố định. |

Các nguồn bổ sung theo mục tiêu gồm [ADD 3.0 của Cervantes và Kazman](https://www.sei.cmu.edu/library/add-30-rethinking-drivers-and-decisions-in-the-design-process/) cho driver và quyết định thiết kế, cùng [Bailis và cộng sự, *Coordination Avoidance in Database Systems*](https://www.vldb.org/pvldb/vol8/p185-bailis.pdf) cho việc phân tích bất biến khi muốn giảm điều phối qua boundary. Các bước triển khai trong báo cáo là suy luận thiết kế cho repo dựa trên các nguồn đã đọc.
