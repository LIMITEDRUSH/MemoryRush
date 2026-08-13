import json
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from memoryrush.admission.benchmark import load_benchmark
from memoryrush.admission.models import QualifierKind, QualifierSlot, SupportMatrix
from memoryrush.admission.solver import InclusionMinimalSolver, evaluate_sufficiency


def test_direction1_builder_materializes_frozen_catalog(tmp_path: Path) -> None:
    from scripts.build_direction1_synthetic_benchmark import (
        CATALOG_OPERATOR_MAP,
        build_benchmark,
    )

    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    build_benchmark(first)
    build_benchmark(second)

    assert first.exists()
    assert first.read_bytes() == second.read_bytes()
    assert b"\r" not in first.read_bytes()
    assert sha256(first.read_bytes()).hexdigest() == sha256(second.read_bytes()).hexdigest()

    raw_cases = [json.loads(line) for line in first.read_text(encoding="utf-8").splitlines()]
    cases = load_benchmark(first)
    assert len(cases) == 36
    assert Counter(case.oracle.decision.value for case in cases) == {
        "ADMIT": 20,
        "REJECT": 13,
        "REVIEW": 3,
    }
    assert Counter(case.oracle.label_source for case in cases) == {
        "llm_generated": 27,
        "programmatic_oracle": 9,
    }
    assert Counter(case.provenance.generator_type for case in cases) == {
        "llm_or_agent": 27,
        "programmatic": 9,
    }
    assert {case.case_family.split()[0] for case in cases} == {
        f"F{index:02d}" for index in range(1, 15)
    }
    assert CATALOG_OPERATOR_MAP == {
        "ENTITY_REPLACE": "replace_entity",
        "NUMBER_REPLACE": "replace_quantifier",
        "DATE_REPLACE": "replace_time",
        "NEGATION_FLIP": "flip_negation",
        "MODALITY_STRENGTHEN": "replace_modality",
        "MODALITY_WEAKEN": "replace_modality",
        "CONDITION_DELETE": "delete_condition",
        "SCOPE_EXPAND_QUANTIFIER": "delete_scope",
        "ATTRIBUTION_TRANSFER": "replace_attribution",
        "EVIDENCE_DUPLICATE": "duplicate_evidence",
        "MEANING_PRESERVING_PARAPHRASE": "paraphrase_meaning_preserving",
        "CONDITION_PRESERVING_PARAPHRASE": "paraphrase_condition_preserving",
        "OVERCOMPOSE_UNSUPPORTED_ATOM": "overcompose_unsupported_atom",
    }

    expected_root_keys = {
        "schema_version",
        "case_id",
        "case_family",
        "document",
        "candidate",
        "evidence_spans",
        "oracle",
        "provenance",
    }
    assert all(set(payload) == expected_root_keys for payload in raw_cases)
    high_risk = {"MSG-C014", "MSG-C023", "MSG-C026"}
    by_id = {case.case_id: case for case in cases}
    assert all(
        "high_risk_not_human_gold" in by_id[case_id].oracle.reason_codes
        for case_id in high_risk
    )
    assert all(case.oracle.adjudication_status != "human_gold" for case in cases)
    semantic_shams = {"MSG-C030", "MSG-C031", "MSG-C032"}
    assert all(
        by_id[case_id].oracle.label_source == "llm_generated"
        and by_id[case_id].oracle.adjudication_status == "provisional"
        and "agent_authored_semantic_sham_not_programmatic_oracle"
        in by_id[case_id].oracle.reason_codes
        and by_id[case_id].provenance.generator_type == "llm_or_agent"
        and by_id[case_id].provenance.base_case_id is not None
        and by_id[case_id].provenance.perturbation_operator is not None
        for case_id in semantic_shams
    )
    unsupported_atom = by_id["MSG-C034"]
    assert unsupported_atom.oracle.label_source == "llm_generated"
    assert unsupported_atom.oracle.adjudication_status == "provisional"
    assert unsupported_atom.provenance.generator_type == "llm_or_agent"
    assert (
        "unsupported_atom_non_support_not_mechanically_provable"
        in unsupported_atom.oracle.reason_codes
    )
    deontic = by_id["MSG-C014"]
    assert deontic.oracle.label_source == "llm_generated"
    assert deontic.oracle.adjudication_status == "provisional"
    assert deontic.provenance.generator_type == "llm_or_agent"
    assert "deontic_label_not_mechanically_provable" in deontic.oracle.reason_codes
    assert by_id["MSG-C006"].oracle.support_cells[0].label.value == "insufficient"
    assert by_id["MSG-C020"].oracle.support_cells[0].label.value == "insufficient"


def _write_payloads(path: Path, payloads: list[dict]) -> None:
    path.write_text(
        "\n".join(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for payload in payloads
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _built_payloads(tmp_path: Path) -> list[dict]:
    from scripts.build_direction1_synthetic_benchmark import build_benchmark

    output = tmp_path / "direction1.jsonl"
    build_benchmark(output)
    return [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]


def test_programmatic_relation_rejects_self_consistent_wrong_c006_admit(
    tmp_path: Path,
) -> None:
    payloads = _built_payloads(tmp_path)
    case = next(payload for payload in payloads if payload["case_id"] == "MSG-C006")
    case["oracle"]["decision"] = "ADMIT"
    case["oracle"]["minimal_evidence_sets"] = [["E1"]]
    cell = case["oracle"]["support_cells"][0]
    cell["label"] = "supports"
    cell["supported_qualifiers"] = deepcopy(
        case["candidate"]["atomic_claims"][0]["qualifiers"]
    )
    forged = tmp_path / "forged-c006-admit.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="programmatic relation.*expected decision REJECT"):
        load_benchmark(forged)


def test_frozen_suite_requires_every_registered_programmatic_relation(
    tmp_path: Path,
) -> None:
    payloads = _built_payloads(tmp_path)
    case = next(payload for payload in payloads if payload["case_id"] == "MSG-C006")
    case["oracle"]["label_source"] = "llm_generated"
    case["oracle"]["adjudication_status"] = "provisional"
    case["provenance"]["generator_type"] = "llm_or_agent"
    forged = tmp_path / "missing-registered-relation.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="programmatic relation registry.*missing"):
        load_benchmark(forged)


def test_frozen_suite_rejects_unpaired_programmatic_provenance(tmp_path: Path) -> None:
    payloads = _built_payloads(tmp_path)
    base = next(payload for payload in payloads if payload["case_id"] == "MSG-C005")
    base["oracle"]["label_source"] = "programmatic_oracle"
    base["oracle"]["adjudication_status"] = "synthetic_oracle"
    base["provenance"]["generator_type"] = "programmatic"
    forged = tmp_path / "unpaired-programmatic-base.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="programmatic relation registry.*unregistered"):
        load_benchmark(forged)


def test_frozen_suite_rejects_extra_unregistered_programmatic_case(
    tmp_path: Path,
) -> None:
    payloads = _built_payloads(tmp_path)
    extra = deepcopy(payloads[0])
    extra["case_id"] = "MSG-C999"
    extra["candidate"]["candidate_id"] = "MSG-C999-candidate"
    extra["oracle"]["label_source"] = "programmatic_oracle"
    extra["oracle"]["adjudication_status"] = "synthetic_oracle"
    extra["provenance"]["generator_type"] = "programmatic"
    payloads.append(extra)
    forged = tmp_path / "extra-programmatic-case.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="programmatic relation registry.*unregistered"):
        load_benchmark(forged)


def test_annotation_schema_rejects_duplicate_minimal_evidence_sets() -> None:
    schema_path = (
        Path(__file__).parents[1]
        / "research"
        / "direction_01_minimal_sufficient_grounding"
        / "annotation-schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    minimal_sets = schema["properties"]["oracle"]["properties"][
        "minimal_evidence_sets"
    ]

    assert minimal_sets["uniqueItems"] is True


def test_programmatic_relation_rejects_unregistered_candidate_change(
    tmp_path: Path,
) -> None:
    payloads = _built_payloads(tmp_path)
    case = next(payload for payload in payloads if payload["case_id"] == "MSG-C006")
    case["candidate"]["proposition"] = case["candidate"]["proposition"].replace(
        "South Workshop", "East Workshop"
    )
    claim = case["candidate"]["atomic_claims"][0]
    claim["text"] = claim["text"].replace("South Workshop", "East Workshop")
    claim["qualifiers"][0]["value"] = "East Workshop"
    forged = tmp_path / "forged-c006-transition.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="programmatic relation.*candidate transition"):
        load_benchmark(forged)


def test_programmatic_relation_rejects_changed_frozen_source(
    tmp_path: Path,
) -> None:
    payloads = _built_payloads(tmp_path)
    case = next(payload for payload in payloads if payload["case_id"] == "MSG-C006")
    old = "North Workshop"
    new = "East Workshop"
    document = case["document"]
    document["snapshot_text"] = document["snapshot_text"].replace(old, new)
    document["paragraphs"][0]["text"] = document["paragraphs"][0]["text"].replace(
        old, new
    )
    document["paragraphs"][0]["snapshot_end"] = len(document["snapshot_text"])
    document["source_sha256"] = sha256(
        document["snapshot_text"].encode("utf-8")
    ).hexdigest()
    span = case["evidence_spans"][0]
    span["text"] = span["text"].replace(old, new)
    span["end_char"] = len(span["text"])
    forged = tmp_path / "forged-c006-source.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="programmatic relation.*frozen source"):
        load_benchmark(forged)


def test_programmatic_relation_rejects_joint_base_and_derived_source_change(
    tmp_path: Path,
) -> None:
    payloads = _built_payloads(tmp_path)
    for case_id in ("MSG-C005", "MSG-C006"):
        case = next(payload for payload in payloads if payload["case_id"] == case_id)
        document = case["document"]
        old = document["snapshot_text"]
        new = old.replace("The North Workshop", "The North and South Workshops")
        document["snapshot_text"] = new
        document["paragraphs"][0]["text"] = new
        document["paragraphs"][0]["snapshot_end"] = len(new)
        document["source_sha256"] = sha256(new.encode("utf-8")).hexdigest()
        span = case["evidence_spans"][0]
        span["text"] = new
        span["end_char"] = len(new)
    forged = tmp_path / "joint-source-mutation.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="canonical source digest"):
        load_benchmark(forged)


def test_duplicate_evidence_positive_is_derived_from_base_certificate(
    tmp_path: Path,
) -> None:
    payloads = _built_payloads(tmp_path)
    case = next(payload for payload in payloads if payload["case_id"] == "MSG-C022")
    case["oracle"]["decision"] = "REJECT"
    case["oracle"]["minimal_evidence_sets"] = []
    for cell in case["oracle"]["support_cells"]:
        cell["label"] = "insufficient"
        cell["supported_qualifiers"] = []
    forged = tmp_path / "forged-c022-reject.jsonl"
    _write_payloads(forged, payloads)

    with pytest.raises(ValueError, match="programmatic relation.*expected decision ADMIT"):
        load_benchmark(forged)


def test_direction1_certificates_and_pair_provenance_are_recomputed(tmp_path: Path) -> None:
    from scripts.build_direction1_synthetic_benchmark import SOURCE_BLOCKS, build_benchmark

    output = tmp_path / "direction1.jsonl"
    build_benchmark(output)
    cases = load_benchmark(output)
    by_id = {case.case_id: case for case in cases}

    for case in cases:
        matrix = SupportMatrix(
            candidate=case.candidate,
            evidence_spans=case.evidence_spans,
            cells=case.oracle.support_cells,
        )
        recomputed = {
            solution.selected_span_ids for solution in InclusionMinimalSolver().solve(matrix)
        }
        assert recomputed == set(case.oracle.minimal_evidence_sets), case.case_id
        base_id = case.provenance.base_case_id
        if base_id is not None:
            assert base_id in by_id
            assert by_id[base_id].provenance.base_case_id is None

    for members in SOURCE_BLOCKS.values():
        documents = {by_id[case_id].document.document_id for case_id in members}
        snapshots = {by_id[case_id].document.snapshot_text for case_id in members}
        hashes = {by_id[case_id].document.source_sha256 for case_id in members}
        assert len(documents) == len(snapshots) == len(hashes) == 1, members


def test_direction1_builder_cli_write_and_check(tmp_path: Path) -> None:
    script = Path("scripts/build_direction1_synthetic_benchmark.py")
    output = tmp_path / "direction1.jsonl"

    written = subprocess.run(
        [sys.executable, str(script), "--output", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert written.returncode == 0, written.stderr
    checked = subprocess.run(
        [sys.executable, str(script), "--output", str(output), "--check"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr
    assert "benchmark is canonical" in checked.stdout


def test_qualifier_loss_cases_encode_exact_missing_slots(tmp_path: Path) -> None:
    from scripts.build_direction1_synthetic_benchmark import build_benchmark

    output = tmp_path / "direction1.jsonl"
    build_benchmark(output)
    by_id = {case.case_id: case for case in load_benchmark(output)}
    expected = {
        "MSG-C013": QualifierSlot(QualifierKind.MODALITY, "asserted actual"),
        "MSG-C016": QualifierSlot(QualifierKind.CONDITION, "unrestricted operating conditions"),
        "MSG-C018": QualifierSlot(QualifierKind.SCOPE, "all staff"),
    }

    for case_id, missing_slot in expected.items():
        case = by_id[case_id]
        matrix = SupportMatrix(case.candidate, case.evidence_spans, case.oracle.support_cells)
        result = evaluate_sufficiency(
            matrix, tuple(span.span_id for span in case.evidence_spans)
        )
        assert result.missing_qualifier_slots == {"A1": (missing_slot,)}, case_id
        assert result.missing_claim_ids == (), case_id
        assert result.missing_claim_parts == {}, case_id


def test_semantically_supportive_evidence_units_are_self_contained_paragraphs(
    tmp_path: Path,
) -> None:
    from scripts.build_direction1_synthetic_benchmark import build_benchmark

    output = tmp_path / "direction1.jsonl"
    build_benchmark(output)
    by_id = {case.case_id: case for case in load_benchmark(output)}
    expected_full_paragraph_spans = {
        "MSG-C004": ("P1",),
        "MSG-C008": ("P1",),
        "MSG-C019": ("P1",),
        "MSG-C020": ("P1",),
        "MSG-C029": ("P2",),
        "MSG-C034": ("P1",),
        "MSG-C035": ("P1",),
    }

    for case_id, paragraph_ids in expected_full_paragraph_spans.items():
        case = by_id[case_id]
        paragraphs = {
            paragraph.paragraph_id: paragraph.text
            for paragraph in case.document.paragraphs
        }
        spans = {span.paragraph_id: span.text for span in case.evidence_spans}
        for paragraph_id in paragraph_ids:
            assert spans[paragraph_id] == paragraphs[paragraph_id], case_id
