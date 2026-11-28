# G10 — protocol đánh giá extraction của Studio

## Bài toán và trạng thái

Phiên bản hiện tại **STUDIO-EVALUATION@2** hỗ trợ một trong hai execution profile: DIRECT / STUDIO-EXTRACT@2 hoặc SENTENCE / STUDIO-EXTRACT@3. Profile được chọn khi prepare, không đổi sau khi thấy output. Matcher atomic link vẫn @1; đây là cập nhật integrity của thí nghiệm, chưa phải kết quả đo nghĩa. [Báo cáo @3](STUDIO_SENTENCE_EXTRACTION.md) vẫn là development smoke, chưa có reference độc lập.

Protocol khóa source, document split, prompt/schema/request hoặc recipe nhiều stage, code, exact model digest, số lượt lặp và quy tắc matching trước khi gọi model. Đích là đánh giá các trường link mà Studio đang trích xuất: QUALITY (ISO/component), INTERACTION (hướng/mode/giao dịch) và SEPARATION (cặp tách). Đây không phải phép đo đầy đủ entailment, trách nhiệm nghiệp vụ, chất lượng kiến trúc hoặc phân loại FR/NFR. Kind FR/NFR đã khai báo là một phần input.

Gói `studio-source-only-v1-20261128` là freeze @1 lịch sử và được giữ nguyên; runner @2 không migrate lock hoặc sửa manifest cũ. Input source format @1 vẫn đọc được, còn annotation/reference phải khóa cho study @2 mới. Cần tạo thư mục freeze mới trên mã đã commit.

Chưa có reference độc lập được nộp. Tất cả semantic metrics hiện vẫn `null`; chưa có inference trên bộ nguồn mới. Mã và tests chuẩn bị đường chạy; tests dùng response/attestation **mô phỏng** trong thư mục tạm, không tạo nhãn chuyên gia cho dữ liệu nghiên cứu.

P2 Tutor có protocol responsibility/relation riêng và vẫn giữ source-only gate của nó. Không dùng lock Studio để mở inference Tutor hoặc đổi fixture P0. Đánh giá từ [bảy run phát triển đã có](STUDIO_LLM_OUTPUT_EVALUATION.md) vẫn là error analysis, không được đổi thành held-out.

## Lượt chuẩn bị @1 đã quan sát — snapshot lịch sử

Sau khi commit/push mã `6c7fabd121d272e56b9bf565cd8b146690242681`, CLI prepare đã tạo `runs/quantum-studio/studies/studio-source-only-v1-20261128/` trên checkout sạch. [CI 46141243324](https://github.com/Achitechture-suggestive-system/quantumn-sync-char/actions/runs/46141243324) thành công trên mã này với 290 tests.

- Study digest: `84e3c3ee4326f3a00168769f16f89f7c44b0dce6c50bbb2474e5ef5c092d77ee`.
- Source digest: `c6d408eb0e8890ccfc2e4cf90c7a428821f3980e457b1695e529f400f6611a8c`.
- Sáu query, 40 row NOT_ANNOTATED, ba repetition dự kiến; source-only package có đúng bốn file và không có claim tham chiếu.
- Freeze ghi hash của bảy extraction request đã tồn tại. Đây là exposure ledger local, không phải sổ mọi lần model đã thấy dữ liệu trên mọi máy.
- `status` và preflight runner thiếu reference cùng giữ `BLOCKED_INDEPENDENT_REFERENCE`, metric null. Check kỹ thuật cài spy trước provider ghi **0 contact**, số extraction request trước/sau vẫn bảy. Không tạo response mới hoặc lock giả để vượt gate. `preflight-check.json` giữ local ở thư mục study.
- Metadata Ollama được đọc riêng: version 0.40.18, exact qwen3:4b digest khớp cấu hình. Đọc metadata không được tính là inference.

Nguồn mới là tài liệu chuẩn bị theo các nhóm khó đã biết; chưa có external corpus hoặc curator độc lập xác nhận độ đại diện. Việc giữ document riêng chưa đủ để kết luận tổng quát hóa ngôn ngữ hoặc domain. Chỉ gửi thư mục `source_only/` của study này cho reviewer, không gửi báo cáo chứa model output trước đó.

## Đơn vị dữ liệu và nguồn mới

`studies/studio_source_only_v1.json` chứa hai document nguyên bản do agent chuẩn bị: Equipment Loan và Room Scheduling. Mỗi document có năm component và tám requirement; tổng 16 requirement, sáu query theo ba tác vụ và **40 unit case/task/source**. Không có allocation, interaction, expected partition hoặc reference label đi kèm. Nguồn là PREPARED_FIXTURE, không phải yêu cầu stakeholder thật hoặc output của local qwen3:4b.

HELD_OUT là phân công dự kiến đối với model được thử, không phải chứng nhận dữ liệu chưa từng xuất hiện trong pretraining. Khi freeze, công cụ:

1. Kiểm schema chỉ nhận component catalog và source requirements, không nhận model output/quality allocations trong source case.
2. Chặn document_group hoặc văn bản trùng giữa DEVELOPMENT/HELD_OUT; chặn văn bản đã biết trong Ticket/OC của repo.
3. Đọc primary request, frame request và request development-probes trong registry local; lưu hash từng file và signature của toàn nguồn/câu đã chuẩn hóa. Chặn held-out trùng cả nguồn hoặc câu trong nguồn. Request đã ghi nhưng chưa nhận response vẫn được xem là potential exposure một cách bảo thủ.
4. Trước mỗi run mới, kiểm lại lịch sử không mất/đổi và chưa có held-out exposure ngoài kế hoạch sau freeze. Không rerun chọn response tốt từ cùng freeze. Cần curator khai báo kiểm paraphrase; chuỗi chuẩn hóa không phát hiện mọi paraphrase, request ngoài registry/máy khác hoặc dữ liệu pretraining. Câu boilerplate trùng cũng có thể bị chặn; không tự bypass bằng cách bỏ file lịch sử.

Ba query mỗi case được chốt theo source IDs. Một unit không được lặp lại ở hai query; repetition là trường riêng. Có thể khai báo DEVELOPMENT trong study để giữ trace, nhưng scorer loại khỏi held-out denominator. Không chia các câu của cùng document sang hai split.

## Gói source-only và nhãn độc lập

Lệnh prepare tạo thư mục mới, không ghi đè study cũ:

```powershell
.\.venv\Scripts\python.exe scripts/studio_evaluation.py prepare `
  --source studies/studio_source_only_v1.json `
  --folder runs/quantum-studio/studies/studio-source-only-v2-sentence `
  --model-digest 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7 `
  --repetitions 3 --method SENTENCE
```

Đường dẫn trên là ví dụ; chọn tên mới nếu đã tồn tại. Checkout phải sạch. Digest trên là model đã quan sát trong các run phát triển, không phải kết quả inference mới; trước lần gọi thật, runner kiểm lại exact digest tại Ollama hiện hành.

Chọn `--method DIRECT` nếu muốn study một lượt @2; mặc định CLI/API vẫn DIRECT. Mỗi study chỉ có một method; chưa đăng ký phép so sánh hai method cùng nguồn trong một run. Không coi hai study chạy nối tiếp sau exposure là một paired experiment hợp lệ.

Chỉ gửi **thư mục `source_only/`** cho mỗi annotator. Thư mục có bốn file: `SOURCE.json`, `README.md`, `ANNOTATION_TEMPLATE.json`, `MANIFEST.json`. Không gửi `requests.json`, `execution.json`, `frozen.json`, repository reports hoặc output model. Validator từ chối file thiếu/thừa, symlink, hash lệch, template có nhãn sẵn hoặc hướng dẫn bị đổi. Hai annotator điền bản riêng **ở ngoài** thư mục đó.

Mỗi row là một unit, phải ghi rationale và chọn:

- `NOT_ANNOTATED`: trạng thái ban đầu; chưa đủ điều kiện khóa.
- `COMPLETE`, `claims=[]`: đã kiểm nguồn và kết luận rõ không có claim hoạt động cho tác vụ này.
- `COMPLETE`, có claims: đã liệt kê các claim thuộc tác vụ trong nguồn.
- `UNRESOLVED`, `claims=[]`: chưa thể kết luận; scorer loại khỏi denominator, không biến thành negative.

Mỗi claim có quote nguyên văn, condition nguyên văn hoặc null và đúng fields của task. QUALITY có characteristic/component_ids; INTERACTION có source/target/mode/local_transaction; SEPARATION có left/right. Claim trùng atomic link bị chặn. Source-only guide giải thích taxonomy và policy chung, không cung cấp đáp án cụ thể cho hai case.

Annotator tự khai ID, thời điểm hoàn tất, provenance HUMAN_SOURCE_ONLY và attest đã làm riêng từ source, chưa xem model output hoặc bài annotator còn lại. Fixture/agent decision và attestation chưa điền bị chặn. Hai ID phải khác nhau. Một annotator hoặc người thứ ba có thể phụ trách adjudication từ nguồn và hai bài đã khóa, cũng chưa xem model output, giải thích mọi unit và khóa reference trước inference. **Đây là lựa chọn protocol của repo**; các trường ID/attestation không xác thực danh tính hay lịch sử truy cập.

```powershell
.\.venv\Scripts\python.exe scripts/studio_evaluation.py lock `
  --folder runs/quantum-studio/studies/studio-source-only-v2-sentence `
  --submission annotator-a.json --output annotator-a.lock.json

# Annotator B làm và khóa riêng theo cùng cách.
.\.venv\Scripts\python.exe scripts/studio_evaluation.py adjudication-template `
  --folder runs/quantum-studio/studies/studio-source-only-v2-sentence `
  --annotation-locks annotator-a.lock.json annotator-b.lock.json `
  --output adjudication.blank.json

# Người adjudicate hoàn tất bản riêng; không dùng template trắng thay quyết định.
.\.venv\Scripts\python.exe scripts/studio_evaluation.py adjudicate `
  --folder runs/quantum-studio/studies/studio-source-only-v2-sentence `
  --annotation-locks annotator-a.lock.json annotator-b.lock.json `
  --submission adjudication.completed.json --output reference.lock.json
```

Các submission/lock là dữ liệu cục bộ của reviewer; không commit credential, thông tin riêng tư hay stage runs hàng loạt. Công cụ chỉ khóa nội dung do người review cung cấp, không tự sinh nhãn hay tự adjudicate khi hai bài khác nhau.

## Gate inference và tái lập

```powershell
.\.venv\Scripts\python.exe scripts/studio_evaluation.py status `
  --folder runs/quantum-studio/studies/studio-source-only-v2-sentence

# Chỉ chạy sau khi reference độc lập hợp lệ đã có.
.\.venv\Scripts\python.exe scripts/studio_evaluation.py run `
  --folder runs/quantum-studio/studies/studio-source-only-v2-sentence `
  --reference reference.lock.json
```

Thiếu reference trả `BLOCKED_INDEPENDENT_REFERENCE`, `link_metrics=null`, `semantic_accuracy=null`; không liên hệ provider. Không có lượt bỏ gate cho fixture trong CLI. Reference cần ít nhất một held-out unit COMPLETE. Trước inference, runner kiểm source/template/request hashes, code hashes, working tree sạch, executable code không đổi từ commit freeze, model digest và runtime. Commit chỉ sửa tài liệu được phép khi mã thực thi vẫn khớp; actual inference SHA vẫn được ghi.

DIRECT freeze exact request từ `build_request`. SENTENCE freeze primary request từ `build_claim_request`, unit registry, frame template không có focus và code của `build_frame_request` trong `execution.json`. Focus thực tế phụ thuộc raw claim, nên **không giả đã biết trước exact secondary request**; verifier tái tạo nó từ raw claim/unit bằng đúng recipe đã khóa. Không dùng reference để tạo request. Hai profile giữ cấu hình adapter của chúng; số repetition ba là pilot, chưa có power analysis. Mỗi repetition/query cần response riêng.

Run mới ở `runs/quantum-studio/evaluations/study-run-…/` ghi Python/platform/package, model/digest/Ollama, reference hash, actual code SHA, query/repetition và thời lượng. Mỗi query giữ hash từng file raw, số provider call và token; scorer kiểm lại từ stage manifest. Thiếu token ở bất kỳ stage nào giữ `tokens=null`, ghi riêng `tokens_observed` và PARTIAL/UNAVAILABLE, không gọi tổng một phần là chi phí đầy đủ hoặc đổi UNKNOWN thành 0. Raw files tiếp tục ở `extractions/`. FAILED giữ call/extraction ID, raw primary và request frame đã gửi; không tạo metric từ trace thiếu hoặc tự resume/retry. Nếu source đã có potential exposure, run mới bị chặn để tránh chọn lọc; thiết kế study tiếp theo phải xử lý exposure công khai.

Scorer yêu cầu đầy đủ mọi query/repetition đã chốt, extraction IDs khác nhau, đúng request/raw payload/hash/model/prompt và thứ tự thời gian. Không chấm run FAILED/thiếu call. Output runtime không tự thành evidence được duyệt trong Studio; runner không sửa model đang mở, không auto-approve hoặc tự sửa hard rules.

Với SENTENCE, kiểm cả primary và từng frame: request theo frozen recipe, response model/done_reason/hash, thứ tự stage, lineage raw claim/raw frame, normalize, duplicate, source/catalog/code và provenance. Missing/unknown unit rows được đếm riêng; không coi chúng là negative đã xử lý. Draft không có model frame hợp lệ không được bịa frame để chấm. Missing claim còn thể hiện qua FN nếu có reference hợp lệ.

Quote SENTENCE được tra từ nguồn qua offset, không phải model-generated citation. `exact_quote_rows` chỉ là kiểm cấu trúc và không dùng để so citation accuracy với DIRECT. Đơn vị annotation/matching vẫn case/task/source; các câu xử lý bên trong không tự thành mẫu độc lập. Hai call cùng model không phải hai annotator hoặc semantic judges.

## Matching và ý nghĩa metric

`SOURCE-TASK-CONDITION-ATOMIC-LINK@1` cố định key gồm case/source/task và condition **đúng chuỗi**; null khác một điều kiện cụ thể:

- QUALITY: `(unit, condition, characteristic, owner_id)`; scope nhiều owner tách thành nhiều atomic links.
- INTERACTION: `(unit, condition, source, target, mode, local_transaction)`; giữ hướng, UNKNOWN và trạng thái transaction.
- SEPARATION: `(unit, condition, min(left,right), max(left,right))`; không hướng.

Quote kiểm structural citation nhưng không đưa toàn quote vào key, để các quote dài/ngắn cùng claim không tự thành hai link khác nhau. Matching không đánh giá đầy đủ frame, tên operation/responsibility, target số, entailment hoặc tương đương ngữ nghĩa của hai cách diễn đạt condition. Chọn boundary condition khác nhau có thể làm exact-match fail dù reviewer thấy tương đương; cần báo hạn chế này và sửa protocol cho study tương lai, không đổi matcher sau khi thấy kết quả.

Với tập prediction P và reference R trên các held-out unit COMPLETE:

```text
TP = |P ∩ R|; FP = |P − R|; FN = |R − P|
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2TP / (2TP + FP + FN)
```

Mẫu số bằng 0 trả null; không coi một tập rỗng là kết quả hoàn hảo. Proposal trùng được deduplicate theo link và báo số duplicate riêng. Units UNRESOLVED/DEVELOPMENT được liệt kê rõ khi loại. Ba repetition dùng cùng reference nên không phải ba bộ case độc lập.

Hai cohort:

1. **raw_projectable_fields:** các field tạo được link hợp lệ trong catalog, có quote/condition phù hợp cấu trúc. Giữ cả mapping có field hoạt động nhưng disposition mâu thuẫn để thấy output raw khác gate.
2. **gate_eligible_fields:** subset không có `proposal_issues`, disposition PROPOSED. Tên này không có nghĩa đã HUMAN_APPROVED hay entailment đúng.

Hàng không project được, source lạ hoặc frame/quote lỗi được đếm riêng, không gọi là true link. Vì raw metric chỉ tính link project được, không đọc precision đó tách khỏi số hàng lỗi và recall. Hàng OUT_OF_SCOPE/AMBIGUOUS có fields rỗng là abstention riêng, không bị gọi là mapping malformed. Các false-hard-policy fields (separation/transaction=true lệch reference) được báo riêng; scorer không thực sự áp dụng chúng thành constraint.

Report có từng repetition, task và document/case; số unit eligible/excluded và agreement về exact link sets giữa hai annotator trước adjudication. Đây là agreement mô tả, không phải chứng minh reference đúng hoặc Cohen kappa trên một universe negative chưa định nghĩa.

Baseline regex dùng `quality_suggestions × component_mentions` nguyên bản cho QUALITY, condition=null. Quy tắc này có thể nhặt cả component bối cảnh; không gọi là oracle. Regex INTERACTION/SEPARATION chưa được hỗ trợ, không giả chúng trả dự đoán âm hoàn hảo. Chưa có cohort human-reviewed, measurement thời gian thao tác reviewer hoặc partition-distance theo reference trong protocol @2; các phần này còn ở G10.

`semantic_accuracy=null` và `architecture_quality=NOT_MEASURED` giữ riêng ngay cả khi có exact-link metrics. Không chuyển F1 của link fields thành độ đúng toàn bộ yêu cầu, architecture quality PASS hoặc independent deployability.

## Kiểm chứng và nguồn phương pháp

Mốc X2 thêm **31 tests** dùng response/attestation mô phỏng: source-only vẫn trắng, thiếu reference không chạm provider, recipe drift dù rehash metadata, cả ba task qua nhiều stage, request/focus/frame/lineage/provenance/timestamp/model bị sửa, bỏ draft, lỗi giữa frame, empty/unknown/duplicate units, quote lặp đúng offset, source format cũ, thiếu token metadata và exposure trước/sau freeze. Nhóm evaluation đạt **57 tests**; đây là validation phần mềm, không phải independent labels hoặc kết quả model mới.

Full regression X2 đạt **343 tests**, compileall và JavaScript syntax qua. Trong vòng kiểm trước đó, 336 tests qua và một probe ASYNC lỗi PermissionError đọc ready; đã sửa riêng ở `19d4e6c` với cleanup constructor và kiểm lại hai mode thật, không tăng timeout giao thức hoặc bỏ assertion. [Bằng chứng và giới hạn artifact tạm](STUDIO_BOUNDARY_EVIDENCE.md#sửa-lỗi-đọc-readiness-trên-windows--28112026).

Audit read-only trên registry local quan sát **64 request files**, **21 signature toàn nguồn/câu** sau chuẩn hóa và không có exact overlap với Equipment Loan/Room Scheduling. Sáu query SENTENCE có lần lượt 8/15/15 và 8/16/16 đoạn xử lý, tổng 78; annotation vẫn có 40 unit case/task/source. Audit không liên hệ provider và không chứng minh không có paraphrase/leakage ngoài registry. Full-source requests, frame requests và 37 development-probe requests được giữ nguyên.

Regression tại mốc X1 có **290 tests** qua, gồm 26 tests mới dùng source/response/attestation giả lập riêng, không phải hai document nghiên cứu mới. Chúng kiểm gate, blinding package, leakage, null denominator, source/model/code/request/response drift, bỏ call, dùng lại response, UNKNOWN, exact direction/transaction/condition, giữ failed trace và luồng đủ các tác vụ. Compileall và diff check qua; tests không cần daemon hoặc credential.

Baltes và cộng sự nhấn mạnh khai báo cấu hình/prompt/traces, chọn metric phù hợp task, lặp thí nghiệm và kiểm output với đánh giá con người. Nguồn được ghim ở **arXiv:2508.15503v8, 18/09/2026**, ghi accepted in Empirical Software Engineering; không tự suy DOI/tập báo cuối. Các cấu trúc lock/matcher và quy trình adjudication ở trên là thiết kế repo, không phải thuật toán được bài này chứng minh. [Bản v8](https://arxiv.org/abs/2508.15503v8) · [Mục 5.3–5.7](https://arxiv.org/html/2508.15503v8)

TraceLLM công bố package gồm splits, prompts và cấu hình; task traceability của bài khác ISO/component/mode của Studio. Dùng làm tham khảo cách công bố thí nghiệm, không nhận F2 của bài làm kết quả nội bộ. [Nhà xuất bản, Data availability](https://link.springer.com/article/10.1007/s00766-026-00460-1). Nguồn S12 về oracle và S10/S21 được đối chiếu trong [source ledger](STUDIO_SOURCE_LEDGER.md).
