# Review mệnh đề và bảo toàn ý nghĩa trước khi phân nhóm

## Phạm vi

Prompt `STUDIO-EXTRACT@2` yêu cầu Ollama đề xuất từng mệnh đề, không chỉ trả nhãn ISO/IDs. `STUDIO-CLAUSE@1` ghi chủ thể, hành vi, đối tượng, điều kiện, modality, component chịu trách nhiệm/nhận tương tác/bối cảnh, loại nghĩa và tác động kiến trúc. Mọi đề xuất vẫn `REVIEW_REQUIRED`; JSON hợp lệ, quote khớp hoặc frame đầy đủ chưa xác nhận entailment.

Đây là cấu trúc hỗ trợ review của Studio, không phải parser EARS, semantic theorem prover hoặc classifier được huấn luyện theo bài báo. P0 và protocol nghiên cứu Tutor giữ nguyên. Các ca OC là dữ liệu phát triển đã biết, không thành held-out sau khi thay prompt.

## Chính sách rõ ràng

| Khai báo | Tác động cho phép sau review | Trường hợp phải giữ lại |
|---|---|---|
| OBLIGATION · nghĩa vụ | Target chất lượng; mode khi có căn cứ chờ/trả sớm; giao dịch cục bộ hoặc tách bắt buộc | Thiếu chủ thể, quote/modality, ID chưa ánh xạ hoặc frame không khớp claim. |
| PROHIBITION · điều cấm | Có thể là target chất lượng, như không được tiết lộ dữ liệu; tác động khác cần review cụ thể | Không biến “must not separate” thành bắt buộc khác Quantum. |
| PERMISSION · cho phép | Có thể hỗ trợ ASYNC nếu bên gọi được trả trước hoàn tất và endpoint rõ | Không tự tạo target chất lượng bắt buộc. |
| EXEMPTION · không bắt buộc | Ghi ngoài phạm vi, không tạo target/constraint chủ động | Không lấy “không phải đáp ứng 150 ms” làm Performance target. |
| DESCRIPTION · mô tả | Workflow order giữ mode UNKNOWN | Không suy ra SYNC chỉ từ thứ tự hoặc câu đứng cạnh nhau. |
| UNKNOWN/AMBIGUOUS | DEFER/REJECT hoặc sửa đầy đủ trước khi áp dụng | Không đổi thành nghĩa vụ đã xác nhận. |

`OUT_OF_SCOPE`/`AMBIGUOUS` phải có effect NONE và các trường tạo ánh xạ rỗng. Role IDs trong frame chỉ mô tả vai trò đang xem xét; không phải allocation. Bản ngoài phạm vi được reviewer xác nhận tạo event `NO_ACTIVE_EFFECT`, không thay vector hay tập phân hoạch.

Các effect kiến trúc được nối rõ với đầu ra: `QUALITY_OBLIGATION` vào allocation; `WAIT_COMPLETION` → SYNC; `RETURN_BEFORE_COMPLETION` → ASYNC; `WORKFLOW_ONLY` → UNKNOWN; `LOCAL_ATOMIC_TRANSACTION` → SYNC cùng hard policy cục bộ; `REQUIRE_SEPARATION` → hard separation. Đây là policy của Studio. Không tự bỏ quy tắc được bảo vệ hoặc biến ASYNC thành điều kiện đủ để tách.

## Kiểm trước và sau quyết định

- Các phần text phải nằm nguyên văn trong quote, quote nằm trong requirement và không lặp nhiều vị trí. Bản cần tham chiếu mơ hồ phải mở rộng ngữ cảnh. Subject/object/modality lấy từ câu khác với action sẽ bị giữ lại để làm rõ. Quy tắc dấu câu là kiểm cấu trúc có giới hạn, không phải bộ phân tích ngôn ngữ đầy đủ.
- Vai trò chủ thể/đối tượng được đối chiếu với tên/ID hiện hành khi chúng xuất hiện rõ trong phần tương ứng. Biệt danh chưa biết không được tự đoán, trừ khi source đã khai báo scope hoặc reviewer bổ sung ánh xạ rõ ràng. Component bối cảnh gây lỗi không tự trở thành component chịu target.
- Một số cue phủ định được dùng để báo mâu thuẫn: không bắt buộc không thành nghĩa vụ, cấm tách không thành yêu cầu tách. Các cue này là lint của repo, không chứng minh đủ mọi cách diễn đạt tiếng Việt/Anh, quan hệ điều kiện hoặc phạm vi phủ định.
- Mode hoặc hard separation có điều kiện không tự trở thành rule vô điều kiện. Tập nhánh tương tác tiếp tục qua review điều kiện G4. Nếu chỉ phân tích một ngữ cảnh được chọn, reviewer phải CORRECT, đánh dấu effect là policy bổ sung và ghi rationale; đây là giả định phạm vi phân tích, chưa chứng minh bao phủ môi trường production.
- Chỉ CORRECT mới ghi được `human_fields` cho phần reviewer bổ sung ngoài nguồn. Model không tự gán HUMAN_DECISION. Rationale và xác nhận đã đọc nghĩa/điều kiện/phủ định là bắt buộc khi áp dụng qua UI.
- Đề xuất trùng chính xác source/payload trong một run được đánh dấu và không áp dụng lần hai. Đây không phải kiểm tương đương ngữ nghĩa giữa paraphrase; mục tiêu trùng tiếp tục qua review `duplicate_of`.
- Allocation và binding quan hệ mang `ClauseReview`: span, source/catalog digest, frame, claim, proposal/run ID, actor khai báo, rationale và thời gian. Đổi source/catalog/claim/scope khiến bằng chứng cũ chặn optimizer. Sửa nguồn qua canvas gỡ allocation cũ; checkpoint gốc được giữ. Không dùng thao tác xác nhận một quote để thay review cả frame của quan hệ đã cũ.
- Mỗi record tách nguồn proposal gốc, nguồn claim sau sửa và nguồn quyết định review. Ví dụ một phản hồi thật có `proposal_provenance=LLM_PROPOSAL`, nhưng correction kỹ thuật của agent mang `claim_provenance=PREPARED_FIXTURE` và review fixture; không gọi đó là expert label.

## Thao tác UI

Mở **Phân tích yêu cầu hiện tại bằng Ollama**, chọn nguồn và tác vụ. QUALITY nhận NFR; INTERACTION/SEPARATION cho chọn cả FR và NFR. Đọc câu đầy đủ và các phần frame ở từng đề xuất. Đặt scope và vai trò đúng với component chịu trách nhiệm. Nếu sửa, chọn **Áp dụng phần đã sửa**, khai báo rationale/nguồn quyết định, xác nhận đã review và lưu. DEFER/REJECT giữ nguyên mô hình.

Nếu model bỏ sót một mệnh đề, mở **Bổ sung mệnh đề reviewer thấy model bỏ sót**, chọn source rồi tạo draft. Draft này ghi HUMAN_DECISION, giữ AMBIGUOUS và chưa đổi optimizer. Reviewer điền mệnh đề rồi áp dụng như một correction; không đổi nguồn thành LLM_PROPOSAL.

Phần ánh xạ ISO hiển thị các mệnh đề đã dùng, provenance và component → Quantum của các phương án đang xem. Cùng một ISO trong một NFR hợp nhất scope và giữ từng proof, không ghi đè mất scope đã duyệt. Danh tính objective vẫn là ISO + NFR gốc theo policy hiện hành; hai target độc lập cùng ISO cần tách NFR hoặc scenario để tránh hiểu đây là hai objective riêng trong năm trục.

Đối chiếu quote chỉ cho thấy vùng văn bản chưa được trích. Quote phủ toàn requirement vẫn có thể bỏ sót một nghĩa vụ bên trong. Giao diện không gọi đây là semantic coverage/recall. Đề xuất cũ không có frame giữ nhãn `LEGACY_UNSTRUCTURED`, vẫn đọc được và cần xác nhận review thủ công riêng trên UI.

## Lượt gọi thật đã quan sát

Ollama `0.40.18`, model `qwen3:4b`, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`:

| Run | Đầu vào chuẩn bị | Kết quả thực tế trước review |
|---|---|---|
| `studio-extraction-94d5e8d6b5b048599be491dfb17835b6` | OC-02/03/07/12, một batch, 849 token đầu ra | Bốn proposal đều OUT_OF_SCOPE nhưng có allocation. OC-03 chỉ trả Security, chưa có proposal Reliability riêng. OC-07 gán thêm CREATE và nhầm object role. Không proposal nào được đưa vào optimizer. |
| `studio-extraction-4c8725ba445c49c8af599379cfe4d528` | Chỉ OC-02, cùng prompt @2, có hash mã kiểm tra trong manifest | Trả Performance efficiency cho REPORT, vẫn OUT_OF_SCOPE với mapping; frame có phần ngoài quote/lẫn mệnh đề. Tiếp tục bị giữ lại. |

Các phản hồi này là **LLM_PROPOSAL từ lần gọi thật**; văn bản OC là **PREPARED_FIXTURE**. Lượt một được quan sát trong quá trình phát triển, sau đó bổ sung guard lẫn mệnh đề. Lượt một và lượt hai khác batch context nên không được diễn giải là ablation một biến. Raw request/response/manifest và `development-check.json` giữ local; không sửa hay thay bằng bản “đẹp hơn”. Chưa có independent labels; `semantic_accuracy=null`.

Trên UI 8501 đã tải checkpoint `checkpoint-c41a1e6e1e0e49b0b8f0a094bed4035d` chứa nguyên bốn proposal của lượt đầu. Với DEV-OC-12, sửa disposition thành PROPOSED, action `duy trì`, modality `phải`, điều kiện `Trong 15 phút kể từ lúc Operations Reporting bị ngắt`, effect QUALITY_OBLIGATION. Giữ chủ thể/owner COMPLETE, context REPORT, Reliability và quote nguồn. Actor `AGENT_TECHNICAL_SMOKE_TEST`, quyết định `PREPARED_FIXTURE`, action CORRECT, có rationale và xác nhận review. Checkpoint **checkpoint-07b06b4948c64e1f9afc35582d10888f** giữ trước–sau. Proposal gốc vẫn LLM_PROPOSAL; claim/review kỹ thuật là fixture.

Với ưu tiên SYNC_FIRST và trọng số mặc định, P011 vẫn xếp đầu; vector `(0,1,0,0,0)` → `(0,1,0,0,1)`, điểm 6→8. P031 `(0,0,1,1,1)` → `(0,0,1,1,2)`, điểm 5→7. Component COMPLETE nhận Reliability ở Q2 trên cả A/P031, B/P011, C/P009. Không thêm cạnh, không đổi hard rules hoặc số 37 phân hoạch khả thi. Thay đổi chỉ thêm target trên một component nên tăng mix, chưa có lý do buộc đổi ranh giới. UI đã hiển thị đúng source/proposal/provenance và tuyến Quantum. Đây là smoke kỹ thuật của agent, không phải stakeholder acceptance.

Tái lập đường chạy, không tự approve:

```powershell
.\.venv\Scripts\python.exe scripts/check_studio_clause_development.py
.\.venv\Scripts\python.exe scripts/check_studio_clause_development.py --case OC-02
```

Script lưu model đầu vào và hash script; manifest mới lưu hash request, response content và mã extraction/validator. Inference không bảo đảm cùng output khi đổi batch/model/runtime dù seed và temperature được cố định.

## Nguồn và giới hạn

- Mavin, Wilkinson, Harwood, Novak. **Easy Approach to Requirements Syntax (EARS)**, RE 2009, 317–322, DOI `10.1109/RE.2009.9`. Năm template và trigger/state/response gợi ý cấu trúc review. Studio chưa triển khai parser EARS hoặc tái hiện đánh giá hàng không; kiểm dấu câu không tương đương EARS. [Accepted manuscript do tác giả cung cấp](https://www.researchgate.net/profile/Alistair-Mavin-2/publication/224079416_Easy_approach_to_requirements_syntax_EARS/links/568ce3bf08aeb488ea311990/Easy-approach-to-requirements-syntax-EARS.pdf)
- Femmer, Méndez Fernández, Wagner, Eder. **Rapid quality assurance with requirements smells**, JSS 123, 190–213, 2017, DOI `10.1016/j.jss.2016.02.047`. Lint là phản hồi sớm bổ trợ review; cue phủ định của Studio là phần tự thiết kế, chưa có bộ nhãn đánh giá false positive/negative. Không chuyển precision/recall của Smella sang dự án. [Bản tác giả](https://wwwbroy.in.tum.de/~femmer/works/2016-requirements_smells-jss.pdf)
- Cleland-Huang, Settimi, Zou, Solc. **Automated classification of non-functional requirements**, Requirements Engineering 12, 103–120, 2007, DOI `10.1007/s00766-007-0045-1`. Phân loại NFR và thích nghi domain là task riêng với mapping component. Studio chưa triển khai classifier/retraining trong bài. [PDF bài báo](https://homepages.uc.edu/~niunn/courses/RE-refs/Huang-REJ07.pdf)
- Alturayeif, Ahmad, Hassine. **TraceLLM**, Requirements Engineering 31, article 6, 2026, DOI `10.1007/s00766-026-00460-1`. Tách dữ liệu và giữ prompt/run cho đánh giá trace links. Lượt OC hiện là phát triển đã biết, chưa đáp ứng held-out/independent labels của G10; không dùng F2 của bài cho Studio. [Nhà xuất bản](https://link.springer.com/article/10.1007/s00766-026-00460-1)

`tests/test_studio_semantics.py` kiểm các đường đã định nghĩa trên fixture phát triển, bao gồm OC-02/03/07/12, điều cấm, alias, source revision, sai vai trò/mode, quote lặp, duplicate payload, lẫn mệnh đề, bổ sung của reviewer và checkpoint. Các test chứng minh guard/hành vi tính toán trong phạm vi đã khai báo; không xác nhận mọi câu được hiểu đúng. NFR thủ công hoặc proposal lịch sử chưa có frame vẫn có thể mang quyết định kiến trúc do reviewer khai báo, không được gắn là semantic validation tự động.
