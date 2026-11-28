# Theo dõi hoàn thiện Quantum Studio

Mục tiêu đang thực hiện là hoàn thiện dự án theo mười gap trong [báo cáo ngày 26/11/2026](STUDIO_GAP_ANALYSIS_2026-11-26.md), với trích dẫn gắn đúng phạm vi phương pháp. Các mốc triển khai dưới đây phục vụ cùng một mục tiêu.

[Bảng nguồn nghiên cứu](STUDIO_SOURCE_LEDGER.md) đối chiếu metadata và tách đóng góp của bài báo khỏi thiết kế, test và giới hạn của Studio. Citation Curto theo năm tập báo 2027, với ngày xuất bản online 03/11/2026.

Chốt báo cáo ngày **28/11/2026**: mã A4 `9ad6f30fdbca9c109c9027b5370dcb5a21122b79` đã push trên `feat/quantum-tradeoff-workbench`, [CI 46166111497](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/46166111497) thành công; 307 tests cục bộ qua. D2 hỗ trợ 9–50 component; X1 có source-only/gate đánh giá DIRECT @2; A4 thêm SENTENCE @3 cùng ba run thật/15 draft, không auto-approve. [Đánh giá output Ollama](STUDIO_LLM_OUTPUT_EVALUATION.md) giữ snapshot @1/@2 chín run/19 proposal riêng với @3 và 37 probe thăm dò. Remote main `3471eff9bbf33c407bd33ef451579499bc35be4b` do PR #1 đã merge phần trước; mốc A4 chỉ push feature, tag P0 giữ nguyên. G2/G10 chưa có xác nhận ngữ nghĩa độc lập; G5/G8 chưa có chất lượng nghiệp vụ/vận hành được đo.

| Gap | Tiến độ triển khai | Điều kiện còn cần kiểm chứng |
|---|---|---|
| G1 · Ollama theo input hiện tại | Adapter gọi thật cho ISO/component, tương tác và bắt buộc tách. Có request, raw response, metadata và proposal chờ review. UI đã chạy requirement mới, sửa đề xuất và tái tính kết quả. | Còn mở rộng kiểm thử lỗi provider và phạm vi semantics ở G2. |
| G2 · Ngữ nghĩa và mệnh đề | Giữ DIRECT @2; thêm SENTENCE @3 theo claim→frame, quote/span tra nguồn, lineage và review riêng. Giữ các claim mâu thuẫn; không dùng model tự chấm làm oracle. | Ba run @3 thật: 15 draft, 9 có issue; draft không issue vẫn sai condition. Đã lấy thêm nghĩa vụ OC-03/08 từng thiếu nhưng đây là dữ liệu phát triển. Cần reference/held-out; không có semantic accuracy. |
| G3 · Mục tiêu trùng | Review chọn NFR gốc qua `duplicate_of`, ghi rationale và checkpoint. Scoring dùng một mục tiêu, giữ tất cả source IDs. Có kiểm paraphrase bất biến điểm, mục tiêu khác scope độc lập và sửa nguồn yêu cầu review lại. | Tính tương đương ngữ nghĩa do reviewer quyết định. Chưa có bộ nhãn độc lập đánh giá quyết định hợp nhất. |
| G4 · UNKNOWN và điều kiện | Khoảng chi phí theo mode, độ phủ khai báo, review hai đến bốn điều kiện; ≤8 chọn min biên trên trên toàn bộ tập khả thi, 9–50 dùng CP-SAT cùng objective và báo phạm vi proof. Nguồn điều kiện đổi làm bằng chứng hết hiệu lực. | Tập mode là giả thuyết do reviewer khai báo. Chưa có xác suất, tương quan mode hay bằng chứng vận hành xác nhận tập điều kiện đầy đủ. |
| G5 · NFR và phép đo | Scenario sáu phần có review, scope ISO đưa vào optimizer và hai adapter bound có điều kiện cho phản hồi/khôi phục. Profile theo candidate, target, provenance và đóng góp thời gian. | Chưa đo vận hành; các bound là giả định. Thứ hạng năm trục chưa dùng target số như objective riêng. Mô hình ngoài đường đi tuần tự/restart toàn Quantum còn chưa hỗ trợ. |
| G6 · Revision và tải lại | Checkpoint chứa input, proposal, quyết định trước–sau, rationale và view. Allocation/điều kiện, quan hệ, scenario, contract/ownership gắn nguồn/revision. Contract kiểm mọi nguồn, claim và kho liên quan. Căn cứ quan hệ/hợp đồng cũ chặn bộ giải, giữ hard rules. v2 đọc v1 không sửa file cũ. | Chưa xác thực danh tính reviewer bằng tài khoản. |
| G7 · Policy sửa hard constraint | Bảo vệ từng quy tắc, chi phí sửa, lọc/xếp MCS theo policy, xem trước và áp dụng qua revision. Chặn sửa quy tắc bảo vệ từ canvas/model review/restore. Lưu riêng bản input bị chặn. | Chi phí và quyết định bảo vệ do reviewer khai báo, chưa có mô hình chi phí nghiệp vụ thực nghiệm hoặc xác thực danh tính reviewer. |
| G8 · Bằng chứng boundary | Review hợp đồng lỗi và ownership, hồ sơ theo candidate; hai tiến trình HTTP/SQLite chạy giao thức mẫu có mất ACK, timeout, retry, restart và chống trùng. | Prototype chỉ thực thi APPLY_EVENT chuẩn bị sẵn. Nghiệp vụ Ticket/Tutor, invariant thật, broker, build/deploy, tải và migration vẫn chưa được kiểm chứng; deployability NOT_VERIFIED. |
| G9 · Backend lớn | ≤8 giữ enumerator; 9–50 dispatch CP-SAT riêng bảo toàn năm trục, mode bounds, hard rules và protected repair. Đối chiếu toàn bộ nghiệm/vector ở bộ nhỏ và benchmark hai họ tổng hợp. UI phân biệt tập đã tìm, proof và timeout. | Pareto cỡ lớn chưa liệt kê toàn cục; runtime phụ thuộc input/phần cứng. Benchmark tổng hợp chưa chứng minh khả năng khái quát ngữ nghĩa hoặc chất lượng nghiệp vụ. |
| G10 · Đánh giá độc lập | Protocol Studio @1 freeze source/request/prompt/code/model và document split; source-only worksheet, hai annotation lock và adjudication trước inference. Scorer exact atomic links có raw/gate cohorts, regex QUALITY baseline, repetitions và null denominator. Hai document mới, 16 requirement/40 unit, chưa có đáp án. | Chưa có independent reference hoặc inference trên bộ mới; source do agent chuẩn bị. Chưa đánh giá human-reviewed cohort, thời gian review, downstream partition agreement hoặc full entailment. [Protocol và giới hạn](STUDIO_EVALUATION_PROTOCOL.md). |

## Mốc A — đầu vào thật, đề xuất và quyết định có lịch sử

**Cập nhật A4 — 28/11/2026:** [SENTENCE @3 và đánh giá output thực tế](STUDIO_SENTENCE_EXTRACTION.md) có 307 tests qua (17 mới), ba lượt qwen thật, 15 draft/18 calls và checkpoint `checkpoint-8662045b5ca04d82975a36cf284de535`. Không approve/correct, đầu vào optimizer giữ nguyên 37 nghiệm. Quote tra từ nguồn là biến đổi xác định, claim/frame là LLM_PROPOSAL; hai stage không phải xác nhận độc lập. Giữ 37 probe thăm dò và các lỗi còn lại trong báo cáo. G10 @1 chỉ hỗ trợ DIRECT @2; freeze cũ giữ nguyên nhưng code hash không khớp sau thay đổi này, cần version freeze mới trước thí nghiệm tương lai. G2/G10 và measurement G5/G8 vẫn mở.

- Giao diện **Phân tích yêu cầu hiện tại bằng Ollama** nhận tối đa tám requirement mỗi lần. Người dùng chọn tác vụ ISO/component, tương tác hoặc bắt buộc tách. Ba tác vụ có schema và hướng dẫn riêng. Model chạy qua client Ollama đã cấu hình trong repo.
- Input chưa duyệt giữ nguyên optimizer. Mỗi đề xuất có mã, source hash, catalog hash, quote, vấn đề cấu trúc và trạng thái. Người review có thể approve, correct, reject hoặc defer, với người thực hiện và rationale do phiên khai báo.
- Chỉ quyết định áp dụng được kiểm lại mới tạo allocation, sửa cạnh hoặc thêm quy tắc tách. Metadata không xác nhận danh tính người vận hành bằng cơ chế đăng nhập. Chữ trong nguồn và ý nghĩa của câu vẫn cần reviewer kiểm tra.
- Checkpoint dùng ID duy nhất, lưu parent cùng mô hình trước–sau và proposal. Có đường tải lại mô hình, trọng số, chế độ xếp hạng và bố cục. Nội dung hoặc scope requirement thay đổi làm allocation cũ bị xóa khỏi input hiện hành và proposal cũ thành `STALE`. Bản checkpoint cũ được giữ.
- Xác nhận ISO thủ công cũng có checkpoint. Quote rỗng cần rationale bổ sung. Đây là đường ghi quyết định kiến trúc của người vận hành khi văn bản nguồn chưa diễn đạt đủ.

## Nguồn và giới hạn áp dụng

| Nguồn | Phần được áp dụng | Phần cần được kiểm chứng riêng trong dự án |
|---|---|---|
| [Alturayeif, Ahmad và Hassine, TraceLLM, Requirements Engineering, 2026](https://doi.org/10.1007/s00766-026-00460-1) | Đề xuất link ứng viên theo ngữ cảnh và review, giữ cấu hình/nguồn để tái lập. | Prompt Studio, nhãn ISO và scope component là task riêng, cần tập đánh giá mới. Các điểm số trong bài không được dùng làm kết quả dự án. |
| [Femmer và cộng sự, Rapid Quality Assurance with Requirements Smells, JSS 123, 2017](https://wwwbroy.in.tum.de/~femmer/works/2016-requirements_smells-jss.pdf) | Hướng bổ sung cảnh báo nguồn có dấu hiệu cần đọc kỹ để hỗ trợ review. | Kiểm phủ định và mệnh đề tiếng Việt, lỗi báo nhầm và bỏ sót còn ở phần việc G2. |
| [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs) | Cung cấp schema JSON qua `format` và kiểm tra lại dữ liệu trả về. | Schema bảo đảm hình dạng, còn quote/ID và diễn giải được kiểm ở các bước riêng. |
| [Streamlit Session State](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state) | Tải giá trị widget trong callback trước khi rerender phiên. | Checkpoint bền vững là thiết kế của repo, dùng lưu trữ local bên ngoài WebSocket session. |
| [Barr, Harman, McMinn, Shahbaz và Yoo, The Oracle Problem in Software Testing: A Survey, IEEE TSE 41(5), 2015, 507–525](https://discovery.ucl.ac.uk/id/eprint/1471263/1/06963470.pdf) | Kiểm quan hệ bất biến của chi phí sau một phép biến đổi đầu vào được định nghĩa trước. | Quan hệ `duplicate_of` và chính sách một mục tiêu là thiết kế của Studio. Test tổng hợp không xác nhận hai câu thực tế tương đương ngữ nghĩa. |

## Mốc B1 — danh tính mục tiêu chất lượng

`Review yêu cầu cùng mục tiêu` cho reviewer chọn NFR cần đối chiếu và NFR gốc đã có ánh xạ. Quyết định cần actor và rationale, tạo checkpoint `QUALITY_TARGET_MERGE`. Ánh xạ cũ của nguồn hợp nhất bị gỡ, mục tiêu dùng characteristic và component của bản gốc. Reviewer cần đối chiếu cả điều kiện tải, ngưỡng, actor và scope trước khi chọn. Mô hình không tự gộp theo sự giống nhau của văn bản.

Ví dụ tổng hợp trong `tests/test_studio_quality_targets.py` xác nhận Security cho Customer Profile ở NFR-03, rồi thêm DUP có cùng scope. Hai mục tiêu riêng làm tăng chi phí. Sau review hợp nhất DUP vào NFR-03, toàn bộ kết quả `Analysis` trùng trường hợp chỉ có NFR-03. Hồ sơ vẫn giữ `[NFR-03, DUP]` dưới nhãn `Security · NFR-03`, nên cả hai requirement truy vết tới component và Quantum. Mục tiêu có scope REPORT giữ nhãn riêng cho tới khi có quyết định review.

Tách mục tiêu tạo `QUALITY_TARGET_UNLINK` và yêu cầu xác nhận ánh xạ mới. Sửa nội dung hoặc scope của nguồn gốc/nguồn hợp nhất làm mất hiệu lực quan hệ liên quan. Validator chặn vòng lặp, liên kết thiếu, liên kết qua nhiều tầng và allocation riêng trên nguồn hợp nhất. Hợp nhất một bản gốc vào bản gốc khác chuyển các nguồn phụ thuộc cùng sang đích mới trong một revision. Đây là chính sách kiến trúc và biến đổi xác định được ghi nhận qua Human Review, chưa phải kết quả phân loại tự động của LLM.

Kiểm chứng mốc B1 đạt **168 tests**, bao gồm sáu test mới về scoring, scope độc lập, invalidation, liên kết hợp lệ và đường bấm review/lưu phiên. `compileall` hoàn tất. Không có lần inference mới phục vụ mốc hợp nhất.

## Mốc B2 — bất định của mode tương tác

Với phân hoạch cố định `P`, gọi `J_known(P)` là điểm năm trục hiện có, trong đó chỉ cạnh đã xác định SYNC/ASYNC góp chi phí mode. Đặt `M_e={SYNC,ASYNC}` cho cạnh UNKNOWN chưa có điều kiện được review. Nếu có tập điều kiện còn khớp source hash và quote, `M_e` là các mode trong tập đó. Với mỗi cạnh UNKNOWN, đóng góp giả thuyết là:

```text
c(P,e,m) = weight_e × [lambda_sync × I(m=SYNC và khác Quantum)
                      + lambda_async × I(m=ASYNC và cùng Quantum)]
L(P) = J_known(P) + sum_e min_{m thuộc M_e} c(P,e,m)
U(P) = J_known(P) + sum_e max_{m thuộc M_e} c(P,e,m)
```

Hai đầu mút chính xác cho một phân hoạch trong mô hình cho phép các mode trên mỗi cạnh thay đổi độc lập. Không gán xác suất cho SYNC/ASYNC. Các hard constraints được giữ nguyên. Khoảng có thể bảo thủ nếu các điều kiện giữa nhiều cạnh có tương quan mà mô hình chưa biểu diễn. Nếu tập mode giả định bỏ sót hành vi thật, khoảng cũng chưa bao phủ hành vi đó.

Giao diện hiển thị `[L,U]` trên thẻ và trong bảng. `Ưu tiên chi phí biên trên khi còn bất định` chọn `argmin U(P)` trên **mọi phân hoạch thỏa hard constraints**, với tie-break theo L, số Quantum và ID. Cách này tránh bỏ lỡ một phương án vốn bị trội khi chỉ xét chi phí mode đã rõ. Nhãn Pareto và ma trận năm trục vẫn mô tả chi phí đã xác định. Khi tắt lựa chọn biên trên, ba chế độ xếp hạng cũ dùng chi phí mode đã rõ, cùng cảnh báo và khoảng điểm để reviewer đánh giá phần chưa biết. Hồ sơ chọn phương án ghi chính sách xếp hạng và các khoảng tương ứng.

`Review tương tác theo điều kiện` nhận hai đến bốn nhánh. Mỗi nhánh có tên điều kiện, mode, requirement nguồn và quote nguyên văn. Quyết định có actor/rationale, source hash và checkpoint trước–sau. Chỉ áp dụng trên cạnh không có giao dịch cục bộ bắt buộc. Nguồn sửa làm tập điều kiện mất hiệu lực và quay về hai giả thuyết UNKNOWN. Reviewer có trách nhiệm xác nhận phạm vi bao phủ, tính loại trừ của các nhánh và quan hệ phụ thuộc giữa chúng. Độ phủ hiển thị là số cạnh có mode hoặc tập điều kiện còn hiệu lực trên tổng số cạnh, không phải semantic accuracy.

[Bertsimas và Sim, *The Price of Robustness*, Operations Research 52(1), 2004, 35–53, DOI 10.1287/opre.1030.0065](https://www.mit.edu/~dbertsim/papers/Robust%20Optimization/The%20price%20of%20Robustness.pdf) nghiên cứu tối ưu dưới dữ liệu bất định và mức bảo thủ. Studio dùng tập mode rời rạc và minimax theo biên trên như thiết kế riêng. Chưa triển khai mô hình bất định có ngân sách Γ của bài, nên chưa có bảo đảm xác suất hay kết quả tối ưu của bài chuyển trực tiếp sang dự án.

Kiểm định xác định trong `tests/test_studio_uncertainty.py` liệt kê đủ bốn tổ hợp của hai cạnh UNKNOWN, đối chiếu min/max với L/U cho từng phân hoạch. Test khác chứng minh phương án minimax có thể nằm ngoài biên Pareto của chi phí đã biết. Có test giữ hard rule, từ chối quote sai, giữ giao dịch cục bộ, invalidation khi sửa nguồn và đường bấm review/lưu hồ sơ trên UI. Đây là ca do dự án tạo cho kiểm thử thuật toán.

Regression mốc B2 đạt **174 tests**. `compileall` và kiểm cú pháp JavaScript qua. Browser 8501 nạp OC-09 ở chế độ oracle tổng hợp, hiện P031 `5–7`, P011 `6–8`, P029 `7–9`. Bật xếp theo biên trên vẫn chọn P031 vì biên trên 7 thấp nhất trong 37 nghiệm. Đây là kết quả giữ nguyên có lý do theo mô hình đã khai báo, không phải đề xuất mới của Ollama. Lượt browser không ghi Human Review cho dữ liệu oracle và đã quay lại sơ đồ người dùng.

## Mốc D1 — chính sách và quyết định sửa ràng buộc

Mỗi quy tắc có `review_policy.protected` và `change_cost` dương từ 1–1000, mặc định false/1 để giữ hành vi input cũ. Các quy tắc vẫn là hard constraints trong mô hình đang phân tích. Chi phí sửa chỉ dùng xếp hạng thay đổi được đề nghị, tách riêng với năm trục chi phí kiến trúc.

`minimal_repairs` loại các tập vi phạm chứa quy tắc bảo vệ, giữ các tập sửa tối thiểu theo bao hàm rồi sắp theo tổng `change_cost`, số quy tắc và ID quy tắc. Với chi phí dương, tập thay đổi có chi phí thấp nhất luôn có thể chọn trong các tập tối thiểu. Studio tiếp tục liệt kê chính xác trong giới hạn tám component. Khi mọi cách gỡ đều đụng quy tắc bảo vệ, hệ thống giữ `INFEASIBLE` và hiện không có cách sửa được phép.

`Review chính sách ràng buộc` ghi actor/rationale và checkpoint riêng cho việc bảo vệ, bỏ bảo vệ hoặc đổi chi phí. `Áp dụng cách sửa đã review` kiểm lại tập sửa còn hiện hành, giữ các quy tắc bảo vệ, ghi danh sách quy tắc thay đổi, chi phí sửa, input trước–sau và số nghiệm sau thay đổi. Bản mô phỏng vẫn giữ riêng cho đến khi bấm áp dụng. Mô phỏng oracle không ghi quyết định vào phiên người dùng.

Canvas, quyết định model và việc tải lại checkpoint đều kiểm quy tắc bảo vệ của mô hình hiện hành. Nếu sửa sơ đồ bị chặn, người dùng có thể tải input nháp, hoặc lưu input bị chặn trong checkpoint `PROTECTED_EDIT_RETAINED` rồi quay lại review policy. Dữ liệu nháp này chưa được áp dụng vào bộ giải. Sửa policy là thao tác có người review và lý do, chưa có phân quyền hay xác thực reviewer bằng tài khoản.

Các ca tổng hợp kiểm OC-10 khi bảo vệ cả hai quy tắc, chỉ bảo vệ một quy tắc, đổi chi phí và thay đổi thật sau review. Chi phí tách bằng 100 và chi phí đổi giao dịch bằng 2 đưa cách đổi giao dịch lên trước. Giữ giao dịch được bảo vệ chỉ cho phép sửa quy tắc tách, cho 10 nghiệm. Giữ quy tắc tách được bảo vệ chỉ cho phép sửa giao dịch, cho 27 nghiệm. Bảo vệ cả hai giữ 0 nghiệm và không có MCS được phép. Các con số thuộc ca oracle đã chuẩn bị, không phải nhãn hoặc chính sách do LLM tạo.

Mốc D1 đạt **182 tests**, `compileall`, kiểm cú pháp JavaScript và staged diff. Bảy test mới gồm API và AppTest cho bảo vệ hai phía, chi phí ưu tiên, proposal không được sửa giao dịch bảo vệ, bản nháp bị chặn được giữ và thao tác áp dụng ghi diff. Phần UI được kiểm thêm trên cổng 8501.

## Mốc A2 — ràng buộc nguồn theo revision của quan hệ

`EvidenceBinding` gắn cạnh và quy tắc tách đã review với source ID/hash, quote, catalog hash, claim hash, proposal/run ban đầu, actor/rationale và provenance của căn cứ/quyết định. Claim hash bao gồm hai đầu quan hệ, mode và trạng thái giao dịch; trọng số chi phí là policy riêng. Đề xuất được sửa ghi `citation_provenance=HUMAN_DECISION`. Source quote khớp và hash khớp chỉ xác nhận tính nhất quán với bản đã review.

Khi requirement bị đổi/xóa, catalog đổi hoặc claim đổi, `analyze` phát `EvidenceReviewRequired`. UI xóa các candidate đang xem và hiện **Cần review lại căn cứ nguồn**, không gán trạng thái `INFEASIBLE` cho thiếu căn cứ. Các hard constraints vẫn giữ nguyên trong mô hình, không bị tự tắt để tạo nghiệm. `Căn cứ nguồn của tương tác và quy tắc` cho reviewer chọn nguồn/quote hiện hành, kiểm nghĩa, nhập actor/rationale rồi xác nhận lại. Revision `SOURCE_EVIDENCE_RECONFIRMED` chỉ đổi căn cứ, giữ mode và quy tắc.

Checkpoint mới dùng `STUDIO-CHECKPOINT@2`. Khi đọc v1, loader chỉ khôi phục binding trong bộ nhớ nếu có bản ghi proposal đã áp dụng và nội dung quan hệ khớp chính xác. Bản gốc không bị ghi lại. Nếu không có actor tương ứng trong quyết định cũ thì giữ `UNKNOWN`. Quan hệ fixture/thủ công chưa có bản ghi áp dụng giữ không có binding. v2 không khôi phục lại proposal đã bị thay thế có chủ đích. Review điều kiện mới và mô phỏng thay đổi giao dịch ghi mô hình trước–sau và gỡ binding của claim đã được thay thế.

Tám test mới kiểm source edit vẫn giữ quote cũ, xóa source, đổi catalog/claim, rebind quy tắc bảo vệ, tương thích checkpoint v1/v2 và luồng UI bị chặn→review→tái tính. Regression đạt **190 tests**, compileall và kiểm cú pháp JavaScript qua. Đã chuyển test oracle `MY-FR` cũ sang thư mục tạm để không ghi checkpoint test vào lịch sử local. Artifact cũ được giữ và không tính làm inference thật.

### Lượt chạy Ollama và UI thực tế cho A2

Thêm FR `REQ-04` từ canvas: “Ticket Router must wait for Ticket Completion to confirm the status update before replying to the caller.” Lượt `studio-extraction-7a648ae31c004fab9cb770c4750d8964` dùng qwen3:4b, Ollama 0.40.18, cùng model digest đã ghi ở mốc A, prompt `STUDIO-EXTRACT@1`, trả 83 token. Quote đúng nguyên văn nhưng hai đầu quan hệ là `REPORT→ROUTE`. Kiểm quote/ID trả không có lỗi cấu trúc, vẫn cần reviewer phát hiện lỗi nghĩa.

Smoke kỹ thuật dùng actor `AGENT_TECHNICAL_SMOKE_TEST`, chọn CORRECT thành `ROUTE→COMPLETE`, giữ SYNC và `local_transaction=false`. Checkpoint `checkpoint-2af62c512fce42689befcc15bc109935` lưu cả đề xuất gốc, phần sửa và binding. Đây là quyết định agent để kiểm dây nối, không phải annotation stakeholder độc lập.

Sau đó thêm câu “This obligation applies during normal operation at 50 updates per minute.” vào nguồn. Dù quote cũ vẫn tồn tại, source hash đổi từ `44c193…` thành `317c3a…`. Checkpoint `checkpoint-ac669974e25d4686bc2d8a8c8bcf2f1b` ghi input sửa. UI xóa kết quả, yêu cầu review lại, còn cạnh SYNC và các hard rules giữ nguyên. Xác nhận lại bằng cùng actor kỹ thuật tạo `checkpoint-061588687e16429ca1ecead3dd0bf79d` và tái tạo 37 nghiệm, P011/6 điểm theo SYNC_FIRST.

Kết quả phân nhóm trước/sau xác nhận căn cứ giữ nguyên vì topology, mode, scope đặc tính và trọng số không đổi. Điều kiện 50 updates/minute chưa đi vào mô hình dự đoán hiệu năng; mục tiêu G5 còn phải triển khai. Không báo semantic accuracy hoặc quality PASS cho lượt thử. Sau kiểm tra đã nạp lại input Ticket Support ban đầu; request/response/checkpoints giữ local, không đưa vào Git.

[Liffiton, Previti, Malik và Marques-Silva, *Fast, Flexible MUS Enumeration*, DOI 10.1007/s10601-015-9183-0](https://markliffiton.com/publications/constraints_liffiton_marco.pdf) cung cấp khái niệm MUS/MCS và thuật toán MARCO. [Ansótegui, Bonet và Levy, *A New Algorithm for Weighted Partial MaxSAT*, AAAI 2010](https://cdn.aaai.org/ojs/7545/7545-13-11075-1-2-20201228.pdf) phân biệt mệnh đề bắt buộc với mệnh đề có chi phí vi phạm. Studio dùng ý tưởng bảo vệ và chi phí sửa, triển khai bằng tập vi phạm của phân hoạch. Chưa triển khai MARCO hoặc solver WPM2 của hai bài, nên không nhận các kết quả benchmark của chúng làm kết quả Studio.

## Bằng chứng chạy ngày 26/11/2026 cho mốc A

Ollama `0.40.18` với `qwen3:4b`, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`. Ba lời gọi qua adapter đã lưu dưới `runs/quantum-studio/extractions/`. Trong yêu cầu ISO cho OC-02/OC-03, model tạo một ánh xạ quote đúng và một quote lệch nguồn. Lượt tương tác OC-08/OC-10 trả cạnh ASYNC của OC-08, còn quote của OC-10 bị sửa lệch. Lượt tách cho OC-10 chọn đúng hai component nhưng dùng đoạn nói về giao dịch cục bộ, nên reviewer vẫn phải kiểm nghĩa của căn cứ.

Thử thêm `REQ-04` trực tiếp từ UI với nội dung “Khi khách hàng đăng nhập và gửi yêu cầu ở tải 300 lượt mỗi phút, luồng Customer Login và Ticket Creation phải trả mã tiếp nhận trong vòng 900 ms ở p95.” Lời gọi `studio-extraction-0ac9899209d24dad8f6f33fedf82b90b` trả 108 token, đề xuất Reliability cho LOGIN/CREATE và quote chứa `90:00 ms`. Kiểm tra chuỗi con phát hiện quote không khớp và chặn áp dụng bản gốc.

Lượt kiểm thử kỹ thuật dùng actor `AGENT_TECHNICAL_SMOKE_TEST`, chọn `CORRECT`, đổi sang Performance efficiency và quote nguyên văn `phải trả mã tiếp nhận trong vòng 900 ms ở p95`. Với xếp hạng theo trọng số mặc định, P031 có 5 điểm trước áp dụng. Sau áp dụng, P011 đứng đầu với 8 điểm. P031 chấm trên đầu vào mới có 11 điểm. Checkpoint `checkpoint-7e212d4b009645dc91b662c3e827e56c` ghi source hash, run ID, rationale và input trước–sau. Đây là bằng chứng kỹ thuật về truyền dữ liệu qua review, với nhãn độc lập và đánh giá chất lượng còn phải thực hiện theo G10.

Sau khi khởi động lại Streamlit, chọn checkpoint này trong lịch sử đã tái tạo P011/8 điểm và nhãn `Performance efficiency · REQ-04` trên sơ đồ. Regression suite tại mốc này đạt **162 tests**. Các phép test giả lập provider dùng dữ liệu ghi rõ `TEST_ONLY` và lưu dưới thư mục tạm của pytest.

## Mốc C1 — scenario sáu phần và profile dự đoán

Mốc này dùng schema `Scenario` hiện có, bổ sung scope, đường đi, target, timing assumptions và quyết định review. Có adapter phản hồi tuần tự và khôi phục tuần tự toàn Quantum. Toàn bộ đầu vào, công thức, điều kiện và giới hạn nằm trong [mô tả C1](STUDIO_QUALITY_SCENARIOS.md). Ô chưa biết, source/catalog cũ, mode nhiều giả thuyết, target không khớp, metric chưa hỗ trợ hoặc bound thiếu đều giữ `INSUFFICIENT_EVIDENCE`, không tự tạo số dự đoán.

Khi bật gán scope, scenario được xác nhận cập nhật characteristic trên component và optimizer tính lại. Profile sau đó tiêu thụ phân hoạch, mode và giả định để đối chiếu bound với target. Các số target hiện ảnh hưởng đối chiếu profile; năm trục điểm thiết kế vẫn giữ công thức cũ. Biên Pareto trong UI chỉ nói về năm trục đó. Measurement luôn `NOT_MEASURED` khi chưa có observation.

Đã kiểm trực tiếp trên 8501 với hai NFR **PREPARED_FIXTURE**:

1. `REQ-04`: Customer sends a ticket during peak load. Ticket Creation waits for Ticket Router and must acknowledge within 900 ms. Scenario `QC-UI`, scope CREATE/ROUTE, đường đi CREATE→ROUTE, SYNC. Bound CREATE=250, ROUTE=350, RTT=400 ms.
2. `REQ-05`: Monitor notices a stopped router process under normal processing load. Ticket Router must restore service within 10 min. This is the recoverability target. Scenario `QC-REC-UI`, scope/đầu mối ROUTE. Bound recovery CREATE=250.000, ROUTE=COMPLETE=200.000, LOGIN=PROFILE=REPORT=50.000, detection=5.000 ms.

Actor `AGENT_TECHNICAL_SMOKE_TEST` và cả provenance của quyết định lẫn timing đều được chọn `PREPARED_FIXTURE`. Đây là phép thử UI và tính toán, không phải output Ollama hay annotation stakeholder. Checkpoint `checkpoint-37bed3b1cdb04b78a6361b03c8ceb7a3` lưu QC-UI; `checkpoint-d39e405292d44e84808f754f487bd139` lưu cả hai scenario.

| Phương án | Điểm thiết kế với trọng số mặc định | Bound phản hồi / target | Bound khôi phục / target |
|---|---:|---|---|
| P031 | 8 | 600 / 900 ms | 655.000 / 600.000 ms |
| P011 | 17 | 1.000 / 900 ms | 405.000 / 600.000 ms |

Chọn P011 cho slot C rồi chọn radio C đã vẽ đúng P011, chuyển Performance efficiency·REQ-04 sang Q1/Q2, giữ Reliability·REQ-05 ở Q2 và cập nhật cả hai profile. P011 nằm ngoài Pareto năm trục thiết kế nhưng có recovery bound nhỏ hơn P031 theo giả định này. Không gán quality PASS cho phương án nào. Dữ liệu chạy và ảnh kiểm tra giữ local.

Regression C1 đạt **208 tests**, trong đó 18 test mới về công thức, UNKNOWN, số/đơn vị, hai mốc ACK/completion, scope/context, khôi phục, review/lưu/gỡ scenario, overflow và provenance fixture. Compileall, JavaScript syntax và diff check qua. Khổ browser 400 px không tràn ngang toàn trang. Input mẫu ban đầu được khôi phục sau phép thử; hai checkpoint scenario vẫn giữ local để tải lại.

## Mốc C2 — hợp đồng boundary và thực thi giao thức mẫu

Review hợp đồng và ownership đã nối vào Studio, checkpoint và JSON so sánh của từng candidate. Contract nháp không đổi bộ giải; bản duyệt cập nhật mode, giữ hard constraints và policy bảo vệ. Mọi nguồn/span/hash, claim, component catalog và kho liên quan đều được kiểm lại. Review một binding đơn không bỏ qua được contract nhiều nguồn bị cũ. Ownership có writer, invariant, consistency, partition key khi cần và lag khai báo; profile chưa coi invariant là đã chứng minh.

`OUTBOX_INBOX_V1` là **PREPARED_FIXTURE**, không phải nội dung sinh bởi LLM. Hai tiến trình thật dùng HTTP loopback và hai file SQLite riêng. Giao thức kiểm operation tổng hợp APPLY_EVENT, lưu command/outbox cùng transaction và giữ event ID/payload cùng effect ở receiver. Mỗi invocation thử tối đa ba lần, timeout 300 ms mỗi attempt. Relay được kích hoạt thủ công, chưa có broker hoặc liveness guarantee.

Trên UI 8501, actor `AGENT_TECHNICAL_SMOKE_TEST` chọn nguồn quyết định `PREPARED_FIXTURE`, nguồn REQ-01/REQ-02 và duyệt ASYNC cho CREATE→ROUTE. Checkpoint **checkpoint-ed282c1e82bd4018ad221d39f9c1cf76** giữ quyết định. ASYNC đã có trong input mẫu nên duyệt lại giao thức không đổi vector/partition; phép kiểm xác định riêng đổi sang SYNC xác nhận chi phí downstream thay đổi và hard rules giữ nguyên.

Phương án B/P011 có ranh giới Q1→Q2. Nút chạy trên UI tạo **probe-75a268797a694ffa9361d0bb3c857018**, status `PROTOTYPE_CONTRACT_CHECK_PASSED`, 9/9 assertion đạt: receiver unavailable, giới hạn retry, restart producer, mất ACK sau commit, duplicate/conflicting payload, restart receiver, timeout sau commit, version sai và outbox hết pending. Bốn PID được ghi và đã dừng; kiểm lại hệ điều hành không còn các PID đó. Đổi sang C/P009 khiến bằng chứng cũ hiện `STALE`. Không có `quality PASS`, semantic metric hoặc inference mới trong mốc này.

Tests mới cũng chạy lịch lỗi thật cho cả SYNC và ASYNC trong thư mục tạm, cùng nhánh báo cáo lỗi/dọn worker và AppTest review hợp đồng/ownership→checkpoint→boundary profiles. Tổng suite hiện **218 tests**; compileall và JavaScript syntax qua. Browser không có exception và khổ 400 px không tràn ngang toàn trang. Runs/ảnh giữ local, không stage.

Điều kiện G8 có đường thực thi và kiểm lỗi cho một giao thức boundary tham chiếu. Các phần nghiệp vụ thật, ownership/invariant chứng minh, build/deploy, schema migration, multi-writer và measurement vận hành vẫn chưa được xác nhận. [Cách sử dụng, tái lập và phạm vi nguồn nghiên cứu](STUDIO_BOUNDARY_EVIDENCE.md).

## Mốc A3 — review mệnh đề, phủ định và vai trò component

`STUDIO-EXTRACT@2` yêu cầu frame có chủ thể, hành vi, đối tượng, điều kiện, modality, role IDs, loại nghĩa và effect. `OUT_OF_SCOPE` có mapping hoạt động, quote/role không khớp, EXEMPTION thành nghĩa vụ, cấm tách thành bắt buộc tách, lẫn mệnh đề và duplicate payload bị giữ lại. Bổ sung ngoài nguồn cần CORRECT + human_fields + rationale. UI có cách tạo draft do reviewer bổ sung nếu model bỏ sót, không ghi công này cho LLM.

Hai lượt qwen3:4b thật trên các OC đã biết được giữ raw. Batch OC-02/03/07/12 trả bốn proposal OUT_OF_SCOPE có allocation; không proposal nào vào optimizer. OC-03 còn thiếu target khôi phục riêng. Lượt OC-02 riêng có lỗi quote/frame và vẫn bị giữ. Guard lẫn mệnh đề được thêm sau khi đọc lỗi phát triển; hai batch khác nhau không phải ablation hay held-out. Không có semantic accuracy hoặc nhãn độc lập mới.

UI 8501 đã CORRECT proposal thật của DEV-OC-12 trong checkpoint `checkpoint-07b06b4948c64e1f9afc35582d10888f`: Reliability→COMPLETE, REPORT chỉ là điều kiện lỗi. P011 giữ thứ hạng, điểm 6→8 do mix tăng; P031 5→7, hard rules và 37 nghiệm giữ nguyên. Source→proposal→correction fixture→component→Q2 hiển thị đúng. Decision fixture của agent không phải human/expert label độc lập.

Regression hiện **241 tests**, thêm 23 trường hợp về clause guard, OC-02/03/07/12, prohibition, alias, hai target, nguồn/catalog/scope cũ, mode/effect có điều kiện, duplicate, lẫn câu, reviewer bổ sung và đường UI/checkpoint. Proposal chưa duyệt, từ chối hoặc defer giữ nguyên optimizer; outcome này được kiểm độc lập với khả năng model hiểu câu. Khổ browser 400 px không tràn ngang toàn trang; input mẫu được khôi phục sau smoke, checkpoint review giữ local. [Schema, policy, nguồn nghiên cứu, các lượt lỗi và hướng dẫn](STUDIO_CLAUSE_REVIEW.md).

## Mốc D2 — backend Studio 9–50 component

Adapter CP-SAT mới mã hóa đúng năm chi phí, hard closure, canonical target và biên UNKNOWN của Studio. Bộ liệt kê ≤8 giữ ID/Pareto và hành vi cũ. Cỡ lớn có thời hạn, seed hợp lệ, nhiều objective để tạo lựa chọn và kiểm lại từng vector bằng Python. Bộ sửa xung đột lớn tìm tối đa ba MCS có protected policy, không đếm Bell(n), không tự áp dụng. JSON giữ tổng số nghiệm/Pareto toàn cục là null, tách số đã tìm và phạm vi chứng minh.

**264 tests** qua, gồm 23 tests mới về tập phân hoạch/vector/L/U tương đương ở bộ nhỏ, Bell(9), ba ranking, trọng số 0, timeout UNKNOWN, min-cost repair và UI/checkpoint cỡ lớn. Compileall, JavaScript syntax và diff check qua. Benchmark tám fixture ở cỡ 9/12/20/50 đều giữ hard rules; pressure 20/50 mới FEASIBLE, chưa tối ưu được chứng minh. Đây là fixture do repo chuẩn bị, không phải LLM hoặc expert annotation.

Browser 8501 chạy ca pressure 50: A/B/C lần lượt 3/2/4 Quantum với điểm 84/89/153, chọn C vẽ đúng và hiện scope characteristics theo target. Không có nút ngoài vùng vẽ hoặc exception ứng dụng; khổ 400 px không tràn ngang toàn trang. [Công thức, raw-run ID, bảng benchmark, nguồn S19/S20 và giới hạn](STUDIO_LARGE_BACKEND.md).

## Mốc X1 — nguồn mới và gate đánh giá extraction

`STUDIO-EVALUATION@1` freeze source/document split, exact request/prompt/schema/code/model và repetitions. Hai annotation source-only khóa riêng rồi adjudication trước inference. Reference chưa có thì cả runner lẫn scorer bị chặn, không lấy correction của agent hoặc oracle làm nhãn. Bộ nguồn Equipment Loan/Room Scheduling có 16 requirement và 40 unit; chưa có inference hoặc independent labels.

Scorer định nghĩa exact atomic link theo condition/source/task, tách raw projectable fields khỏi gate-eligible fields, invalid rows, abstentions, false-hard-policy fields và units bị loại. Có baseline lexical cho QUALITY; hai task regex khác ghi chưa hỗ trợ. Mỗi repetition/query cần response riêng và đủ calls đã chốt. Lỗi provider giữ status cùng extraction ID/raw manifest. Scorer không auto-approve hoặc sửa đầu vào optimizer.

Regression **290 tests** qua, gồm 26 tests mới về source-only/freeze/exposure, annotation/adjudication, tampering, model digest, UNKNOWN, null denominator, response reuse, provider failure và luồng đủ ba tác vụ bằng response/attestation mô phỏng. Compileall, JavaScript syntax và diff check qua. Số tests không thay semantic accuracy; các source/reference test chỉ ở thư mục tạm. [Protocol, lệnh chạy, matcher và giới hạn](STUDIO_EVALUATION_PROTOCOL.md).

Gói thực đã freeze tại `runs/quantum-studio/studies/studio-source-only-v1-20261128/`, có 40 row trắng và sáu request đã chốt. Preflight không có reference ghi 0 provider contact, không tăng số bảy extraction request đang có và giữ metric null. Chưa có annotation hoặc adjudication hợp lệ; gate này chưa phải kết quả ngữ nghĩa mới.

### Bổ sung kiểm thật G1/G2 sau X1

Hai call @2 trên OC-08/OC-10 đã biết, không dùng source held-out mới, bổ sung năm proposal INTERACTION và hai SEPARATION. Cả bảy quote khớp nhưng đều có blocker: endpoint không khớp frame/source, modality chứa nhãn thay vì từ nguồn, disposition mâu thuẫn hoặc text field rỗng/sai. Giữ REVIEW_REQUIRED, không approve, đầu vào optimizer và 37 nghiệm giữ nguyên. Tổng inventory phát triển hiện chín run/19 proposal; chưa có semantic metrics. [Bằng chứng R8/R9 và checkpoint chờ review](STUDIO_LLM_OUTPUT_EVALUATION.md#cập-nhật-r8r9--interaction-và-separation-prompt-2).
