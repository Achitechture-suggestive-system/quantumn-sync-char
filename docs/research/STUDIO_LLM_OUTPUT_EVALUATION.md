# Đánh giá phản hồi Ollama hiện có — 28/11/2026

## Kết luận theo bằng chứng hiện tại

`qwen3:4b` đã trả proposal thật cho ISO/component, tương tác SYNC/ASYNC và yêu cầu tách. Tuy nhiên, các phản hồi đã lưu còn sai quote, sai endpoint, lẫn vai trò/nghĩa vụ và thiếu mệnh đề. Model hiện phù hợp làm nguồn đề xuất để reviewer kiểm; các lượt này chưa đủ căn cứ cho tự động xác nhận evidence hoặc chia Quantum trực tiếp từ output thô.

Phần R1–R7 dưới đây đọc **bảy thư mục extraction tại mốc chốt đầu**, không gọi model mới trong bước audit đó, không thay raw output và không dựng expert labels. R8/R9 bổ sung INTERACTION/SEPARATION: snapshot DIRECT @1/@2 có **9 run, 19 proposal**, 16 quote khớp và 15 hàng có issue lịch sử. Ba lượt SENTENCE @3 tiếp theo có **15 draft qua 18 call**, báo riêng ở phần dưới vì quote được tra nguồn, không phải model sinh. Ngoài ra có 37 thư mục probe phát triển, không gộp vào inventory hoặc benchmark. Đây là phân tích lỗi phát triển do agent thực hiện, không phải đánh giá độc lập. Phạm vi không bao gồm mọi lần gọi LLM lịch sử của pipeline PetClinic/Tutor hoặc các bộ requirement sinh sẵn khác trong repo.

Mã đối chiếu snapshot R1–R7: `ed779df4f4c2b3d2fe4822c26a74f21cc01420a3`. [CI 46041605823](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/46041605823) thành công; suite tại mốc đó có 264 tests. Mốc X1/R8/R9 sau này có 290 tests. Test pass xác nhận hành vi phần mềm trong phạm vi test, không xác nhận độ đúng ngữ nghĩa của model.

## Mẫu dữ liệu và tính nguyên vẹn

Cập nhật @3: [báo cáo trích xuất theo câu](STUDIO_SENTENCE_EXTRACTION.md) ghi ba run thật ngày 28/11, raw claim/frame, provenance, 37 probe thăm dò, lệnh tái chạy và checkpoint chờ review. QUALITY 8 draft (4 chưa có issue), INTERACTION 5 (2 chưa có issue), SEPARATION 2 (0 chưa có issue). Model lấy thêm nghĩa vụ bị bỏ sót nhưng còn false proposals, sai condition ngay ở draft không issue và frame tự phân loại nhầm non-waiting thành exemption. Không auto-approve; 37 nghiệm giữ nguyên. Không gọi 6/15 là accuracy; semantic metrics vẫn null. Counts quote ở bảng R1–R7 dưới đây chỉ thuộc snapshot cũ, không trộn quote tra nguồn của @3 với quote LLM tự sinh.

Các lượt diễn ra 26–27/11/2026 UTC; báo cáo kiểm lại ngày 28/11 giờ Việt Nam. Ollama `0.40.18`, tag `qwen3:4b`, digest `359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`. OC là văn bản PREPARED_FIXTURE đã dùng trong phát triển. Hai nguồn `REQ-04` được nhập để smoke UI, có nội dung và source digest khác nhau; không ghép hai nguồn chỉ vì cùng ID. Chúng không phải requirement do stakeholder độc lập cung cấp.

| Chỉ báo kiểm lại | Kết quả quan sát | Được phép suy ra |
|---|---:|---|
| Request hash khớp manifest | 7/7 lượt | Request đã lưu nhất quán với hash. |
| Response content hash khớp manifest | 7/7 lượt | Nội dung phản hồi đã lưu nhất quán với hash. |
| Proposal payload giữ nguyên nội dung raw response | 12/12 hàng | Adapter không sửa các giá trị model thành đáp án chuẩn bị sẵn; trường metadata được thêm riêng. |
| Response có `done_reason=stop`, tag model khớp | 7/7 lượt | Các response này hoàn tất; không đo tính đúng nghĩa hoặc tính sẵn sàng của provider qua mọi lần gọi. |
| Quote không rỗng, là chuỗi con nguyên văn của đúng source | 9/12 hàng | Chỉ là độ khớp chuỗi; quote đúng vẫn có thể không hỗ trợ claim. |
| Có ít nhất một `issues` trong manifest lúc chạy | 8/12 hàng | Các validator ở thời điểm đó báo vấn đề. Bốn hàng không có issue không phải bốn hàng đúng. |
| Proposal prompt @2 bị giữ lại khi kiểm hiện tại | 5/5 hàng | Có blocker cấu trúc/clause. Không được diễn giải là semantic error rate hay detection recall. |
| Precision / recall / F1 / semantic accuracy | `null` · NOT_MEASURED | Chưa có independent adjudicated reference labels. |

Mẫu số 12 của snapshot R1–R7 là số **hàng model trả về**, gồm tám QUALITY, ba INTERACTION và một SEPARATION. Nó không bao gồm các nghĩa vụ bị model bỏ sót, không phải số case độc lập. Prompt @1/@2, tác vụ và batch context khác nhau; không gộp chúng thành benchmark so sánh chất lượng prompt. Không suy ra tỷ lệ áp dụng của người dùng từ `REVIEW_REQUIRED` trong manifest gốc: quyết định về sau nằm ở checkpoint riêng.

| Đầu ra / căn cứ | Nguồn gốc cần giữ |
|---|---|
| Nội dung requirement trong request | SOURCE_REQUIREMENT, được chuẩn bị cho phát triển/smoke; không phải corpus stakeholder độc lập. |
| Quote, label, IDs, mode, disposition và frame raw | LLM_PROPOSAL của bảy response đã lưu. |
| Hash, kiểm chuỗi, issues, vector, thứ hạng và feasible counts | DETERMINISTIC_TRANSFORMATION; issues lịch sử và re-audit hiện tại được tách riêng. |
| Ý nghĩa cùng/tách Quantum, trọng số và cost drivers | ARCHITECTURAL_POLICY của repo. |
| Correction do actor agent thực hiện | PREPARED_FIXTURE / technical smoke; @1 có metadata legacy thiếu provenance cấp event. |
| Nhãn hoặc acceptance độc lập từ con người | Chưa có HUMAN_DECISION đủ điều kiện làm reference trong mẫu báo cáo này. |

Nhận xét ngữ nghĩa ở bảng lỗi là phân tích kỹ thuật của agent từ source/raw output; không gắn chúng là chuyên gia hoặc là một inference đánh giá độc lập.

## Sổ bảy lượt được kiểm

Mỗi thư mục dưới `runs/quantum-studio/extractions/<run-id>/` chứa `request.json`, `response.json`, `manifest.json`. R6/R7 còn có `architecture.json` và `development-check.json`. Raw artifacts được giữ local và loại khỏi Git theo policy; bảng này là tóm tắt, không thay bộ dữ liệu tái lập đầy đủ.

| Mã | Run ID | Prompt / tác vụ | Nguồn | Hàng trả về / token |
|---|---|---|---|---:|
| R1 | `studio-extraction-1e1dc304fef34fc69c43ea8f35d0ea6c` | @1 · QUALITY | OC-02, OC-03 | 2 / 173 |
| R2 | `studio-extraction-a33b2fd3d4374c32b34f98422f31c276` | @1 · INTERACTION | OC-08, OC-10 | 2 / 213 |
| R3 | `studio-extraction-3cfd1c54ec1649838d7ecf046d65ae91` | @1 · SEPARATION | OC-10 | 1 / 71 |
| R4 | `studio-extraction-0ac9899209d24dad8f6f33fedf82b90b` | @1 · QUALITY | REQ-04, p95 900 ms | 1 / 108 |
| R5 | `studio-extraction-7a648ae31c004fab9cb770c4750d8964` | @1 · INTERACTION | REQ-04, chờ xác nhận | 1 / 83 |
| R6 | `studio-extraction-94d5e8d6b5b048599be491dfb17835b6` | @2 · QUALITY | DEV-OC-02/03/07/12 | 4 / 849 |
| R7 | `studio-extraction-4c8725ba445c49c8af599379cfe4d528` | @2 · QUALITY | DEV-OC-02 riêng | 1 / 218 |

Hash prefixes sau chỉ để nhận diện; khi audit dùng SHA-256 đầy đủ trong manifest. Request hash theo `json.dumps(ensure_ascii=False, sort_keys=True)`, UTF-8; response hash theo bytes UTF-8 của `message.content`, không phải toàn bộ JSON response.

| Run | Request SHA-256 prefix | Response content SHA-256 prefix |
|---|---|---|
| R1 | `e8b8591336103afe` | `d4f4b6a41a405e01` |
| R2 | `8490366820c7009d` | `14a2619f65129c32` |
| R3 | `3f53292a75a0b9d9` | `e67af26b3222f5aa` |
| R4 | `b687569eeb1753b7` | `261e94ff145b095e` |
| R5 | `4f86fc1a76cf9806` | `2eb0df0393845ffb` |
| R6 | `66ddf8ea442b409b` | `de1888823bd5aca0` |
| R7 | `37ba1cf3f4457889` | `83350b7188016047` |

## Đọc từng lỗi và tác động kiến trúc có thể xảy ra

Các diễn giải trong cột nhận xét là **technical error analysis**, không phải reference labels độc lập. Không tự dùng chúng để sửa evidence trong phiên người dùng.

| Run / nguồn | Model thực sự trả | Nhận xét từ nguồn và giới hạn | Cách pipeline xử lý |
|---|---|---|---|
| R1 / OC-02 | Reliability → REPORT, quote đủ hai câu; không issue ở validator @1. | Có tín hiệu phù hợp với nghĩa vụ khôi phục 90 giây. Quote đồng thời chứa câu miễn nghĩa vụ 150 ms, chưa tách clause; không đủ căn cứ gọi toàn bộ diễn giải đúng. | Giữ REVIEW_REQUIRED, không tự đưa allocation vào optimizer. |
| R1 / OC-03 | Security → PROFILE; quote thêm `: ` trước `3 phút`. | Nguồn còn có nghĩa vụ khôi phục REPORT trong 3 phút; không có proposal riêng cho nghĩa vụ đó. | Quote sai bị báo issue; thiếu mệnh đề cần reviewer đọc toàn nguồn, không được coi quote dài là recall đầy đủ. |
| R2 / OC-08 | CREATE→ROUTE, ASYNC, `local_transaction=false`, quote đúng. | Phù hợp với câu không đợi Router. Nhưng nguồn còn nêu ROUTE phải chờ COMPLETE; không có proposal cho cạnh thứ hai trong lượt này. | Hàng trả về vẫn cần review; reviewer có thể bổ sung mệnh đề thiếu với provenance riêng. |
| R2 / OC-10 | ROUTE→COMPLETE, SYNC và giao dịch cục bộ; quote bị chèn `Ticket:`. | ID/mode có tín hiệu từ nguồn nhưng citation bị biến đổi. Không thể dùng thông tin có vẻ hợp lý để bỏ qua citation sai. | Validator quote chặn bản gốc. Policy tách trong cùng nguồn vẫn cần review riêng, không tự giải mâu thuẫn bằng bỏ rule. |
| R3 / OC-10 | Tách ROUTE/COMPLETE, quote là đoạn yêu cầu **cùng giao dịch cục bộ**. | Cặp component đúng danh mục và nguồn có câu tách ở phía sau, nhưng đoạn model viện dẫn không chứng minh separation. Nếu chấp nhận chỉ dựa quote/ID, có thể tạo hard constraint bằng căn cứ sai. | Validator @1 không báo lỗi chuỗi/ID; bắt buộc người review kiểm entailment. Output @1 là legacy, không được tính như đã chạy frame guard @2. |
| R4 / REQ-04 | Reliability → LOGIN/CREATE; quote đổi `900 ms` thành `90:00 ms`. | Mục tiêu nguồn là thời gian phản hồi p95; cần xem xét Performance efficiency. Sai số và nhãn là hai vấn đề riêng. | Chặn quote sai. Correction kỹ thuật sau đó có actor/rationale và nguồn riêng. |
| R5 / REQ-04 | REPORT→ROUTE, SYNC; quote đúng toàn câu. | Nguồn nêu Ticket Router chờ Ticket Completion: hai endpoint model trả sai dù quote khớp và mọi ID hợp lệ. | Validator @1 không báo issue; review phải sửa endpoints. Đây là ví dụ trực tiếp cho giới hạn của citation matching. |
| R6 / DEV-OC-02 | Reliability → REPORT nhưng OUT_OF_SCOPE, effect NONE; action lấy câu miễn 150 ms, modality lấy câu khôi phục. | Trạng thái mâu thuẫn với mapping hoạt động; lẫn hai câu có nghĩa khác nhau. | Manifest gốc đã chặn trạng thái; kiểm lại hiện tại còn báo lẫn modality/action. Không sửa manifest cũ. |
| R6 / DEV-OC-03 | Security → PROFILE nhưng OUT_OF_SCOPE; modality chứa cả mệnh đề khôi phục REPORT. | Lẫn mệnh đề, thiếu proposal Reliability riêng. | Bị giữ lại; guard hiện tại báo thêm lẫn câu, không suy rằng guard tìm đủ mọi thiếu sót. |
| R6 / DEV-OC-07 | Functional suitability → REPORT/CREATE, OUT_OF_SCOPE; object_ids chứa CREATE. | Nguồn gọi CREATE là bối cảnh, nghĩa vụ đọc v1/v2 thuộc REPORT. Scope chứa CREATE và vai trò object chưa có căn cứ; label cần review theo taxonomy. | Có blocker role/trạng thái; không đưa cả hai component vào mục tiêu chất lượng. |
| R6 / DEV-OC-12 | Reliability → COMPLETE, REPORT là context; OUT_OF_SCOPE, effect NONE; condition/modality đảo vai. | Owner/context có tín hiệu phù hợp với nguồn, nhưng claim chưa sử dụng được vì trạng thái và frame. | Giữ lại cho tới correction. Không đổi OUT_OF_SCOPE thành approved trong adapter. |
| R7 / DEV-OC-02 | Performance efficiency → REPORT, OUT_OF_SCOPE; object thành `mốc 15:00 ms`. | Quote toàn nguồn đúng nhưng fragment object không nằm trong quote; nhắm câu được miễn nghĩa vụ và bỏ nghĩa vụ khôi phục riêng. | Bốn issues được ghi: fragment ngoài quote, object/modality lẫn câu, disposition có mapping. Không proposal nào áp dụng. |

Không quan sát duplicate payload trong 12 hàng này không chứng minh model không sinh duplicate hoặc paraphrase trùng ở dữ liệu khác. Các cơ chế duplicate và canonical target có tests riêng; không lấy kết quả tests đó làm kết quả inference.

## Tác động sau review đã được tái tính

Hai before/after dưới đây được đọc từ checkpoint và tái tính trên mã đối chiếu. Chúng chứng minh đường truyền dữ liệu sau một correction kỹ thuật. Actor là `AGENT_TECHNICAL_SMOKE_TEST`; không phải stakeholder hoặc expert annotation.

| Correction có lưu lịch sử | Trước → sau với cùng setting | Giải thích |
|---|---|---|
| R4, `checkpoint-7e212d4b009645dc91b662c3e827e56c` | WEIGHTED: P031 đứng đầu 5 điểm → P011 đứng đầu 8 điểm; 37 → 37 nghiệm khả thi. | Sửa sang Performance efficiency trên LOGIN/CREATE và quote nguyên văn. Allocation mới làm đổi spread/mix và thứ hạng; 5→8 không phải chất lượng xấu đi vì hai điểm thuộc hai input khác nhau. Event legacy chưa có trường provenance cấp event; báo cáo nhận diện đây là agent smoke qua actor/rationale, không bổ sung giả metadata vào file cũ. |
| R6 / DEV-OC-12, `checkpoint-07b06b4948c64e1f9afc35582d10888f` | SYNC_FIRST: P011 vẫn đứng đầu, vector `(0,1,0,0,0)` → `(0,1,0,0,1)`, 6→8 điểm. P031 5→7; 37 → 37 nghiệm. | Correction disposition/frame/effect mới cho phép Reliability→COMPLETE vào scoring. Target chỉ có một owner nên tăng mix trong Quantum của COMPLETE; không thêm topology hoặc hard rule. Ranh giới giữ nguyên có lý do. Record @2 tách proposal LLM_PROPOSAL, claim và review PREPARED_FIXTURE. |

Hard rules của ca DEV-OC-12 trước/sau bằng nhau. Correction và điểm là bằng chứng kỹ thuật về tác động nhân quả trong mô hình; không chứng minh Reliability 99,5% đạt được. Quality measurement giữ NOT_MEASURED. [Chi tiết UI, policy và provenance](STUDIO_CLAUSE_REVIEW.md).

Kiểm lại proposal @2 trên hai `architecture.json` lưu sẵn còn cho cùng 37 nghiệm, P031 đứng đầu với trọng số mặc định; thao tác đọc/kiểm proposal không thay input optimizer. Không nhầm setting WEIGHTED của phép kiểm này với SYNC_FIRST của checkpoint correction.

## Đánh giá mức sẵn sàng và việc còn thiếu

- **Đã có bằng chứng:** inference cục bộ thật, raw response giữ nguyên, citation/role/disposition guard có hiệu lực trong các đường đã kiểm, review tạo revision và ảnh hưởng scoring/downstream. Các mô hình cỡ lớn cũng giữ objective/hard constraints, theo [báo cáo D2](STUDIO_LARGE_BACKEND.md).
- **Chưa đủ để tự động tin output:** câu nhiều nghĩa vụ bị bỏ sót, span/frame và endpoint có thể sai; không issue không đồng nghĩa đúng; batch @2 bốn hàng đều mâu thuẫn disposition. Snapshot R1–R7 chưa có lượt INTERACTION/SEPARATION thật với prompt @2. R8/R9 bổ sung bằng chứng inference cho hai tác vụ này nhưng vẫn có lỗi, không thay bằng kết quả tests.
- **Chưa có phép so sánh prompt đáng tin:** @1/@2 khác cấu trúc, batch và thời điểm validator; các ca đã được dùng để điều chỉnh guard. Một lần singleton không đủ kết luận batching là nguyên nhân hoặc @2 tốt/xấu hơn theo tỷ lệ.
- **Bước nghiên cứu tiếp theo:** chốt prompt/schema/code, lấy dữ liệu từ document/case mới và nhãn source-only độc lập trước khi inference, định nghĩa đơn vị mệnh đề/matching và adjudication, rồi đo riêng raw model, sau structural gate và sau human review. Ghi omissions, false hard policies, corrections và thời gian review với mẫu số. Chưa chạy bước này trong báo cáo.

Trade-off và vector trong Studio hiện được tính bởi hàm Python/CP-SAT theo policy, không phải con số model tự chấm. `explain_candidate` tạo giải thích xác định từ cost drivers; không gắn phần này là LLM-generated. Các fixture benchmark 9–50 component không đo năng lực đọc hiểu của qwen.

Khung phân biệt link/citation và đánh giá độc lập liên hệ nguồn S10 (TraceLLM), S12 (oracle problem), S17 (EARS) và S18 (NFR classification) trong [source ledger](STUDIO_SOURCE_LEDGER.md). Đây là nguồn phương pháp; kết quả định lượng của các bài không được dùng làm kết quả Studio. Không cần gọi LLM khác để tự chấm model rồi xem đó là reference label độc lập.

## Cập nhật R8/R9 — INTERACTION và SEPARATION prompt @2

Hai lượt chạy thật ngày 28/11/2026 dùng code `b52909f653aed7a2ffaab378e841c51007ccc6f6`, prompt STUDIO-EXTRACT@2, cùng Ollama/model digest đã ghi ở trên. Input là OC-08/OC-10 đã biết, thêm vào mẫu Ticket dưới ID DEV-OC-08/DEV-OC-10, kind UNSPECIFIED. Đây là PREPARED_FIXTURE dùng phát triển, không phải held-out. Không điều chỉnh prompt/code sau khi thấy hai response và không sửa raw artifacts.

| Run | Task / source | Đầu ra thực tế | Thời gian call |
|---|---|---|---:|
| R8 · `studio-extraction-9f887b70a4e94d999e161290aa18db11` | INTERACTION · DEV-OC-08, DEV-OC-10 | 5 proposal, 911 token; cả năm OUT_OF_SCOPE, mode UNKNOWN, vẫn có endpoint hoạt động. | 28,59 giây |
| R9 · `studio-extraction-a186da6bc7e64cac9ff33173ce1c732d` | SEPARATION · DEV-OC-10 | 2 proposal, 369 token; một OUT_OF_SCOPE, một PROPOSED; cả hai chọn REPORT/CREATE. | 7,25 giây |

Các thời gian là wall-clock của từng call trên máy hiện tại, gồm overhead; hai lượt không là benchmark latency hoặc phân bố hiệu năng. Request/response SHA-256 đầy đủ được kiểm lại:

| Run | Request hash | Response content hash |
|---|---|---|
| R8 | `b6e38d5f56ca4e2469aca710041f30e7364b99f649abbed5d3f71de59a6797cd` | `2f3a378cb245c2187f5c893e5d72e4e714ee26abbf8de201fc20ad3c83860378` |
| R9 | `4a7a64675a5eddd4b824a3cad5a139d14fe98c7e027223d187f9fbb1a821a0a3` | `3b949927848dac8d8b1577d2327716164c7b0cfb3a68915b0889f2228ae0871d` |

**R8:** Một frame gọi đúng chủ thể ROUTE và object COMPLETE ở câu chờ xác nhận, nhưng claim lại là PROFILE→ROUTE. Các claim còn lại cũng dùng PROFILE dù source không nêu component này. `modality="SYNC"` không phải đoạn nguyên văn trong nguồn. Hai frame dùng chuỗi rỗng ở trường đòi null hoặc text có nội dung. Quote nguồn đều khớp nhưng disposition/role/frame mâu thuẫn; không proposal nào được áp dụng. Có tách thêm hàng theo mệnh đề chưa chứng minh phân loại hay mode đúng.

**R9:** Proposal đầu trích câu cùng giao dịch cục bộ và thêm `giao: giao dịch` vào phần condition; modality lại là SYNC. Proposal sau trích đúng câu mandatory isolation, có effect REQUIRE_SEPARATION nhưng endpoint REPORT/CREATE lệch ROUTE/COMPLETE trong nguồn/frame; modality PROHIBITION không có nguyên văn và chính sách không được mô tả đúng vai trò. Các guard fragment/role/disposition/condition đều giữ lại. Chỉ đổi disposition sang PROPOSED vẫn không đủ để dùng làm hard constraint.

Tất cả bảy quote mới đều là chuỗi con của đúng source. **7/7 proposal mới có issue**, cả bảy giữ REVIEW_REQUIRED. Đây là kết quả structural gate trên các output cụ thể, không phải semantic error rate, accuracy hoặc detection recall. Thêm cả R8/R9 thì chín request/response hashes và 19 raw payload đều khớp; tổng số quote exact là 16/19, có issue lịch sử là 15/19. Các mẫu số trộn task/prompt và có nhiều clause từ cùng source nên không dùng để so sánh prompt.

Checkpoint `checkpoint-fe7722aaf0d147c5832dbba35cc668b8` chỉ nạp model input và bảy proposal để reviewer có thể mở lại; event LOAD_KNOWN_DEVELOPMENT_PROPOSALS, actor AGENT_TECHNICAL_SMOKE_TEST, provenance PREPARED_FIXTURE. Không có APPROVE/CORRECT hoặc expert label mới. Kiểm lại trước/sau: 37 nghiệm, P011 đứng đầu theo SYNC_FIRST, input optimizer không đổi. Kết quả này chứng minh gate bảo toàn mô hình trước review, chưa chứng minh model tự tạo được phân hoạch đáng tin.

Gói source-only mới của G10 vẫn khớp hash. Đối chiếu text xác nhận hai request R8/R9 không chứa requirement từ Equipment Loan/Room Scheduling. Exposure ledger của study là snapshot bảy run trước freeze; hai run phát triển bổ sung không được gọi là inference trên study. Các file architecture/development-task-check và checkpoint giữ local, không stage vào Git.
