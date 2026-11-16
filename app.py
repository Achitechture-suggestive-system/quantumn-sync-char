"""Streamlit entrypoint for the local EQCR + QAME MVP."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone

import streamlit as st

from eqcr.fixture import get_fixture
from eqcr.drawio_export import architecture_graph_to_drawio
from eqcr.ollama import (
    OllamaError,
    apply_proposals_to_fixture,
    list_models,
    propose_responsibilities,
)
from eqcr.pipeline import run_pipeline, validate_project_package
from eqcr.project_io import load_project_json
from eqcr.review import (
    apply_artifact_review,
    apply_constraint_edit,
    apply_evidence_relation_edit,
    apply_responsibility_edit,
    artifact_diff,
    replay_artifact_review_decisions,
)
from eqcr.traceability import refresh_traceability_artifact
from eqcr.p2_review import apply_tutor_human_review
from eqcr.p2_protocol import (
    RELATION_PREDICATES,
    build_blind_annotation_template,
    lock_blind_annotation,
    verify_blind_annotation_lock,
)
from eqcr.tutor_support import get_tutor_support_fixture
from eqcr.storage import (
    list_snapshots,
    load_snapshot,
    make_export_zip,
    new_run_id,
    save_run,
    save_snapshot,
)


st.set_page_config(page_title="EQCR + QAME MVP", page_icon="🧩", layout="wide")
st.markdown(
    """
    <style>
      :root {
        --paper: #f2efe7;
        --surface: #fbfaf6;
        --ink: #203136;
        --muted: #617174;
        --rule: #d4d0c5;
        --teal: #28665f;
        --copper: #b65d3c;
      }
      .stApp { background: var(--paper); color: var(--ink); }
      [data-testid="stAppViewContainer"] main {
        background-image: radial-gradient(ellipse at 90% 0%, rgba(40,102,95,.07), transparent 36%);
      }
      .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 4rem; }
      h1, h2, h3 { color: var(--ink); font-family: Georgia, "Times New Roman", serif; }
      h1 { font-size: clamp(2.1rem, 4vw, 3.25rem) !important; letter-spacing: -.045em; line-height: 1.04 !important; }
      h2 { letter-spacing: -.025em; }
      p, label, [data-testid="stCaptionContainer"] { color: var(--muted); }
      [data-testid="stMarkdownContainer"] code, code {
        color: #8f482f; background: #e8e3d8; border-radius: 2px; padding: .13rem .32rem;
      }
      [data-testid="stTabs"] [role="tablist"] { gap: .35rem; border-bottom: 1px solid var(--rule); }
      [data-testid="stTabs"] button[role="tab"] {
        color: var(--muted); border-radius: 2px 2px 0 0; padding: .65rem 1rem;
      }
      [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--teal); background: rgba(40,102,95,.07); border-bottom: 2px solid var(--teal);
      }
      div.stButton > button, div.stDownloadButton > button, button[kind="primary"] {
        border-radius: 3px; border: 1px solid var(--ink); min-height: 2.7rem;
        font-weight: 600; transition: background-color .15s ease, transform .15s ease;
      }
      div.stButton > button:hover, div.stDownloadButton > button:hover {
        border-color: var(--teal); color: var(--teal); transform: translateY(-1px);
      }
      [data-testid="stDataFrame"], [data-testid="stJson"] {
        border: 1px solid var(--rule); border-radius: 3px; background: var(--surface);
      }
      [data-testid="stAlert"] { border-radius: 3px; }
      [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
        background: var(--surface); border-radius: 3px; border-color: var(--rule);
      }
      .workbench-mark {
        display: flex; justify-content: space-between; gap: 1rem; margin: 0 0 1.1rem;
        padding: .55rem 0; border-top: 2px solid var(--copper); border-bottom: 1px solid var(--rule);
        color: var(--muted); font: 600 .68rem/1.4 "Trebuchet MS", sans-serif;
        letter-spacing: .13em; text-transform: uppercase;
      }
      @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition-duration: .01ms !important; scroll-behavior: auto !important; }
      }
    </style>
    <div class="workbench-mark"><span>Requirements lab · case study</span><span>Local / evidence-led / reviewable</span></div>
    """,
    unsafe_allow_html=True,
)
st.title("EQCR + QAME — Architecture Quantum Review")
st.caption(
    "Requirements-based case studies. Candidate groups are reviewable proposals; runtime deployability is not verified and quality targets are not measured."
)

for key, value in {
    "fixture": None,
    "run_fixture": None,
    "pending_model_fixture": None,
    "artifacts": None,
    "run_id": None,
    "run_dir": None,
    "snapshot_version": 0,
    "ollama_models": [],
    "ollama_proposals": None,
    "p2_blind_annotation_lock": None,
    "notice": None,
    "review_preview": None,
    "responsibility_preview": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

input_tab, evidence_tab, quantum_tab, review_tab = st.tabs(
    ["Input", "Evidence & Constraints", "Quantum & Contracts", "Human Review & Validation"]
)


def _save_current() -> None:
    artifacts = st.session_state.artifacts
    if not artifacts:
        return
    artifacts["metadata"]["run_id"] = st.session_state.run_id
    run_dir = save_run(st.session_state.run_id, artifacts)
    st.session_state.run_dir = str(run_dir)


def _show_json(title: str, payload: object) -> None:
    st.subheader(title)
    st.json(payload, expanded=False)


def _refresh_artifact_metadata_assertion(artifacts: dict) -> None:
    artifacts["validation_report"]["assertions"]["all_artifacts_have_provenance_and_verification_status"] = all(
        isinstance(payload.get("artifact_metadata"), dict)
        and bool(payload["artifact_metadata"].get("provenance", {}).get("kind"))
        and bool(payload["artifact_metadata"].get("verification_status"))
        and bool(payload["artifact_metadata"].get("verification_scope"))
        for payload in artifacts.values()
        if isinstance(payload, dict)
    )


def _attach_review_request(artifacts: dict, request: dict, source_artifact: str) -> None:
    artifacts["review_request"] = deepcopy(request)
    artifacts["review_request"]["artifact_metadata"] = {
        "provenance": {
            "kind": "HUMAN_REVIEW_REQUEST",
            "execution_mode": artifacts["metadata"]["execution_mode"],
            "source_artifacts": [source_artifact],
        },
        "verification_status": "PASS",
        "verification_scope": "Request fields and audit source are recorded; semantic correctness is not established by the request.",
    }
    _refresh_artifact_metadata_assertion(artifacts)


def _attach_ollama_proposals(artifacts: dict, proposal_data: dict) -> None:
    proposal_artifact = deepcopy(proposal_data)
    proposal_artifact["artifact_metadata"] = {
        "provenance": {
            "kind": proposal_data.get("provenance", "LOCAL_OLLAMA_UNVERIFIED"),
            "execution_mode": artifacts["metadata"]["execution_mode"],
            "source_artifacts": ["raw_requirements"],
            "model": proposal_data.get("model"),
            "prompt_version": proposal_data.get("prompt_version"),
            "input_sha256": proposal_data.get("input_sha256"),
        },
        "verification_status": proposal_data.get("status", "REVIEW_REQUIRED"),
        "verification_scope": "Structured output, IDs, citation resolution, and exact source spans only; model semantics remain unverified.",
    }
    artifacts["ollama_proposals"] = proposal_artifact
    refresh_traceability_artifact(artifacts)
    _refresh_artifact_metadata_assertion(artifacts)


def _start_run(fixture: dict, execution_mode: str) -> None:
    artifacts = run_pipeline(fixture, execution_mode=execution_mode)
    if st.session_state.ollama_proposals:
        _attach_ollama_proposals(artifacts, st.session_state.ollama_proposals)
    run_id = new_run_id()
    artifacts["metadata"]["run_id"] = run_id
    st.session_state.artifacts = artifacts
    st.session_state.run_fixture = fixture
    st.session_state.run_id = run_id
    st.session_state.snapshot_version = 1
    run_dir = save_run(run_id, artifacts)
    save_snapshot(run_id, "v1", artifacts)
    st.session_state.run_dir = str(run_dir)
    if (
        execution_mode == "OFFLINE_FIXTURE"
        and fixture.get("fixture_label") == "PRECOMPUTED"
        and fixture.get("responsibility_provenance", "PRECOMPUTED") == "PRECOMPUTED"
    ):
        st.session_state.notice = "Offline fixture completed. Its inputs are PRECOMPUTED; all derived outputs remain reviewable."
    elif execution_mode == "OFFLINE_FIXTURE":
        st.session_state.notice = "Deterministic run completed from the frozen source input and reviewed revisions."
    elif execution_mode == "STRUCTURED_INPUT":
        st.session_state.notice = "Structured project input completed the deterministic pipeline; derived outputs remain reviewable."
    else:
        st.session_state.notice = "Model-assisted fixture completed. Citations passed structural checks; semantics remain REVIEW_REQUIRED."


def _prepare_responsibility_revision(artifacts: dict, fixture: dict, **edit: str):
    updated_fixture, decision, revision = apply_responsibility_edit(fixture, artifacts, **edit)
    updated_fixture["constraints"] = deepcopy(artifacts["constraints"]["items"])
    updated = run_pipeline(
        updated_fixture,
        constraints_override=artifacts["constraints"]["items"],
        decisions=artifacts["decisions"]["items"] + [decision],
        revisions=artifacts["revisions"]["items"] + [revision],
        execution_mode=artifacts["metadata"]["execution_mode"],
    )
    updated = replay_artifact_review_decisions(updated)
    updated["metadata"].update(artifacts["metadata"])
    updated["metadata"]["responsibility_provenance"] = updated_fixture["responsibility_provenance"]
    if artifacts.get("ollama_proposals"):
        _attach_ollama_proposals(updated, artifacts["ollama_proposals"])
    return updated_fixture, updated, decision, revision


with input_tab:
    st.subheader("Choose a requirements-based case")
    st.write(
        "Load PetClinic for the frozen baseline or Tutor Support for the P2 case, then inspect sources and proposals before review."
    )
    structured_template = get_fixture()
    structured_template["fixture_label"] = "USER_SUPPLIED"
    structured_template["fixture_note"] = "Editable structured project package template; review all supplied semantics."
    structured_template["responsibility_provenance"] = "USER_SUPPLIED_REVIEW_REQUIRED"
    st.download_button(
        "Download structured project JSON template",
        data=json.dumps(structured_template, ensure_ascii=False, indent=2),
        file_name="eqcr_project_package_template.json",
        mime="application/json",
    )
    structured_upload = st.file_uploader("Optional: load a structured project package (JSON)", type=["json"])
    if st.button("Load structured project JSON", disabled=structured_upload is None):
        try:
            candidate_fixture = load_project_json(structured_upload.getvalue())
            candidate_fixture.setdefault("fixture_label", "USER_SUPPLIED")
            candidate_fixture.setdefault("fixture_note", "User-supplied structured project package; semantics remain reviewable.")
            candidate_fixture.setdefault("responsibility_provenance", "USER_SUPPLIED_REVIEW_REQUIRED")
            validate_project_package(candidate_fixture)
            st.session_state.fixture = candidate_fixture
            st.session_state.run_fixture = None
            st.session_state.pending_model_fixture = None
            st.session_state.artifacts = None
            st.session_state.run_id = None
            st.session_state.run_dir = None
            st.session_state.snapshot_version = 0
            st.session_state.ollama_proposals = None
            st.session_state.review_preview = None
            st.session_state.responsibility_preview = None
            st.session_state.notice = "Structured project JSON passed schema and reference checks; semantic decisions remain review-required."
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
            st.error(f"Could not load structured project JSON: {exc}")
    load_col, tutor_col, run_col, ollama_col = st.columns(4)
    if load_col.button("Load PetClinic demo data", width="stretch"):
        st.session_state.fixture = get_fixture()
        st.session_state.run_fixture = None
        st.session_state.pending_model_fixture = None
        st.session_state.artifacts = None
        st.session_state.run_id = None
        st.session_state.run_dir = None
        st.session_state.snapshot_version = 0
        st.session_state.ollama_proposals = None
        st.session_state.p2_blind_annotation_lock = None
        st.session_state.review_preview = None
        st.session_state.responsibility_preview = None
        st.session_state.notice = "Loaded the PRECOMPUTED PetClinic mini-case input."
    if tutor_col.button("Load Tutor Support P2 case", width="stretch"):
        st.session_state.fixture = get_tutor_support_fixture()
        st.session_state.run_fixture = None
        st.session_state.pending_model_fixture = None
        st.session_state.artifacts = None
        st.session_state.run_id = None
        st.session_state.run_dir = None
        st.session_state.snapshot_version = 0
        st.session_state.ollama_proposals = None
        st.session_state.p2_blind_annotation_lock = None
        st.session_state.review_preview = None
        st.session_state.responsibility_preview = None
        st.session_state.notice = "Loaded the original Tutor Support P2 requirements case."
    is_tutor_case = bool(
        st.session_state.fixture
        and st.session_state.fixture.get("raw_requirements", {}).get("case_id") == "TUTOR-SUPPORT-P2-01"
    )
    if run_col.button(
        "Run offline fixture",
        type="primary",
        width="stretch",
        disabled=is_tutor_case,
    ):
        if st.session_state.fixture is None:
            st.session_state.fixture = get_fixture()
        execution_mode = "OFFLINE_FIXTURE" if st.session_state.fixture.get("fixture_label") == "PRECOMPUTED" else "STRUCTURED_INPUT"
        _start_run(st.session_state.fixture, execution_mode)
    if ollama_col.button("Check local Ollama models", width="stretch"):
        try:
            st.session_state.ollama_models = list_models()
            st.session_state.notice = (
                f"Found {len(st.session_state.ollama_models)} local model(s)."
                if st.session_state.ollama_models
                else "Ollama is reachable, but no local models are installed."
            )
        except OllamaError as exc:
            st.session_state.notice = str(exc)

    if st.session_state.notice:
        st.info(st.session_state.notice)
    if st.session_state.fixture is not None:
        st.markdown(
            f"**Input status:** `{st.session_state.fixture.get('fixture_label', 'USER_SUPPLIED')}` · "
            "requirements-only · no source code supplied"
        )
        _show_json("Raw requirements, workflow, and scenarios", st.session_state.fixture["raw_requirements"])
        blind_lock_valid = True
        if is_tutor_case:
            blind_lock = st.session_state.p2_blind_annotation_lock
            blind_lock_valid = verify_blind_annotation_lock(
                st.session_state.fixture["raw_requirements"], blind_lock
            )
            if blind_lock_valid:
                lock_info = blind_lock["lock"]
                st.success(
                    f"Source-only annotation locked at {lock_info['locked_at']} · "
                    f"reviewer {lock_info['reviewer_id']} · SHA-256 {lock_info['annotation_sha256']}"
                )
                st.download_button(
                    "Download locked blind annotation",
                    data=json.dumps(blind_lock, ensure_ascii=False, indent=2),
                    file_name="P2_BLIND_ANNOTATION_LOCK.json",
                    mime="application/json",
                )
            else:
                st.info(
                    "Complete and lock the source-only annotation first. Model proposals and their review remain hidden until the app records its timestamp and content hash."
                )
                blind_template = build_blind_annotation_template(st.session_state.fixture["raw_requirements"])
                blind_input_key = f"p2_blind_annotation_{blind_template['source_bundle_sha256'][:12]}"
                blind_annotation_text = st.text_area(
                    "Source-only annotation JSON (0..N roles per FR; attest source-only work and no prior model-output exposure)",
                    value=json.dumps(blind_template, ensure_ascii=False, indent=2),
                    height=420,
                    key=blind_input_key,
                )
                if st.button("Lock source-only annotation before model review", type="primary"):
                    try:
                        submitted_annotation = json.loads(blind_annotation_text)
                        st.session_state.p2_blind_annotation_lock = lock_blind_annotation(
                            st.session_state.fixture["raw_requirements"],
                            submitted_annotation,
                        )
                        st.session_state.notice = "Source-only annotation locked. Proposals can now be generated and reviewed in this session."
                        st.rerun()
                    except (json.JSONDecodeError, ValueError, TypeError) as exc:
                        st.error(f"Could not lock the source-only annotation: {exc}")
    else:
        st.info("Choose PetClinic demo data, the Tutor Support P2 case, or a structured JSON package to inspect an input.")

    if st.session_state.ollama_models:
        preferred = next(
            (m for m in ("qwen3:4b", "qwen3.5:4b", "qwen3.5:9b") if m in st.session_state.ollama_models),
            st.session_state.ollama_models[0],
        )
        model = st.selectbox(
            "Local proposal model (proposals always need human review)",
            st.session_state.ollama_models,
            index=st.session_state.ollama_models.index(preferred),
        )
        blind_lock_valid = (
            not is_tutor_case
            or verify_blind_annotation_lock(
                st.session_state.fixture["raw_requirements"],
                st.session_state.p2_blind_annotation_lock,
            )
        )
        if st.button("Run local Ollama proposals", disabled=not blind_lock_valid):
            if st.session_state.fixture is None:
                st.session_state.fixture = get_fixture()
            with st.spinner("Waiting for the local model..."):
                try:
                    proposal_data = propose_responsibilities(
                        st.session_state.fixture["raw_requirements"],
                        model,
                        blind_annotation_lock=st.session_state.p2_blind_annotation_lock if is_tutor_case else None,
                    )
                    st.session_state.ollama_proposals = proposal_data
                    st.session_state.notice = "LLM proposals received; source IDs were resolved to exact input spans. Semantic review is still required."
                    if st.session_state.artifacts:
                        _attach_ollama_proposals(st.session_state.artifacts, proposal_data)
                        _save_current()
                except OllamaError as exc:
                    st.session_state.notice = str(exc)
        if st.session_state.ollama_proposals and blind_lock_valid:
            proposal_data = st.session_state.ollama_proposals
            st.caption(
                f"Model `{proposal_data['model']}` · prompt `{proposal_data['prompt_version']}` · "
                f"input SHA-256 `{proposal_data['input_sha256']}` · all semantics remain review-required."
            )
            _show_json(
                "Responsibility coverage (zero, one, or multiple model candidates per FR)",
                {
                    "counts": proposal_data.get("proposal_coverage_by_requirement", {}),
                    "uncovered_requirement_ids": proposal_data.get("uncovered_requirement_ids", []),
                    "optimizer_cap": 8,
                },
            )
            _show_json(
                "Context normalization proposals",
                {
                    "context_summary": proposal_data["context_summary"],
                    "status": proposal_data["context_status"],
                    "normalized_requirements": proposal_data["normalized_requirements"],
                },
            )
            _show_json("Responsibility proposals", proposal_data["proposals"])
            _show_json(
                "Typed evidence proposals — not applied to evidence",
                {
                    "references_valid": proposal_data["evidence_proposals_valid"],
                    "items": proposal_data["evidence_proposals"],
                },
            )
            _show_json(
                "Boundary hypotheses — not applied to optimizer candidates",
                {
                    "references_valid": proposal_data["boundary_hypotheses_valid"],
                    "items": proposal_data["boundary_hypotheses"],
                },
            )
            st.caption(
                "The app resolves cited IDs to exact input spans. Structural reference checks do not establish "
                "that a relation or boundary hypothesis is semantically correct."
            )
            with st.expander("Prompt and schema audit record"):
                st.json(
                    {
                        "model": proposal_data["model"],
                        "response_model": proposal_data["response_model"],
                        "prompt_version": proposal_data["prompt_version"],
                        "input_sha256": proposal_data["input_sha256"],
                        "generation_parameters": proposal_data["generation_parameters"],
                        "output_schema": proposal_data["output_schema"],
                    },
                    expanded=False,
                )
            if st.session_state.ollama_proposals.get("can_apply_to_fixture"):
                if st.button("Use these proposals for a candidate run"):
                    try:
                        st.session_state.pending_model_fixture = apply_proposals_to_fixture(
                            st.session_state.fixture or get_fixture(), st.session_state.ollama_proposals
                        )
                        st.session_state.notice = "Proposals are ready as review-required inputs; run the model-assisted pipeline when ready."
                        st.rerun()
                    except OllamaError as exc:
                        st.error(str(exc))
            else:
                st.warning("The model output has invalid/duplicate citations or exceeds the exact optimizer cap. It cannot be sent to optimization until corrected or reduced in Human Review.")
                if is_tutor_case and st.button("Prepare Tutor case for human corrections"):
                    st.session_state.pending_model_fixture = deepcopy(st.session_state.fixture)
                    st.session_state.notice = (
                        "The model set is incomplete or ambiguous. Prepared placeholders remain unchanged; "
                        "a reviewer must correct every missing/invalid responsibility before using this candidate."
                    )
                    st.rerun()
    if st.session_state.pending_model_fixture is not None:
        if st.session_state.pending_model_fixture.get("responsibility_provenance") == "LOCAL_OLLAMA_UNVERIFIED":
            st.success(
                "Source-checked responsibility set ready for a candidate run. Evidence and boundary proposals remain "
                "separate; every model-derived semantic decision stays REVIEW_REQUIRED."
            )
        else:
            st.warning(
                "This review run still contains prepared placeholders, not model responsibilities. "
                "Use Human Review to correct missing or ambiguous rows before interpretation."
            )
        if st.button("Run with these LLM proposals"):
            execution_mode = "P2_LOCAL_LLM" if is_tutor_case else "OLLAMA_ASSISTED"
            _start_run(st.session_state.pending_model_fixture, execution_mode)
            st.rerun()
    if not st.session_state.ollama_models and st.session_state.fixture is not None:
        st.caption("Optional: install and start Ollama, then check for models. Offline fixture does not require it.")

    artifacts = st.session_state.artifacts
    if artifacts:
        snapshot_exports = {
            f"snapshots/{version}.json": load_snapshot(st.session_state.run_id, version)
            for version in list_snapshots(st.session_state.run_id)
        }
        st.success(
            f"Run `{st.session_state.run_id}` · status `{artifacts['validation_report']['status']}` · "
            f"saved under `{st.session_state.run_dir}`"
        )
        st.download_button(
            "Download all run artifacts (ZIP)",
            data=make_export_zip(artifacts, extra=snapshot_exports),
            file_name=f"{st.session_state.run_id}-artifacts.zip",
            mime="application/zip",
        )
        st.download_button(
            "Download validation report (JSON)",
            data=json.dumps(artifacts["validation_report"], ensure_ascii=False, indent=2),
            file_name="validation_report.json",
            mime="application/json",
        )

with evidence_tab:
    artifacts = st.session_state.artifacts
    if artifacts:
        left, right = st.columns(2)
        with left:
            _show_json("Evidence records", artifacts["evidence"])
        with right:
            _show_json("Constraints and detected conflicts", artifacts["constraints"])
        st.caption("Policy origin is shown per constraint. UNKNOWN and SCOPED_ABSENT are separate evidence states.")
    else:
        st.info("Run the offline fixture to see evidence and constraint records.")

with quantum_tab:
    artifacts = st.session_state.artifacts
    if artifacts:
        st.subheader("Candidate optimization")
        partitions = artifacts["partitions"]
        if partitions.get("solver_backend") == "CP_SAT":
            st.write(
                f"CP-SAT proved the declared objective minimum J = **{partitions['objective_minimum']}**; "
                f"**{partitions['optimal_candidate_count']}** optimal candidates are reported. "
                f"The complete optimal set was enumerated: **{partitions['optimal_candidate_set_complete']}**."
            )
            st.caption("The feasible set was not exhaustively enumerated; the result is not an architecture recommendation.")
        else:
            st.write(
                f"Enumerated **{partitions['enumerated_partition_count']}** set partitions; "
                f"**{partitions['feasible_candidate_count']}** satisfy active hard constraints; "
                f"**{partitions['optimal_candidate_count']}** tie at J = {partitions['objective_minimum']}."
            )
        st.caption(partitions["interpretation"])
        st.dataframe(partitions["optimal_candidates"], width="stretch", hide_index=True)
        st.subheader("Selected display candidate — proposed, not verified")
        st.json(artifacts["quanta"], expanded=False)

        architecture_graph = artifacts["quanta"]["architecture_graph"]
        graph_lines = ["digraph architecture {", "  rankdir=TB;", '  graph [fontname="Arial"];', '  node [shape=box, fontname="Arial"];']
        for node in architecture_graph["nodes"]:
            node_id = node["id"].replace('"', '\\"')
            node_label = node["label"].replace("Presentation / application tier not specified", "Presentation / app tier not specified")
            label = f'{node_label}\\n{node["status"]}'.replace('"', '\\"')
            style = "dashed" if node["status"] == "UNKNOWN" else "solid"
            shape = "ellipse" if node["layer"] == "ACTOR" else "box"
            graph_lines.append(f'  "{node_id}" [label="{label}", style={style}, shape={shape}];')
        for edge in architecture_graph["edges"]:
            source = edge["from"].replace('"', '\\"')
            target = edge["to"].replace('"', '\\"')
            label = edge["label"].replace('"', '\\"')
            style = "dashed" if edge["status"] in {"UNKNOWN", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"} else "solid"
            graph_lines.append(f'  "{source}" -> "{target}" [label="{label}", style={style}];')
        graph_lines.append("}")
        st.subheader("Quantum and interaction graph")
        st.graphviz_chart("\n".join(graph_lines), width="stretch")
        st.download_button(
            "Download editable Draw.io",
            data=architecture_graph_to_drawio(architecture_graph),
            file_name="eqcr_qame_architecture.drawio",
            mime="application/xml",
            key="download_architecture_drawio",
        )
        graph_left, graph_right = st.columns(2)
        with graph_left:
            node_ids = [item["id"] for item in architecture_graph["nodes"]]
            node_id = st.selectbox("Inspect graph node", node_ids)
            st.json(next(item for item in architecture_graph["nodes"] if item["id"] == node_id), expanded=False)
        with graph_right:
            if architecture_graph["edges"]:
                edge_ids = [item["id"] for item in architecture_graph["edges"]]
                edge_id = st.selectbox("Inspect graph connection", edge_ids)
                st.json(next(item for item in architecture_graph["edges"] if item["id"] == edge_id), expanded=False)
            else:
                st.info("No graph connections are available for this candidate.")
        lower_left, lower_right = st.columns(2)
        with lower_left:
            _show_json("Interaction contract skeleton", artifacts["interactions"])
            interaction_edges = artifacts["interactions"]["edges"]
            interaction_options = [option for edge in interaction_edges for option in edge.get("options", [])]
            if interaction_options:
                st.subheader("Sync / Async options — hypotheses, no protocol selected")
                st.dataframe(
                    [
                        {
                            "mode": option["mode"],
                            "pattern": option["pattern"],
                            "status": option["status"],
                            "condition": option["condition"],
                            "rationale": option["rationale"],
                        }
                        for option in interaction_options
                    ],
                    width="stretch",
                    hide_index=True,
                )
                st.caption(
                    "Both alternatives cite the supplied Pet–Visit scenario and scheduling requirement. "
                    "Their source does not establish the missing timing, consistency, failure, or retry decisions."
                )
        with lower_right:
            _show_json("QAME quality profiles", artifacts["quality_profiles"])
    else:
        st.info("Run the offline fixture to see candidate partitions, quantum groups, and quality traces.")

with review_tab:
    artifacts = st.session_state.artifacts
    is_tutor_run = bool(
        artifacts
        and artifacts.get("raw_requirements", {}).get("case_id") == "TUTOR-SUPPORT-P2-01"
        and st.session_state.ollama_proposals
    )
    has_p2_review = bool(
        artifacts
        and any(
            item.get("decision_type")
            in {"HUMAN_RESPONSIBILITY_REVIEW", "HUMAN_RELATION_REVIEW", "HUMAN_HYPOTHESIS_REVIEW"}
            for item in artifacts.get("decisions", {}).get("items", [])
        )
    )
    if is_tutor_run and not has_p2_review:
        proposal_data = st.session_state.ollama_proposals
        review_template = {
            "responsibilities": [
                {
                    "proposal_id": proposal["id"],
                    "action": "",
                    "reason": "",
                    "source": "",
                    "actor": "",
                }
                for proposal in proposal_data["proposals"]
            ],
            "additional_responsibilities": [],
            "evidence": [
                {
                    "proposal_id": item["id"],
                    "action": "",
                    "reason": "",
                    "source": "",
                    "actor": "",
                    "architecture_implication": "UNRESOLVED",
                    "architecture_rationale": "",
                    "responsibility_pairs": [],
                }
                for item in proposal_data["evidence_proposals"]
            ],
            "boundaries": [
                {
                    "proposal_id": item["id"],
                    "action": "",
                    "reason": "",
                    "source": "",
                    "actor": "",
                }
                for item in proposal_data["boundary_hypotheses"]
            ],
        }
        review_input_key = f"tutor_review_json_{proposal_data['input_sha256'][:12]}"
        with st.expander("Review Tutor Support proposals before evidence can affect optimization", expanded=False):
            st.caption(
                "Each responsibility proposal may be APPROVED, CORRECTED into one or more roles, REJECTED, or DEFERRED. "
                "Add manual responsibility rows only with source citations. Relation approval records business evidence; "
                "optimizer constraints require a separate architecture implication and explicit responsibility pairs."
            )
            review_payload_text = st.text_area(
                "Human review decisions (JSON)",
                value=json.dumps(review_template, ensure_ascii=False, indent=2),
                height=360,
                key=review_input_key,
            )
            if st.button("Apply human review & recompute P2 case", type="primary"):
                try:
                    review_payload = json.loads(review_payload_text)
                    current_fixture = st.session_state.run_fixture or st.session_state.fixture
                    reviewed_fixture, review_decisions = apply_tutor_human_review(
                        current_fixture,
                        proposal_data,
                        review_payload,
                    )
                    previous = st.session_state.artifacts
                    reviewed_artifacts = run_pipeline(
                        reviewed_fixture,
                        decisions=review_decisions,
                        execution_mode="P2_REVIEWED_LOCAL_LLM",
                    )
                    _attach_ollama_proposals(reviewed_artifacts, proposal_data)
                    run_id = st.session_state.run_id or new_run_id()
                    reviewed_artifacts["metadata"]["run_id"] = run_id
                    st.session_state.fixture = reviewed_fixture
                    st.session_state.run_fixture = reviewed_fixture
                    st.session_state.artifacts = reviewed_artifacts
                    st.session_state.run_id = run_id
                    st.session_state.snapshot_version += 1
                    version = st.session_state.snapshot_version
                    run_dir = save_run(run_id, reviewed_artifacts)
                    save_snapshot(run_id, f"v{version}", reviewed_artifacts)
                    st.session_state.run_dir = str(run_dir)
                    st.session_state.notice = (
                        "Recorded the supplied human decisions and recomputed all ten pipeline stages. "
                        "APPROVED remains a review record; quality measurements are still not measured."
                    )
                    st.rerun()
                except (json.JSONDecodeError, ValueError, KeyError, TypeError, AttributeError) as exc:
                    st.error(f"Could not apply P2 review decisions: {exc}")
    if artifacts:
        with st.expander("Traceability graph — structural links and unresolved decisions"):
            st.write(
                f"{artifacts['traceability']['summary']['node_count']} nodes · "
                f"{artifacts['traceability']['summary']['edge_count']} links · "
                f"graph checks {artifacts['traceability']['status']}"
            )
            st.caption(artifacts["traceability"]["note"])
            st.json(artifacts["traceability"], expanded=False)
        if is_tutor_run:
            role_by_id = {item["id"]: item for item in artifacts["responsibilities"]["items"]}
            accepted_relations = [
                item
                for item in artifacts["evidence"]["items"]
                if item.get("review_status") == "APPROVED"
                and item.get("status") == "PRESENT"
                and item.get("relation_annotation_id")
                and item.get("architecture_implication") in {"COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"}
                and item.get("subject_id") in role_by_id
                and item.get("object_id") in role_by_id
            ]
            st.subheader("Revise an approved evidence relation")
            if accepted_relations:
                st.caption(
                    "Choose an FR pair and the reviewed responsibilities that cover those endpoints. "
                    "PRESENT relations need source citations for both FRs and a separate architecture rationale."
                )
                requirement_ids = [item["id"] for item in artifacts["raw_requirements"]["requirements"]]
                with st.form("p2_evidence_revision_form"):
                    evidence_id = st.selectbox("Approved evidence relation", [item["id"] for item in accepted_relations])
                    current_evidence = next(item for item in accepted_relations if item["id"] == evidence_id)
                    responsibility_ids = list(role_by_id)
                    current_relation = next(
                        item for item in artifacts["relation_registry"]["items"]
                        if item["id"] == current_evidence["relation_annotation_id"]
                    )
                    current_subject_role = current_evidence["subject_id"]
                    current_object_role = current_evidence["object_id"]
                    subject_responsibility_id = st.selectbox(
                        "Subject responsibility",
                        responsibility_ids,
                        index=responsibility_ids.index(current_subject_role),
                    )
                    subject_requirement_id = st.selectbox(
                        "Subject requirement",
                        requirement_ids,
                        index=requirement_ids.index(current_relation["subject_requirement_id"]),
                    )
                    relation_predicate = st.selectbox(
                        "Registered architectural relation predicate",
                        [item for item in sorted(RELATION_PREDICATES) if item != "BUSINESS_PRECEDES"],
                        index=[item for item in sorted(RELATION_PREDICATES) if item != "BUSINESS_PRECEDES"].index(current_evidence["predicate"]),
                    )
                    object_responsibility_id = st.selectbox(
                        "Object responsibility",
                        responsibility_ids,
                        index=responsibility_ids.index(current_object_role),
                    )
                    object_requirement_id = st.selectbox(
                        "Object requirement",
                        requirement_ids,
                        index=requirement_ids.index(current_relation["object_requirement_id"]),
                    )
                    architecture_implication = st.selectbox(
                        "Separate architecture implication",
                        ["COLOCATE_CANDIDATE"] if relation_predicate == "SHARES_STATE_OR_INVARIANT" else ["SEPARATE_CANDIDATE"],
                        index=0,
                    )
                    source_requirement_ids = st.multiselect(
                        "Source requirements cited",
                        requirement_ids,
                        default=list(dict.fromkeys([subject_requirement_id, object_requirement_id])),
                    )
                    architecture_rationale = st.text_area(
                        "Architectural candidate rationale",
                        value=current_relation.get("architecture_rationale", ""),
                    )
                    evidence_edit_reason = st.text_area(
                        "Correction reason",
                        value="Correct the accepted relation against the cited requirements.",
                    )
                    evidence_edit_source = st.text_input("Review source", value="P2-HUMAN-REVIEW")
                    evidence_edit_actor = st.text_input("Reviewer identifier", value="reviewer")
                    apply_evidence_edit = st.form_submit_button("Apply correction & Revalidate", type="primary")
                if apply_evidence_edit:
                    try:
                        previous = artifacts
                        base_fixture = st.session_state.run_fixture or st.session_state.fixture
                        revised_fixture, decision, revision = apply_evidence_relation_edit(
                            base_fixture,
                            previous,
                            object_id=evidence_id,
                            subject_requirement_id=subject_requirement_id,
                            predicate=relation_predicate,
                            object_requirement_id=object_requirement_id,
                            source_requirement_ids=source_requirement_ids,
                            subject_responsibility_id=subject_responsibility_id,
                            object_responsibility_id=object_responsibility_id,
                            architecture_implication=architecture_implication,
                            architecture_rationale=architecture_rationale,
                            reason=evidence_edit_reason,
                            source=evidence_edit_source,
                            actor=evidence_edit_actor,
                        )
                        updated = run_pipeline(
                            revised_fixture,
                            decisions=previous["decisions"]["items"] + [decision],
                            revisions=previous["revisions"]["items"] + [revision],
                            execution_mode=previous["metadata"]["execution_mode"],
                        )
                        updated["metadata"].update(previous["metadata"])
                        updated["metadata"]["responsibility_provenance"] = revised_fixture.get(
                            "responsibility_provenance", "LOCAL_OLLAMA_HUMAN_REVIEWED"
                        )
                        _attach_ollama_proposals(updated, st.session_state.ollama_proposals)
                        diff = artifact_diff(previous, updated, exclude={"decisions", "revisions"})
                        revision_record = updated["revisions"]["items"][-1]
                        revision_record["changed_artifacts"] = sorted(
                            set(diff["changed_artifacts"]) | {"decisions", "revisions"}
                        )
                        revision_record["artifact_diff"] = diff["changes"]
                        revision_record["recomputed_artifacts"] = revision_record["invalidated_artifacts"]
                        revision_record["stale_artifacts_after_revalidation"] = []
                        revision_record["revalidation_status"] = updated["validation_report"]["status"]
                        updated["decisions"]["items"][-1]["created_at_utc"] = datetime.now(timezone.utc).isoformat()
                        updated["decisions"]["items"][-1]["result"] = "APPLIED_AND_REVALIDATED"
                        revision_record["created_at_utc"] = datetime.now(timezone.utc).isoformat()
                        unchanged = all(previous.get(key) == updated.get(key) for key in revision_record["unaffected_artifacts"])
                        updated["validation_report"]["assertions"]["unaffected_artifacts_unchanged"] = unchanged
                        updated["validation_report"]["regression_check"] = {
                            "status": "PASS" if unchanged else "FAIL",
                            "checked_artifacts": revision_record["unaffected_artifacts"],
                            "note": "Relation and evidence correction leaves unrelated source and responsibility artifacts unchanged.",
                        }
                        st.session_state.fixture = revised_fixture
                        st.session_state.run_fixture = revised_fixture
                        st.session_state.artifacts = updated
                        st.session_state.snapshot_version += 1
                        version = st.session_state.snapshot_version
                        run_dir = save_run(st.session_state.run_id, updated)
                        save_snapshot(st.session_state.run_id, f"v{version}", updated)
                        st.session_state.run_dir = str(run_dir)
                        st.session_state.notice = (
                            f"Saved v{version}; the reviewed evidence change recomputed optimizer and downstream outputs. "
                            f"Unchanged artifacts: {'PASS' if unchanged else 'FAIL'}."
                        )
                        st.rerun()
                    except (ValueError, KeyError) as exc:
                        st.error(str(exc))
            else:
                st.info("Approve or correct a PRESENT evidence proposal first. Only approved relations can be revised here.")
        st.subheader("Revise a responsibility proposal")
        responsibility_by_id = {item["id"]: item for item in artifacts["responsibilities"]["items"]}
        with st.expander("Edit name, activity, or operation and preview downstream impact"):
            responsibility_id = st.selectbox(
                "Responsibility to revise",
                list(responsibility_by_id),
                key="responsibility_edit_target",
            )
            current_responsibility = responsibility_by_id[responsibility_id]
            with st.form("responsibility_revision_form"):
                edited_name = st.text_input(
                    "Responsibility name",
                    value=current_responsibility["name"],
                    key=f"responsibility_name_{responsibility_id}",
                )
                edited_activity = st.text_input(
                    "Activity",
                    value=current_responsibility["activity"],
                    key=f"responsibility_activity_{responsibility_id}",
                )
                edited_operation = st.text_input(
                    "Operation",
                    value=current_responsibility["operation"],
                    key=f"responsibility_operation_{responsibility_id}",
                )
                responsibility_reason = st.text_area(
                    "Revision reason",
                    value="Human revision after reviewing the requirement and workflow.",
                    key=f"responsibility_reason_{responsibility_id}",
                )
                responsibility_source = st.text_input(
                    "Revision source",
                    value="HUMAN-DEMO-REVIEW",
                    key=f"responsibility_source_{responsibility_id}",
                )
                responsibility_actor = st.text_input(
                    "Reviewer identifier",
                    value="demo-reviewer",
                    key=f"responsibility_actor_{responsibility_id}",
                )
                responsibility_preview_button = st.form_submit_button("Preview responsibility impact")
                responsibility_apply_button = st.form_submit_button(
                    "Apply responsibility revision & Revalidate", type="primary"
                )
            responsibility_request = {
                "object_id": responsibility_id,
                "name": edited_name,
                "activity": edited_activity,
                "operation": edited_operation,
                "reason": responsibility_reason,
                "source": responsibility_source,
                "actor": responsibility_actor,
            }
            if responsibility_preview_button:
                try:
                    base_fixture = st.session_state.run_fixture or st.session_state.fixture or get_fixture()
                    revised_fixture, projected, _, revision_preview = _prepare_responsibility_revision(
                        artifacts, base_fixture, **responsibility_request
                    )
                    stale = revision_preview["invalidated_artifacts"]
                    st.session_state.responsibility_preview = {
                        "request": responsibility_request,
                        "invalidated_artifacts": stale,
                        "preview_status": {name: "STALE" for name in stale},
                        "before": {
                            key: current_responsibility[key]
                            for key in ("name", "activity", "operation")
                        },
                        "after": {key: responsibility_request[key] for key in ("name", "activity", "operation")},
                        "predicted_status": projected["validation_report"]["status"],
                        "predicted_feasible_candidates": projected["partitions"]["feasible_candidate_count"],
                        "note": "Preview only: no decision, fixture input, or snapshot has been saved.",
                    }
                except (ValueError, KeyError) as exc:
                    st.session_state.responsibility_preview = None
                    st.error(str(exc))
            saved_responsibility_preview = st.session_state.responsibility_preview
            if saved_responsibility_preview and saved_responsibility_preview["request"] == responsibility_request:
                st.markdown("**Responsibility impact preview — downstream outputs are stale until revalidation**")
                st.json(saved_responsibility_preview, expanded=False)
            if responsibility_apply_button:
                try:
                    previous = artifacts
                    base_fixture = st.session_state.run_fixture or st.session_state.fixture or get_fixture()
                    revised_fixture, updated, decision, revision = _prepare_responsibility_revision(
                        previous, base_fixture, **responsibility_request
                    )
                    _attach_review_request(updated, responsibility_request, "responsibilities")
                    decision_record = updated["decisions"]["items"][-1]
                    revision_record = updated["revisions"]["items"][-1]
                    unchanged = all(
                        previous.get(key) == updated.get(key)
                        for key in revision_record["unaffected_artifacts"]
                    )
                    updated["validation_report"]["assertions"]["unaffected_artifacts_unchanged"] = unchanged
                    updated["validation_report"]["regression_check"] = {
                        "status": "PASS" if unchanged else "FAIL",
                        "checked_artifacts": revision_record["unaffected_artifacts"],
                        "note": "Responsibility-only feedback must not silently rewrite source context or raw requirements.",
                    }
                    diff = artifact_diff(previous, updated, exclude={"decisions", "revisions"})
                    revision_record["changed_artifacts"] = sorted(
                        set(diff["changed_artifacts"]) | {"decisions", "revisions"}
                    )
                    revision_record["artifact_diff"] = diff["changes"]
                    revision_record["recomputed_artifacts"] = revision_record["invalidated_artifacts"]
                    revision_record["stale_artifacts_after_revalidation"] = []
                    revision_record["revalidation_status"] = updated["validation_report"]["status"]
                    timestamp = datetime.now(timezone.utc).isoformat()
                    decision_record["created_at_utc"] = timestamp
                    decision_record["result"] = "APPLIED_AND_REVALIDATED"
                    revision_record["created_at_utc"] = timestamp
                    st.session_state.artifacts = updated
                    st.session_state.fixture = revised_fixture
                    st.session_state.run_fixture = revised_fixture
                    st.session_state.responsibility_preview = None
                    st.session_state.snapshot_version += 1
                    version = st.session_state.snapshot_version
                    run_dir = save_run(st.session_state.run_id, updated)
                    save_snapshot(st.session_state.run_id, f"v{version}", updated)
                    st.session_state.run_dir = str(run_dir)
                    st.session_state.notice = (
                        f"Saved responsibility revision v{version}; recomputed downstream outputs. "
                        f"Unchanged input check: {'PASS' if unchanged else 'FAIL'}."
                    )
                    st.rerun()
                except (ValueError, KeyError) as exc:
                    st.error(str(exc))

        st.subheader("Record an artifact review outcome")
        st.caption(
            "Approve, Reject, or Defer records a human status without changing structural verification. "
            "Use the constraint form below to revise supported step 04 policies."
        )
        review_choices = {
            "responsibilities": [item["id"] for item in artifacts["responsibilities"]["items"]],
            "evidence": [item["id"] for item in artifacts["evidence"]["items"]],
            "quanta": [item["id"] for item in artifacts["quanta"]["quanta"]],
            "interactions": [item["id"] for item in artifacts["interactions"]["edges"]],
            "quality_profiles": [item["scenario_id"] for item in artifacts["quality_profiles"]["profiles"]],
        }
        available_review_targets = [name for name, ids in review_choices.items() if ids]
        with st.form("artifact_review_form"):
            if available_review_targets:
                review_target = st.selectbox("Artifact to review", available_review_targets)
                review_object_id = st.selectbox("Artifact item", review_choices[review_target])
                review_action = st.selectbox("Review outcome", ["APPROVE", "REJECT", "DEFER"])
                review_reason = st.text_area("Review justification", value="Reviewed during the demo.")
                review_source = st.text_input("Review source", value="HUMAN-DEMO-REVIEW")
                review_actor = st.text_input("Reviewer identifier", value="demo-reviewer")
                record_review = st.form_submit_button("Record artifact review")
            else:
                st.info("No reviewable artifact items are available in this run.")
                record_review = st.form_submit_button("Record artifact review", disabled=True)
        if record_review:
            try:
                updated = apply_artifact_review(
                    artifacts,
                    target_artifact=review_target,
                    object_id=review_object_id,
                    action=review_action,
                    reason=review_reason,
                    source=review_source,
                    actor=review_actor,
                )
                timestamp = datetime.now(timezone.utc).isoformat()
                updated["decisions"]["items"][-1]["created_at_utc"] = timestamp
                updated["revisions"]["items"][-1]["created_at_utc"] = timestamp
                updated["metadata"].update(artifacts["metadata"])
                st.session_state.snapshot_version += 1
                version = st.session_state.snapshot_version
                run_dir = save_run(st.session_state.run_id, updated)
                save_snapshot(st.session_state.run_id, f"v{version}", updated)
                st.session_state.artifacts = updated
                st.session_state.run_dir = str(run_dir)
                st.session_state.review_preview = None
                st.session_state.notice = (
                    f"Recorded {review_action} for {review_target}/{review_object_id} in v{version}. "
                    "Quality measurement and deployment verification remain unchanged."
                )
                st.rerun()
            except (ValueError, KeyError) as exc:
                st.error(str(exc))

        st.subheader("Preview, apply, and revalidate a review decision")
        st.write(
            "Use the sample edit `ADD MUST_LINK(R4,R6)` with object ID `H4` to create a contradiction with H3. "
            "Then use `DISABLE H3` with object ID `H3` as a human correction and revalidate."
        )
        with st.form("review_form"):
            target_step = st.selectbox("Target step", ["04"])
            object_id = st.text_input("Object ID", value="H4")
            old_value = st.text_input("Old value (audit label)", value="ABSENT")
            new_value = st.text_input("New value", value="ADD MUST_LINK(R4,R6)")
            reason = st.text_area("Reason", value="Demo review: test the stated policy and inspect the resulting conflict.")
            source = st.text_input("Source", value="HUMAN-DEMO-REVIEW")
            actor = st.text_input("Reviewer", value="demo-reviewer")
            preview = st.form_submit_button("Preview impact")
            apply = st.form_submit_button("Apply & Revalidate", type="primary")

        request_fields = {
            "target_step": target_step,
            "object_id": object_id,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "source": source,
            "actor": actor,
        }
        if preview:
            try:
                constraints, decision, revision = apply_constraint_edit(
                    artifacts,
                    target_step=target_step,
                    object_id=object_id,
                    old_value=old_value,
                    new_value=new_value,
                    reason=reason,
                    source=source,
                    actor=actor,
                )
                projected = run_pipeline(
                    st.session_state.run_fixture or st.session_state.fixture or get_fixture(),
                    constraints_override=constraints,
                    decisions=artifacts["decisions"]["items"] + [decision],
                    revisions=artifacts["revisions"]["items"] + [revision],
                    execution_mode=artifacts["metadata"]["execution_mode"],
                )
                stale = revision["invalidated_artifacts"]
                st.session_state.review_preview = {
                    "request": request_fields,
                    "invalidated_artifacts": stale,
                    "preview_status": {name: "STALE" for name in stale},
                    "before_status": artifacts["validation_report"]["status"],
                    "predicted_status": projected["validation_report"]["status"],
                    "predicted_feasible_candidates": projected["partitions"]["feasible_candidate_count"],
                    "predicted_optimal_candidates": projected["partitions"]["optimal_candidate_count"],
                    "unaffected_artifacts": revision["unaffected_artifacts"],
                    "note": "Preview only: no decision, snapshot, or artifact has been saved.",
                }
            except (ValueError, KeyError) as exc:
                st.session_state.review_preview = None
                st.error(str(exc))

        saved_preview = st.session_state.review_preview
        if saved_preview and saved_preview["request"] == request_fields:
            st.markdown("**Impact preview — affected outputs are stale until revalidation**")
            st.json(saved_preview, expanded=False)

        if apply:
            try:
                previous = artifacts
                constraints, decision, revision = apply_constraint_edit(
                    previous,
                    target_step=target_step,
                    object_id=object_id,
                    old_value=old_value,
                    new_value=new_value,
                    reason=reason,
                    source=source,
                    actor=actor,
                )
                decisions = previous["decisions"]["items"] + [decision]
                revisions = previous["revisions"]["items"] + [revision]
                updated = run_pipeline(
                    st.session_state.run_fixture or st.session_state.fixture or get_fixture(),
                    constraints_override=constraints,
                    decisions=decisions,
                    revisions=revisions,
                    execution_mode=previous["metadata"]["execution_mode"],
                )
                updated = replay_artifact_review_decisions(updated)
                updated["metadata"].update(previous["metadata"])
                if previous.get("ollama_proposals"):
                    _attach_ollama_proposals(updated, previous["ollama_proposals"])
                _attach_review_request(
                    updated,
                    {
                        "target_step": target_step,
                        "object_id": object_id,
                        "old_value": old_value,
                        "new_value": new_value,
                        "reason": reason,
                        "source": source,
                        "actor": actor,
                    },
                    "constraints",
                )
                diff = artifact_diff(previous, updated, exclude={"decisions", "revisions"})
                changed_artifacts = sorted(set(diff["changed_artifacts"]) | {"decisions", "revisions"})
                updated["revisions"]["items"][-1]["changed_artifacts"] = changed_artifacts
                updated["revisions"]["items"][-1]["artifact_diff"] = diff["changes"]
                updated["revisions"]["items"][-1]["recomputed_artifacts"] = updated["revisions"]["items"][-1]["invalidated_artifacts"]
                updated["revisions"]["items"][-1]["stale_artifacts_after_revalidation"] = []
                updated["revisions"]["items"][-1]["revalidation_status"] = updated["validation_report"]["status"]
                updated["decisions"]["items"][-1]["created_at_utc"] = datetime.now(timezone.utc).isoformat()
                updated["decisions"]["items"][-1]["result"] = "APPLIED_AND_REVALIDATED"
                unchanged = all(previous.get(key) == updated.get(key) for key in ["raw_requirements", "context", "responsibilities", "evidence"])
                updated["validation_report"]["assertions"]["unaffected_artifacts_unchanged"] = unchanged
                updated["validation_report"]["regression_check"] = {
                    "status": "PASS" if unchanged else "FAIL",
                    "checked_artifacts": ["raw_requirements", "context", "responsibilities", "evidence"],
                    "note": "Constraint-only feedback must not silently rewrite input or requirement artifacts.",
                }
                st.session_state.artifacts = updated
                st.session_state.review_preview = None
                version = st.session_state.snapshot_version + 1
                st.session_state.snapshot_version = version
                run_dir = save_run(st.session_state.run_id, updated)
                save_snapshot(st.session_state.run_id, f"v{version}", updated)
                st.session_state.run_dir = str(run_dir)
                st.session_state.notice = f"Saved v{version}; recomputed the full pipeline after the reviewed change. Status: {updated['validation_report']['status']}."
                st.rerun()
            except (ValueError, KeyError) as exc:
                st.error(str(exc))

        artifacts = st.session_state.artifacts
        if st.session_state.notice:
            st.info(st.session_state.notice)
        st.subheader("Validation report")
        st.dataframe(artifacts["validation_report"]["steps"], width="stretch", hide_index=True)
        _show_json("Validation details and limits", artifacts["validation_report"])
        st.subheader("Decision and revision audit")
        st.json({"decisions": artifacts["decisions"], "revisions": artifacts["revisions"]}, expanded=False)
        versions = list_snapshots(st.session_state.run_id)
        if len(versions) > 1:
            earlier_versions = versions[:-1]
            compare_version = st.selectbox("Compare current run with snapshot", earlier_versions)
            earlier = load_snapshot(st.session_state.run_id, compare_version)
            st.subheader(f"Diff: {compare_version} → current")
            st.json(artifact_diff(earlier, artifacts), expanded=False)
        st.caption(f"Snapshots saved in `{st.session_state.run_dir}\\snapshots` (v1 is the initial run).")
    else:
        st.info("Run the offline fixture before submitting a human review decision.")
