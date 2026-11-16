# Reproducibility bundle — schema 1.0.0

## Mục đích và phạm vi

Tải **Download all run artifacts (ZIP)** trong app để lưu một run cùng các snapshot hiện có. ZIP mới chứa `reproducibility_manifest.json` và `checksums.sha256.json`. Manifest dùng schema `EQCR-REPRODUCIBILITY-BUNDLE@1.0.0`.

Manifest ghi case/run ID, execution mode, hash input requirements và source refs, hash annotation lock khi có, hash decisions/revisions, commit và trạng thái working tree, Python/platform, package versions, hash `requirements.txt`, solver backend/các tham số hiện có, model/prompt metadata khi được cung cấp, tổng hợp provenance theo artifact, hash từng member và CI run ID nếu được chạy trong GitHub Actions. Trường source version/license được giữ null hoặc `NOT_RECORDED` nếu không có dữ liệu.

| Nội dung | Provenance được ghi nhận |
|---|---|
| Raw requirements, workflow, scenarios | `SOURCE_REQUIREMENTS`; hash canonical của gói raw và SourceRefs |
| Responsibilities, relations, evidence | Đếm theo `provenance` hiện có; `PREPARED_FIXTURE` không đổi thành LLM output |
| Constraints | Đếm theo `origin` đã ghi trong constraint |
| Partitions, quanta, interactions, quality profiles | `DETERMINISTIC_TRANSFORMATION` hoặc policy/field-level provenance được nêu riêng; xem từng artifact để biết source refs và trạng thái |
| Decisions và revisions | Đếm decision type; bản ghi chi tiết vẫn ở JSON artifact/snapshot |
| LLM/model | Metadata chỉ có khi artifact thực sự chứa proposal; manifest trống không phải bằng chứng đã chạy model |

`checksums.sha256.json` chứa SHA-256 cho mọi ZIP member khác, gồm cả manifest. Manifest `bundle_member_sha256` bao phủ mọi artifact và snapshot, không bao phủ chính manifest hoặc checksum file. Validator kiểm tên member trùng/đường dẫn nguy hiểm, JSON parse, coverage chính xác và các hash.

## Kiểm tra một bundle

PowerShell tại repository root:

```powershell
.\.venv\Scripts\python.exe scripts\validate_artifact_bundle.py "path\to\run-artifacts.zip"
```

Kết quả thành công trả JSON `status=PASS`, schema version, case/run ID và số member được kiểm tra. Đây là kiểm tra toàn vẹn và cấu trúc ZIP; validator không chạy lại optimizer, không tái gọi Ollama, không xác thực chữ ký, danh tính reviewer, quyền sử dụng nguồn, semantic correctness hoặc kiến trúc. ZIP không được ký; người có thể sửa cả artifact và checksum map vẫn có thể tạo một bundle tự nhất quán.

## Giới hạn tái lập

- `requirements.txt` hash và package versions ghi môi trường đã biết, nhưng dependency ranges chưa phải lockfile transitive hoàn chỉnh.
- Không có CI run ID thì trạng thái là `NOT_RECORDED`; nếu có ID, CI outcome cũng chưa được query/verified bởi exporter.
- Source package version, authorship, licensing, model digest, reviewer identity hoặc exposure status không được suy ra khi thiếu input.
- Hashes bảo vệ khỏi sửa đổi vô tình sau export khi checksum map còn đáng tin; không chứng minh nguồn gốc hoặc tính khoa học của dữ liệu.
- LLM/model proposals, prepared fixtures, deterministic transformations, architectural policies và human decisions giữ provenance riêng trong artifact; summary manifest không thay thế nội dung/decision log gốc.
- Bản export chỉ phản ánh trạng thái artifacts/snapshots tại thời điểm tải. Nó không tự động thực hiện lại pipeline hoặc tạo run P2.
