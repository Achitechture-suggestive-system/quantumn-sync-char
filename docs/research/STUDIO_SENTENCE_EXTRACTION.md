# Trích xuất theo câu — claim và frame vẫn cần Human Review

## Thay đổi và phạm vi

Mã thực thi của mốc này đã được commit thành **`9ad6f30fdbca9c109c9027b5370dcb5a21122b79`**, push feature và [CI 46166111497](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/46166111497) thành công. Các hash file extraction/guard trong cả ba manifest live đã đối chiếu khớp working tree của commit này; không retune mã sau khi đọc ba output. [Nhật ký publish](../development/GITHUB_PUBLISH_LOG.md).

`SENTENCE` dùng prompt `STUDIO-EXTRACT@3` để giảm số trường model phải sinh cùng lúc. UI chọn cách này mặc định; `DIRECT` giữ prompt @2 và vẫn là mặc định API để bảo toàn protocol G10 @1. Đây là biến thể do repo thiết kế, chưa chứng minh tối ưu hoặc tốt hơn trên dữ liệu độc lập.

Luồng thực thi:

1. Chọn 1–8 requirement; QUALITY chỉ nhận NFR đã khai báo. Tách theo dấu kết câu hoặc xuống dòng, giữ dấu chấm trong `1.2` và dấu chấm phẩy. Mỗi đoạn có source ID và offset ký tự chính xác. Đây là heuristic, không phải parser mệnh đề nguyên tử.
2. LLM bước một trả claim theo unit: nhãn/owner, hướng/mode/transaction hoặc cặp tách. Có thể trả `claims=[]`. Schema xuất hiện trong cả `format` và prompt.
3. Mỗi claim có một call LLM đọc frame từ chính câu đó. Focus chỉ nêu participant và quality hint nếu có; không truyền mode/atomicity bước một để model chép lại. Frame vẫn có thể sai và hai call cùng model không độc lập.
4. Adapter tra quote/offset từ nguồn, suy role IDs từ tên nguyên văn và giữ nguyên các giá trị claim. Frame NONE/EXEMPTION/UNKNOWN làm draft AMBIGUOUS, **không xóa claim mâu thuẫn**. Guard kiểm quote, role, trạng thái và effect; không phải semantic oracle.
5. Reviewer approve/correct/reject/defer. Claim sai hoặc frame sai cần quyết định CORRECT có rationale riêng. Chỉ dữ liệu đã áp dụng qua review mới vào allocation/quan hệ/hard policy và optimizer. Quy tắc bảo vệ hiện có vẫn có hiệu lực.

Giới hạn 24 đoạn và 24 claim mỗi lượt; vượt giới hạn báo lỗi, giữ raw response đã có, không cắt bỏ âm thầm. Số call hoàn tất thông thường là `1 + số claim`, tối đa 25. Không tự retry/repair output. Missing/duplicate unit ID được báo ở cấp run; đủ unit không có nghĩa đủ nghĩa vụ. Lỗi stage giữ manifest FAILED và các response đã nhận, không thay input.

## Nguồn gốc từng trường

| Nội dung | Nguồn gốc |
|---|---|
| Văn bản requirement và các ví dụ OC phát triển | SOURCE_REQUIREMENT; nội dung ca là PREPARED_FIXTURE của repo. |
| Characteristic/owner, endpoints/mode/local transaction, cặp tách | LLM_PROPOSAL bước một, giữ trong `raw_claim`. |
| Subject/action/object/condition/modality/kind/effect | LLM_PROPOSAL bước hai, giữ trong `raw_frame`; không phải xác nhận. |
| Quote, source ID, offset | SOURCE_REQUIREMENT qua DETERMINISTIC_TRANSFORMATION; không gọi quote này là model-generated. |
| Role IDs, disposition, issues, hash và unit coverage | DETERMINISTIC_TRANSFORMATION. |
| Hard semantics, trọng số và tiêu chí phân hoạch | ARCHITECTURAL_POLICY hiện có, không phải model tự chấm. |
| Correction/review | HUMAN_DECISION hoặc PREPARED_FIXTURE theo người thao tác khai báo; không tự sinh expert label. |

`processing` giữ hai raw object, unit/span, field origins và digest (`STUDIO-SENTENCE-LINEAGE@1`). Review kiểm lại việc normalize; APPROVE không được sửa claim/frame gốc. CORRECT giữ bản gốc và provenance quyết định riêng. Quan hệ approve có citation provenance DETERMINISTIC_TRANSFORMATION nhưng claim provenance LLM_PROPOSAL. Digest phát hiện thay đổi dữ liệu, không xác thực danh tính hoặc chữ ký số.

## Ba lượt chạy thật ngày 28/11/2026

Ollama **0.40.18**, model **qwen3:4b**, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`. Temperature 0, seed 611, context 8192; primary tối đa 4000 token, frame tối đa 1200. Các OC đã biết được dùng để phát triển prompt; đây không phải held-out hoặc corpus stakeholder. Không chạy Equipment Loan/Room Scheduling.

| Run ID | Task / nguồn DEV-OC | Đoạn / draft / call | Token | Thời gian toàn lượt | Draft chưa có issue / có issue |
|---|---|---:|---:|---:|---:|
| `studio-extraction-008e2453ea674025b4510c142194954c` | QUALITY · 02/03/07/12 | 8 / 8 / 9 | 884 | 25,36 s | 4 / 4 |
| `studio-extraction-4f714e4baf9d4d708d8bfd99e5cbd524` | INTERACTION · 08/10 | 5 / 5 / 6 | 605 | 13,69 s | 2 / 3 |
| `studio-extraction-fdd00123a7a746d9b61c9ed5aba985b3` | SEPARATION · 10 | 2 / 2 / 3 | 219 | 6,01 s | 0 / 2 |

Thời gian gồm metadata/LLM/lưu artifacts trên máy hiện tại, chưa gồm review; mỗi task chỉ một lượt, không là benchmark latency. Tổng 15 draft/18 call; cả 15 REVIEW_REQUIRED, không approve/correct. Tất cả request/content hash của 18 stage đã đối chiếu khớp file; đây là kiểm integrity. Quote của 15 draft tra đúng source/span **theo thiết kế**, không phải điểm citation do model tự sinh.

Phân tích kỹ thuật trực tiếp từ raw output, **không phải labels độc lập**:

| Nguồn | Kết quả quan sát và giới hạn |
|---|---|
| QUALITY OC-02 | Có Reliability→REPORT cho khôi phục 90 giây; vẫn sinh Performance efficiency từ câu miễn 150 ms. Frame miễn nghĩa vụ giữ draft đó AMBIGUOUS. Draft Reliability không issue nhưng `condition="trong vòng 90 giây"` là thời hạn, chưa phải điều kiện lỗi ở đầu câu. Guard chưa phát hiện sai vai trò này. |
| QUALITY OC-03 | Có hai draft riêng Security→PROFILE và Reliability→REPORT, khác omission quan sát ở @2. Frame khôi phục chỉ giữ `bị dừng`, thiếu ngữ cảnh worker báo cáo đầy đủ; không kết luận đúng toàn bộ semantics. |
| QUALITY OC-07 | Đã có Compatibility→REPORT, nhưng còn Functional suitability→CREATE từ câu bối cảnh, bị chặn. Draft Compatibility không issue vẫn đặt tiêu chí kiểm `40/40 mẫu` trong condition; cần review, không coi là đúng vì qua gate. |
| QUALITY OC-12 | Owner COMPLETE có tín hiệu phù hợp nguồn; action `must maintain` là bản dịch, không nguyên văn nên bị chặn. Sinh thêm Reliability→REPORT từ câu `có thể phục hồi sau`, giữ mâu thuẫn để review. |
| INTERACTION OC-08 | Claim đầu CREATE→ROUTE ASYNC có tín hiệu từ câu không đợi, nhưng frame phân loại nhầm EXEMPTION/NONE khiến draft bị giữ lại. Claim ROUTE→COMPLETE SYNC từ câu chờ riêng đã xuất hiện và không issue. Câu miễn giao dịch còn sinh cạnh UNKNOWN không được hỗ trợ như một call riêng. |
| INTERACTION OC-10 | Có ROUTE→COMPLETE SYNC/local_transaction=true với frame LOCAL_ATOMIC_TRANSACTION, không issue. Câu bắt buộc tách lại sinh thêm interaction UNKNOWN; action không nguyên văn và effect không khớp nên bị chặn. |
| SEPARATION OC-10 | Hai claim cùng cặp ROUTE/COMPLETE. Một dùng sai câu giao dịch cục bộ: frame giữ LOCAL_ATOMIC_TRANSACTION nên guard chặn separation. Claim trên đúng câu tách vẫn có action `bắt buộc nằm ở` không liên tục nguyên văn, bị chặn. Chưa có draft separation qua guard trong lượt này. |

**6/15 chưa có issue không phải accuracy 40%, cũng không phải sáu claim đúng.** Guard có thể bỏ lọt sai condition và giữ lại claim có tín hiệu đúng vì frame sai. Precision/recall/F1/semantic_accuracy giữ null/NOT_MEASURED; thiếu reference độc lập, nhiều unit cùng document và dữ liệu đã dùng phát triển.

Checkpoint **`checkpoint-8662045b5ca04d82975a36cf284de535`** gộp nguồn cùng 15 draft để mở trong **Lịch sử và tải lại phiên Studio**. Event LOAD_SENTENCE_DEVELOPMENT_PROPOSALS, actor AGENT_TECHNICAL_SMOKE_TEST, provenance PREPARED_FIXTURE. Không có review giả. Mỗi run kiểm analyze trước/sau bằng nhau: 37 nghiệm; bản gộp vẫn 37, P031 đứng đầu theo trọng số mặc định. Điều này chứng minh draft chưa đổi optimizer, chưa chứng minh model đã gây ra phân hoạch mới.

## Thử nghiệm thăm dò trước khi chốt @3

Giữ **37 thư mục** dưới `runs/quantum-studio/development-probes/`, tách khỏi inventory extraction R1–R9 và ba run @3. Không xóa thử nghiệm thất bại:

| Nhóm / số thư mục | Quan sát để phát triển |
|---|---|
| grounding / 1 | `grounding-probe-c34b1ebbef174913b6804d4003c6807f`: thêm schema vào system của request R8, giữ schema/options/source. Endpoints có tín hiệu tốt hơn nhưng mode vẫn UNKNOWN; một lượt không chứng minh causal improvement về semantic quality. |
| compact / 3; claims / 3 | Schema gọn giảm field phải sinh nhưng còn mode/condition/frame sai và bỏ nghĩa vụ khôi phục. Không áp dụng tự động đáp án tham chiếu. |
| units / 3 | Tách theo câu lấy thêm nghĩa vụ khôi phục/chờ nhưng cũng sinh claim trên exemption/bối cảnh. Vì thế không coi mỗi câu là positive requirement. |
| frame / 14 | Thử để model tự trả `supports_claim`: bác nhiều claim có căn cứ, có lúc chấp nhận câu cùng transaction thành separation. Không dùng self-judge này làm validator hoặc oracle. |
| spans / 13 | Tên nguyên văn giúp role mapping nhưng còn lỗi frame. Biến thể probe từng suy effect từ claim có thể cho false separation qua; @3 yêu cầu model đọc effect từ source, giữ mâu thuẫn và qua guard, không dùng effect do adapter tự ép theo task. |

Ngoài probe grounding, các biến thể đổi nhiều yếu tố; **không phải ablation kiểm soát**. Artifact không đồng nhất metadata giữa các phiên thăm dò, chưa có freeze/labels/repetition preregistered. Không lấy tập probe hoặc 307 tests làm semantic benchmark.

## Tái chạy và giới hạn G10

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/check_studio_clause_development.py --method SENTENCE --task QUALITY --case OC-02 OC-03 OC-07 OC-12
.\.venv\Scripts\python.exe -X utf8 scripts/check_studio_clause_development.py --method SENTENCE --task INTERACTION --case OC-08 OC-10
.\.venv\Scripts\python.exe -X utf8 scripts/check_studio_clause_development.py --method SENTENCE --task SEPARATION --case OC-10
```

Mỗi lượt tạo ID mới, lưu architecture, primary/frame request/response, manifest và development-check. Script chỉ lấy văn bản OC, không gửi oracle allocations/relations/expected results cho model. Output lần sau có thể khác. Raw/checkpoint giữ local theo policy, không có trong Git; báo cáo này không thay replication bundle đầy đủ.

307 tests qua, gồm 17 tests mới dùng response/decision mô phỏng cho offset, hai stage, lineage, correction, provenance, duplication, exemption, separation, failure và UI; compileall/JavaScript syntax/diff check qua. AppTest kiểm render và draft không áp dụng; chưa có kiểm browser thật mới cho @3 trong mốc này.

`STUDIO-EVALUATION@1` chỉ freeze/score DIRECT @2, **chưa đánh giá SENTENCE @3**. Gói freeze cũ `studio-source-only-v1-20261128` giữ nguyên lịch sử; mã thực thi mới làm code hash không còn khớp. Cần tạo version freeze mới trên code đã commit trước một study tương lai, không sửa gói cũ hoặc bypass gate. Chưa có annotator/reference cho hai source mới. G2/G10 vẫn chưa hoàn tất.

## Căn cứ phương pháp

[Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs) khuyến nghị đưa schema cả vào format và prompt; repo áp dụng ở @3. Đây là tài liệu API, không chứng minh hiệu quả semantics. Geng, Josifoski, Peyrard và West, **Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning**, EMNLP 2023, 10932–10952, DOI `10.18653/v1/2023.emnlp-main.674`, nghiên cứu grammar/input-dependent structure cho NLP. Repo dùng schema động qua Ollama, **chưa triển khai/tái lập GCD của bài** và không chuyển metrics của bài sang Studio. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.674/)

Heuristic chia câu, quy trình claim→frame, lineage và policy AMBIGUOUS là thiết kế repo; chưa có bài trên xác nhận chúng tối ưu hoặc đủ entailment. Xem S22/S23 trong [source ledger](STUDIO_SOURCE_LEDGER.md), [inventory @1/@2](STUDIO_LLM_OUTPUT_EVALUATION.md) và [protocol độc lập](STUDIO_EVALUATION_PROTOCOL.md).
