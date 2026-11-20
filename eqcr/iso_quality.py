"""Versioned product-quality taxonomy and examples of verification methods."""

from enum import StrEnum


class QualityCharacteristic(StrEnum):
    FUNCTIONAL_SUITABILITY = "Functional suitability"
    PERFORMANCE_EFFICIENCY = "Performance efficiency"
    COMPATIBILITY = "Compatibility"
    INTERACTION_CAPABILITY = "Interaction capability"
    RELIABILITY = "Reliability"
    SECURITY = "Security"
    MAINTAINABILITY = "Maintainability"
    FLEXIBILITY = "Flexibility"
    SAFETY = "Safety"


ISO_EDITION = "ISO/IEC 25010:2023"
ISO_REFERENCE = "https://www.iso.org/standard/78176.html"
REGISTRY_VERSION = "1.0.0"

# Names and clause positions follow ISO. Operational examples are project-authored.
_TERMS = (
    (
        ("Functional completeness", "Cover the required work", "Feature coverage", "Requirements coverage inspection"),
        ("Functional correctness", "Produce the specified outcome", "Business rules and invariants", "Domain acceptance tests"),
        ("Functional appropriateness", "Support the intended task", "Task flow", "Scenario-based task walkthrough"),
    ),
    (
        ("Time behaviour", "Respond or process work within timing goals", "Critical path and queue delay", "Load test with response-time percentiles"),
        ("Resource utilization", "Stay within operating resource limits", "CPU, memory and I/O allocation", "Resource profiling under a defined workload"),
        ("Capacity", "Handle the specified operating limits", "Concurrent sessions and data volume", "Ramp test to the stated capacity limit"),
    ),
    (
        ("Co-existence", "Share an environment without disruption", "Resource contention and interference", "Concurrent workload and interference test"),
        ("Interoperability", "Exchange and interpret data correctly", "Interface and schema compatibility", "Cross-system contract tests"),
    ),
    (
        ("Appropriateness recognizability", "Help users identify whether the product serves their needs", "Discoverability of available tasks", "First-use task-selection study"),
        ("Learnability", "Help users acquire the skills to perform a task", "Onboarding and interaction patterns", "Time to independently complete a new task"),
        ("Operability", "Support effective operation and control", "Feedback and action stability", "Representative task walkthrough"),
        ("User error protection", "Prevent or help users recover from input errors", "Validation and reversible actions", "Faulty-input and recovery task tests"),
        ("User engagement", "Encourage continued interaction", "Feedback and interaction continuity", "User study with retention or engagement observations"),
        ("Inclusivity", "Support people across diverse backgrounds", "Localization and inclusive design", "Evaluation with representative user groups"),
        ("User assistance", "Provide help across different user capabilities", "Assistive technology and help surfaces", "Assistive-technology and guided-task tests"),
        ("Self-descriptiveness", "Make actions and status understandable", "Labels and contextual feedback", "Unaided interpretation test"),
    ),
    (
        ("Faultlessness", "Operate without failure under ordinary conditions", "Defects and normal-path failure rates", "Failure rate under a defined normal workload"),
        ("Availability", "Be usable when required", "Uptime and dependency availability", "Availability observation over a specified window"),
        ("Fault tolerance", "Continue the required operation when faults occur", "Redundancy and isolation", "Fault-injection test with observable service degradation"),
        ("Recoverability", "Restore service and data after failure", "Restore path and recovery point", "Recovery drill measuring RTO and RPO"),
    ),
    (
        ("Confidentiality", "Restrict disclosure to authorized parties", "Access control and data classification", "Authorization and disclosure-control tests"),
        ("Integrity", "Protect information from unauthorized modification", "Write authorization and data validation", "Unauthorized-write rejection tests"),
        ("Non-repudiation", "Support proof that an action or event occurred", "Signed records and event provenance", "Disputed-action evidence verification"),
        ("Accountability", "Relate actions to responsible entities", "Attribution and audit trail", "Actor-to-audit-record trace tests"),
        ("Authenticity", "Verify the identities and origins asserted by entities", "Identity and origin verification", "Authentication and source-verification tests"),
        ("Resistance", "Continue required operation during attacks", "Defensive controls and service resilience", "Review of defensive control effectiveness under a defined threat model"),
    ),
    (
        ("Modularity", "Limit how changes affect other units", "Coupling and module boundaries", "Change propagation analysis"),
        ("Reusability", "Support use of an asset in another context", "Stable interfaces and dependencies", "Reuse trial in a second stated context"),
        ("Analysability", "Determine failure causes or impacts of changes", "Diagnostics and dependency tracing", "Time to diagnose a known incident"),
        ("Modifiability", "Implement change while controlling regressions", "Change surface and regression isolation", "Representative change task and regression suite"),
        ("Testability", "Support setting and executing tests", "Controllability and observability for tests", "Test isolation and reproducibility check"),
    ),
    (
        ("Adaptability", "Support changes in the operating environment", "Configuration and platform changes", "Run agreed tasks across target environments"),
        ("Scalability", "Accommodate changing demand by changing capacity", "Elastic resources and partitioning", "Load ramp while varying capacity"),
        ("Installability", "Install or remove the system in the target environment", "Packaging and installation dependencies", "Clean install and removal in the target environment"),
        ("Replaceability", "Substitute an equivalent product or unit", "Interface stability and migration", "Replacement trial with compatibility checks"),
    ),
    (
        ("Operational constraint", "Keep operation within the specified safety limits", "Safeguards and permitted states", "Check safe operating limits against the safety assessment"),
        ("Risk identification", "Identify conditions that can threaten safety", "Hazard detection and risk records", "Review hazard coverage against operating scenarios"),
        ("Fail safe", "Enter or retain a safe state on failure", "Safe fallback and state transitions", "Verify fallback in a controlled safety test"),
        ("Hazard warning", "Inform operators of hazardous conditions", "Warning path and timeliness", "Verify that warnings arrive within the stated window"),
        ("Safe integration", "Preserve safety when combining or changing products", "Integration safety obligations", "Review safety assumptions and test interfaces"),
    ),
)

ARCHITECTURE_DRIVERS = {
    "ARCH-DEPLOYABILITY": {"name": "Independent deployability", "method": "Independent release and rollback drill"},
    "ARCH-TRANSACTIONAL-CONSISTENCY": {"name": "Transactional consistency", "method": "Invariant and failure-boundary tests"},
    "ARCH-OBSERVABILITY": {"name": "Operational observability", "method": "Incident detection and trace reconstruction drill"},
}


def iso_registry() -> dict:
    characteristics = []
    for index, (name, children) in enumerate(zip(QualityCharacteristic, _TERMS, strict=True), 1):
        clause = f"3.{index}"
        identifier = f"ISO25010-2023-{clause}"
        characteristics.append({
            "id": identifier, "name": name.value, "standard": ISO_EDITION, "clause": clause,
            "reference": ISO_REFERENCE, "provenance": "ISO_TAXONOMY",
            "subcharacteristics": [
                {
                    "id": f"{identifier}.{number}", "characteristic_id": identifier, "name": term,
                    "standard": ISO_EDITION, "clause": f"{clause}.{number}", "reference": ISO_REFERENCE,
                    "provenance": "ISO_TAXONOMY", "operational_interpretation": interpretation,
                    "concerns": [concern], "verification_methods": [method],
                    "guidance_provenance": "PROJECT_AUTHORED_GUIDANCE",
                }
                for number, (term, interpretation, concern, method) in enumerate(children, 1)
            ],
        })
    return {
        "version": REGISTRY_VERSION, "standard": ISO_EDITION, "characteristics": characteristics,
        "architecture_drivers": [
            {"id": identifier, **driver, "provenance": "PROJECT_ARCHITECTURAL_DRIVER"}
            for identifier, driver in ARCHITECTURE_DRIVERS.items()
        ],
    }


def iso_subcharacteristics() -> dict[str, dict]:
    return {
        item["id"]: item
        for characteristic in iso_registry()["characteristics"]
        for item in characteristic["subcharacteristics"]
    }
