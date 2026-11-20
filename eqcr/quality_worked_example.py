"""Prepared equipment reservation case for reproducing the quality decomposition."""

from .fixture import _ref


def get_quality_worked_example(*, explicit_wait_evidence: bool = True) -> dict:
    spec = (
        ("Submit reservation", "submit reservation", "A borrower can submit a reservation request."),
        ("Reserve equipment", "validate availability and reserve equipment", "The system shall provide an equipment reservation outcome."),
        ("Show reservation outcome", "display outcome", "A borrower can see whether a reservation was accepted."),
        ("Publish reservation event", "publish the completed reservation fact", "The system shall provide a completed reservation notice."),
        ("Update reporting", "refresh the utilization report", "A manager can view an equipment utilization report."),
    )
    requirements, workflows, responsibilities = [], [], []
    for number, (name, operation, text) in enumerate(spec, 1):
        fr_id, activity_id = f"FR-{number:02d}", f"ACT-{number:02d}"
        fr_ref = _ref(f"SRC-{fr_id}", text, text)
        workflow_text = f"Activity {number}: {operation}."
        workflow_ref = _ref(activity_id, workflow_text, workflow_text)
        requirements.append({"id": fr_id, "text": text, "source_ref": fr_ref})
        workflows.append({"id": activity_id, "text": workflow_text, "source_ref": workflow_ref})
        responsibilities.append({
            "id": f"R{number}", "name": name, "activity": name, "operation": operation,
            "requirement_ids": [fr_id], "source_refs": [fr_ref, workflow_ref],
            "workflow_activity_ids": [activity_id], "workflow_mapping_status": "MAPPED",
            "provenance": "PREPARED_FIXTURE",
            "decomposition_rationale": "Prepared decomposition of the corresponding workflow activity.",
        })
    nfr = (
        "At busy-hour load, a borrower submits a reservation request. R1, R2 and R3 "
        "process the request and return the reservation result. Time behaviour target: "
        "p95 end-to-end response <= 400 ms."
    )
    report_nfr = "R5 shall provide Recoverability by rebuilding the utilization view after a reporting worker restarts."
    wait = ("The initiating call must receive the completed reservation outcome before continuing. "
            if explicit_wait_evidence else "")
    wait += "It must return the current outcome. Receipt does not need to share the reservation transaction."
    async_source = (
        "Reporting may refresh after reservation completion. Event visibility within 5 minutes is permitted. "
        "The reporting update is independent of the reservation transaction."
    )
    preference = "Prepared what-if policy: prefer separating reporting and reservation writes."
    ledger = ("Serial planning ledger: R2 processing allocation 120 ms; I-RESERVE communication allowance 40 ms. "
              "I-RESERVE caller deadline 160 ms.")
    documents = [
        {"id": "NFR-RESERVATION", "text": nfr, "declared_type": "NFR"},
        {"id": "NFR-REPORT", "text": report_nfr, "declared_type": "NFR"},
        {"id": "SRC-MIXED", "text": "A borrower can view the outcome; p95 response time must be at most 200 ms."},
        {"id": "SRC-WAIT", "text": wait, "declared_type": "FR"},
        {"id": "SRC-EVENT", "text": async_source, "declared_type": "FR"},
        {"id": "SRC-PREFERENCE", "text": preference, "declared_type": "DESIGN_DECISION"},
        {"id": "SRC-BUDGET", "text": ledger, "declared_type": "DESIGN_DECISION"},
    ]
    for document in documents:
        document["provenance"] = "PREPARED_FIXTURE"
    parts = {
        "stimulus_source": "a borrower", "stimulus": "submits a reservation request",
        "environment": "busy-hour load", "artifact": "R1, R2 and R3",
        "response": "return the reservation result", "response_measure": "p95 end-to-end response",
    }
    return {
        "fixture_label": "PREPARED_QUALITY_WORKED_EXAMPLE",
        "fixture_note": "Equipment reservation illustration. No expert reviews, independent labels or executed measurements.",
        "raw_requirements": {
            "case_id": "EQUIPMENT-RESERVATION-QUALITY-DEMO", "context_id": "C0",
            "context_description": "Borrowers reserve shared equipment and management reports reflect completed reservations.",
            "requirements": requirements, "workflows": workflows, "scenarios": [],
        },
        "responsibilities": responsibilities,
        "evidence": [
            {
                "id": "EV-REPORT-INDEPENDENCE", "subject_id": "R4", "object_id": "R5",
                "predicate": "DOMAIN_INVARIANT", "status": "SCOPED_ABSENT", "provenance": "SCOPE_BOUNDARY",
                "source_refs": [_ref("SRC-EVENT", "The reporting update is independent of the reservation transaction.", async_source)],
                "rationale": "Scoped to the reporting update versus the reservation transaction.",
            },
            {
                "id": "EV-DEPLOYABILITY-MISSING", "subject_id": "R2", "object_id": "R5",
                "predicate": "independent_deployment_evidence", "status": "UNKNOWN", "provenance": "UNKNOWN",
                "rationale": "The supplied example has no deployment or release evidence.",
            },
        ],
        "constraints": [{
            "id": "SOFT-REPORT-ISOLATION", "relation": "CANNOT_LINK", "left": "R2", "right": "R5",
            "hardness": "SOFT", "weight": 2, "origin": "WHAT_IF_POLICY",
            "rationale": preference, "source_refs": [_ref("SRC-PREFERENCE", preference, preference)],
        }],
        "quality_decomposition": {
            "source_documents": documents,
            "scenarios": [
                {
                    "id": "QS-RESERVATION", "nfr_id": "NFR-RESERVATION.A01",
                    "parts": {key: _ref("NFR-RESERVATION", value, nfr) for key, value in parts.items()},
                    "target": _ref("NFR-RESERVATION", "<= 400 ms", nfr),
                    "fr_ids": ["FR-01", "FR-02", "FR-03"], "responsibility_ids": ["R1", "R2", "R3"],
                    "subcharacteristic_ids": ["ISO25010-2023-3.2.1"],
                    "measurement_method": "Run a busy-hour workload and measure the end-to-end p95.",
                    "assumptions": ["Busy-hour workload distribution requires elicitation."],
                    "latency_ceiling_ms": 400,
                    "latency_allocations": [
                        {"kind": "RESPONSIBILITY", "subject_id": "R2", "milliseconds": 120,
                         "source_ref": _ref("SRC-BUDGET", "R2 processing allocation 120 ms", ledger)},
                        {"kind": "COMMUNICATION", "subject_id": "I-RESERVE", "milliseconds": 40,
                         "source_ref": _ref("SRC-BUDGET", "I-RESERVE communication allowance 40 ms", ledger)},
                    ],
                },
                {
                    "id": "QS-RECOVERY", "nfr_id": "NFR-REPORT.A01",
                    "parts": {"stimulus": _ref("NFR-REPORT", "after a reporting worker restarts", report_nfr),
                              "response": _ref("NFR-REPORT", "rebuilding the utilization view", report_nfr)},
                    "fr_ids": ["FR-05"], "responsibility_ids": ["R5"],
                    "subcharacteristic_ids": ["ISO25010-2023-3.5.4"],
                    "architecture_driver_ids": ["ARCH-OBSERVABILITY"],
                },
            ],
            "interactions": [
                {
                    "id": "I-RESERVE", "caller": "R1", "callee": "R2", "purpose": "Reserve equipment and obtain its outcome.",
                    "source_refs": [_ref("SRC-WAIT", wait, wait)] if explicit_wait_evidence else [requirements[1]["source_ref"]],
                    "basis_refs": {
                        **({"timing": _ref("SRC-WAIT", "must receive the completed reservation outcome before continuing", wait)}
                           if explicit_wait_evidence else {}),
                        "freshness": _ref("SRC-WAIT", "return the current outcome", wait),
                        "consistency": _ref("SRC-WAIT", "return the current outcome", wait),
                        "atomicity": _ref("SRC-WAIT", "does not need to share the reservation transaction", wait),
                    },
                    "request": "Reservation request and equipment ID", "response": "Reservation outcome",
                    "timing": "IMMEDIATE" if explicit_wait_evidence else "UNKNOWN",
                    "consistency": "STRONG", "freshness": "Return the current reservation outcome",
                    "atomicity": "NOT_REQUIRED", "deadline": _ref("SRC-BUDGET", "I-RESERVE caller deadline 160 ms", ledger),
                    "failure": "Surface the reservation error", "timeout": "Stop waiting at the caller deadline",
                    "operational_overhead": "Budget communication separately if the interaction crosses a boundary",
                },
                {
                    "id": "I-REPORT", "caller": "R4", "callee": "R5", "purpose": "Publish a completed reservation fact.",
                    "source_refs": [_ref("SRC-EVENT", async_source, async_source)],
                    "basis_refs": {
                        "timing": _ref("SRC-EVENT", "Reporting may refresh after reservation completion", async_source),
                        "consistency": _ref("SRC-EVENT", "Event visibility within 5 minutes is permitted", async_source),
                        "freshness": _ref("SRC-EVENT", "Event visibility within 5 minutes is permitted", async_source),
                        "atomicity": _ref("SRC-EVENT", "The reporting update is independent of the reservation transaction", async_source),
                    },
                    "request": "Completed reservation event", "response": "Asynchronous consumption acknowledgement",
                    "timing": "DEFERRED", "consistency": "EVENTUAL", "freshness": "Visibility within 5 minutes",
                    "atomicity": "NOT_REQUIRED", "deadline": _ref("SRC-EVENT", "within 5 minutes", async_source),
                    "message_intent": "EVENT", "delivery": "At least once",
                    "retries": "Bounded retry then hold for operator recovery",
                    "idempotency": "Apply each reservation ID and revision once",
                    "ordering": "Only the newest revision per reservation is applied",
                    "failure": "Retain failed events for inspection and replay",
                    "timeout": "Bound each attempt before retrying",
                    "independent_availability": True,
                    "operational_overhead": "Monitor backlog, replay, and duplicate suppression",
                },
            ],
        },
    }
