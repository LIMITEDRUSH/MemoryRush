import json
from hashlib import sha256

import pytest

from memoryrush.admission.benchmark import load_benchmark, parse_benchmark_case


def _payload() -> dict:
    paragraph = "The 120-person trial may finish in 2025 under stable funding."
    document_snapshot = paragraph
    source_hash = sha256(document_snapshot.encode("utf-8")).hexdigest()
    return {
        "schema_version": "direction1.synthetic_oracle.v0.1",
        "case_id": "case-001",
        "case_family": "fully_supported_single_span",
        "document": {
            "document_id": "doc-001",
            "title": "Synthetic trial",
            "snapshot_text": document_snapshot,
            "source_sha256": source_hash,
            "paragraphs": [
                {
                    "paragraph_id": "p_001",
                    "text": paragraph,
                    "snapshot_start": 0,
                    "snapshot_end": len(paragraph),
                }
            ],
        },
        "candidate": {
            "candidate_id": "candidate-001",
            "proposition": "The 120-person trial may finish in 2025 under stable funding.",
            "atomic_claims": [
                {
                    "claim_id": "claim-001",
                    "text": "The 120-person trial may finish in 2025 under stable funding.",
                    "qualifiers": [
                        {"kind": "quantifier", "value": "120"},
                        {"kind": "modality", "value": "may"},
                        {"kind": "time", "value": "2025"},
                        {"kind": "condition", "value": "under stable funding"},
                    ],
                    "required_support_parts": [],
                }
            ],
        },
        "evidence_spans": [
            {
                "span_id": "span-001",
                "paragraph_id": "p_001",
                "start_char": 0,
                "end_char": len(paragraph),
                "text": paragraph,
            }
        ],
        "oracle": {
            "decision": "ADMIT",
            "reason_codes": ["fully_supported"],
            "minimal_evidence_sets": [["span-001"]],
            "label_source": "programmatic_oracle",
            "adjudication_status": "synthetic_oracle",
        },
        "provenance": {
            "construction": "project_authored_synthetic",
            "base_case_id": None,
            "perturbation_operator": None,
            "generator": "human_specified_by_agent",
        },
    }


def test_parse_valid_case_resolves_candidate_and_span() -> None:
    case = parse_benchmark_case(_payload())

    assert case.case_id == "case-001"
    assert case.candidate.atomic_claims[0].qualifiers[1].value == "may"
    assert case.evidence_spans[0].text.startswith("The 120-person")
    assert case.document.paragraphs[0].snapshot_start == 0
    assert case.oracle.minimal_evidence_sets == (("span-001",),)


def test_source_hash_and_evidence_offsets_are_verified() -> None:
    bad_hash = _payload()
    bad_hash["document"]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source_sha256"):
        parse_benchmark_case(bad_hash)

    bad_span = _payload()
    bad_span["evidence_spans"][0]["start_char"] = 1
    with pytest.raises(ValueError, match="does not match paragraph"):
        parse_benchmark_case(bad_span)


def test_oracle_minimal_sets_must_reference_known_spans() -> None:
    payload = _payload()
    payload["oracle"]["minimal_evidence_sets"] = [["span-missing"]]

    with pytest.raises(ValueError, match="unknown evidence span"):
        parse_benchmark_case(payload)


def test_llm_generated_label_cannot_claim_human_adjudication() -> None:
    payload = _payload()
    payload["oracle"]["label_source"] = "llm_generated"
    payload["oracle"]["adjudication_status"] = "human_gold"

    with pytest.raises(ValueError, match="LLM-generated"):
        parse_benchmark_case(payload)


@pytest.mark.parametrize(
    ("label_source", "adjudication_status"),
    [
        ("programmatic_oracle", "provisional"),
        ("programmatic_oracle", "human_gold"),
        ("llm_generated", "synthetic_oracle"),
        ("human", "synthetic_oracle"),
    ],
)
def test_label_source_and_adjudication_combinations_are_truthful(
    label_source: str,
    adjudication_status: str,
) -> None:
    payload = _payload()
    payload["oracle"]["label_source"] = label_source
    payload["oracle"]["adjudication_status"] = adjudication_status

    with pytest.raises(ValueError, match="label_source/adjudication_status"):
        parse_benchmark_case(payload)


@pytest.mark.parametrize(
    "object_path",
    [
        (),
        ("document",),
        ("document", "paragraphs", 0),
        ("candidate",),
        ("candidate", "atomic_claims", 0),
        ("candidate", "atomic_claims", 0, "qualifiers", 0),
        ("evidence_spans", 0),
        ("oracle",),
        ("provenance",),
    ],
)
def test_unknown_fields_are_rejected_at_every_schema_level(object_path: tuple) -> None:
    payload = _payload()
    target = payload
    for component in object_path:
        target = target[component]
    target["unexpected"] = "must fail closed"

    with pytest.raises(ValueError, match="unknown fields.*unexpected"):
        parse_benchmark_case(payload)


def test_repeated_paragraph_text_requires_distinct_ordered_snapshot_offsets() -> None:
    payload = _payload()
    snapshot = "A. A."
    payload["document"]["snapshot_text"] = snapshot
    payload["document"]["source_sha256"] = sha256(snapshot.encode("utf-8")).hexdigest()
    payload["document"]["paragraphs"] = [
        {"paragraph_id": "p_001", "text": "A.", "snapshot_start": 0, "snapshot_end": 2},
        {"paragraph_id": "p_002", "text": "A.", "snapshot_start": 0, "snapshot_end": 2},
    ]
    payload["evidence_spans"][0].update(
        {"paragraph_id": "p_002", "text": "A.", "start_char": 0, "end_char": 2}
    )

    with pytest.raises(ValueError, match="ordered, non-overlapping"):
        parse_benchmark_case(payload)


def test_load_benchmark_rejects_duplicate_case_ids(tmp_path) -> None:
    path = tmp_path / "benchmark.jsonl"
    serialized = json.dumps(_payload())
    path.write_text(f"{serialized}\n{serialized}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate case_id"):
        load_benchmark(path)


def test_admit_case_requires_an_oracle_minimal_evidence_set() -> None:
    payload = _payload()
    payload["oracle"]["minimal_evidence_sets"] = []

    with pytest.raises(ValueError, match="ADMIT oracle"):
        parse_benchmark_case(payload)
