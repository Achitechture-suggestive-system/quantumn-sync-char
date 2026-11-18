# Tutor Support — tài liệu nguồn

- Case ID: `TUTOR-SUPPORT-P2-01`
- Context ID: `C0`
- Context: An original, small Tutor Support requirements case. The package contains requirements and workflows only; it supplies no source code, runtime topology, deployment evidence, or confirmed architecture policy.

Các đoạn trích và offsets bên dưới được giữ nguyên theo SOURCE_DATA.json.

## Yêu cầu chức năng

### FR-01 — source `TUTOR-REQ-FR-01`
Span: `0:71`

> A learner can search the tutor directory by subject and available time.

### FR-02 — source `TUTOR-REQ-FR-02`
Span: `0:70`

> A learner can view a tutor profile, subjects, and listed availability.

### FR-03 — source `TUTOR-REQ-FR-03`
Span: `0:57`

> A tutor can publish and update weekly availability slots.

### FR-04 — source `TUTOR-REQ-FR-04`
Span: `0:62`

> A learner can request a tutoring session in an available slot.

### FR-05 — source `TUTOR-REQ-FR-05`
Span: `0:65`

> A tutor can accept or decline a pending tutoring session request.

### FR-06 — source `TUTOR-REQ-FR-06`
Span: `0:77`

> The learner receives a notice when the tutor accepts or declines the request.

## Hoạt động workflow

### WF-01 — source `TUTOR-WF-01`
Span: `0:68`

> A learner searches the tutor directory by subject and a time window.

### WF-02 — source `TUTOR-WF-02`
Span: `0:74`

> The learner reviews a tutor profile and selects an open availability slot.

### WF-03 — source `TUTOR-WF-03`
Span: `0:81`

> The learner requests the slot; the tutor accepts or declines the pending request.

### WF-04 — source `TUTOR-WF-04`
Span: `0:54`

> The learner receives a notice of the tutor's decision.

## Quality scenarios

### SC-REQUEST-ACK — source `SC-REQUEST-ACK`
Span: `0:271`

> Session request acknowledgement. Stimulus: During a peak period of 50 request submissions per minute, a learner requests an available tutoring slot. Measure: p95 request acknowledgement time at 50 submissions per minute. Target: p95 <= 2 seconds at 50 submissions/minute.

### SC-DECISION-NOTICE — source `SC-DECISION-NOTICE`
Span: `0:253`

> Tutor decision notification. Stimulus: A tutor accepts or declines a pending session request. Measure: percentage of decision notices delivered within 30 seconds. Target: at least 99% of notices delivered within 30 seconds over a rolling 24-hour window.
