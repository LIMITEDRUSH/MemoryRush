from __future__ import annotations

import json
import hmac
from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from memoryrush.admission.benchmark import BenchmarkCase, load_benchmark
from memoryrush.admission.semantic_manifest import (
    DECODING_SEED,
    InferenceManifest,
    InferenceSchedule,
    OpaqueSpanIdPair,
    build_inference_artifacts,
    build_inference_schedule,
    parse_inference_manifest,
    parse_inference_schedule,
    parse_outer_mapping,
)


BENCHMARK_PATH = Path("data/benchmarks/direction1_synthetic_v0_1.jsonl")
OPAQUE_NAMESPACE = "0123456789abcdef" * 4
OTHER_OPAQUE_NAMESPACE = "fedcba9876543210" * 4


@pytest.fixture(scope="module")
def benchmark_cases() -> tuple[BenchmarkCase, ...]:
    return load_benchmark(BENCHMARK_PATH)


def test_inference_manifest_is_canonical_stable_and_contains_only_model_fields(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    rebuilt_manifest, rebuilt_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )

    assert len(manifest.cases) == 36
    assert "case_000000000001" not in {case.case_id for case in manifest.cases}
    assert manifest.canonical_bytes() == rebuilt_manifest.canonical_bytes()
    assert manifest.sha256 == rebuilt_manifest.sha256
    assert outer_mapping.canonical_bytes() == rebuilt_mapping.canonical_bytes()
    assert outer_mapping.sha256 == rebuilt_mapping.sha256
    assert outer_mapping.inference_manifest_sha256 == manifest.sha256

    payload = json.loads(manifest.canonical_bytes())
    assert set(payload) == {"schema_version", "cases"}
    for case in payload["cases"]:
        assert set(case) == {"case_id", "proposition", "atomic_claims", "evidence"}
        assert case["case_id"].startswith("case_")
        for claim in case["atomic_claims"]:
            assert set(claim) == {
                "claim_id",
                "text",
                "qualifiers",
                "required_support_parts",
            }
            assert claim["claim_id"].startswith("claim_")
            assert all(set(slot) == {"kind", "value"} for slot in claim["qualifiers"])
        for evidence in case["evidence"]:
            assert set(evidence) == {"span_id", "text"}
            assert evidence["span_id"].startswith("span_")

    serialized = manifest.canonical_bytes().decode("utf-8")
    forbidden_keys = {
        "document_id",
        "paragraph_id",
        "candidate_id",
        "case_family",
        "oracle",
        "support_cells",
        "claim_form",
        "minimal_evidence_sets",
        "reason_codes",
        "label_source",
        "adjudication_status",
        "provenance",
        "base_case_id",
        "perturbation_operator",
        "source_sha256",
        "start_char",
        "end_char",
        "path",
    }
    assert forbidden_keys.isdisjoint(_all_keys(payload))
    assert "MSG-C" not in serialized
    assert all(case.document.source_sha256 not in serialized for case in benchmark_cases)

    original_ids = {
        value
        for case in benchmark_cases
        for value in (
            case.case_id,
            case.document.document_id,
            case.candidate.candidate_id,
            *(claim.claim_id for claim in case.candidate.atomic_claims),
            *(span.span_id for span in case.evidence_spans),
            *(span.paragraph_id for span in case.evidence_spans),
        )
    }
    visible_identifier_values = {
        case["case_id"] for case in payload["cases"]
    } | {
        child[id_key]
        for case in payload["cases"]
        for collection, id_key in (("atomic_claims", "claim_id"), ("evidence", "span_id"))
        for child in case[collection]
    }
    assert original_ids.isdisjoint(visible_identifier_values)


def test_outer_mapping_retains_reversible_ids_and_source_blocks_separately(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )

    assert outer_mapping.opaque_namespace == OPAQUE_NAMESPACE
    assert OPAQUE_NAMESPACE not in manifest.canonical_bytes().decode("utf-8")
    assert {item.opaque_case_id for item in outer_mapping.cases} == {
        item.case_id for item in manifest.cases
    }
    assert {item.original_case_id for item in outer_mapping.cases} == {
        case.case_id for case in benchmark_cases
    }
    assert {item.source_block_identity for item in outer_mapping.cases} == {
        case.document.source_sha256 for case in benchmark_cases
    }

    originals = {case.case_id: case for case in benchmark_cases}
    for item in outer_mapping.cases:
        original = originals[item.original_case_id]
        assert item.original_document_id == original.document.document_id
        assert item.original_candidate_id == original.candidate.candidate_id
        assert {pair.original_id for pair in item.claim_ids} == {
            claim.claim_id for claim in original.candidate.atomic_claims
        }
        assert {pair.original_id for pair in item.span_ids} == {
            span.span_id for span in original.evidence_spans
        }
        assert {pair.original_paragraph_id for pair in item.span_ids} == {
            span.paragraph_id for span in original.evidence_spans
        }


def test_opaque_namespace_is_required_validated_and_run_local(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    with pytest.raises(TypeError):
        build_inference_artifacts(benchmark_cases)  # type: ignore[call-arg]
    for invalid in ("", "0" * 63, "G" * 64, True):
        with pytest.raises((TypeError, ValueError), match="opaque_namespace"):
            build_inference_artifacts(
                benchmark_cases, opaque_namespace=invalid  # type: ignore[arg-type]
            )

    first_manifest, first_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    other_manifest, other_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OTHER_OPAQUE_NAMESPACE
    )
    assert first_manifest.sha256 != other_manifest.sha256
    assert first_mapping.sha256 != other_mapping.sha256
    assert {case.case_id for case in first_manifest.cases}.isdisjoint(
        case.case_id for case in other_manifest.cases
    )

    expected = "case_" + hmac.new(
        bytes.fromhex(OPAQUE_NAMESPACE),
        b"case\0MSG-C001",
        sha256,
    ).hexdigest()[:12]
    original_to_opaque = {
        item.original_case_id: item.opaque_case_id for item in first_mapping.cases
    }
    assert expected == "case_18ba1d7e0d33"
    assert original_to_opaque["MSG-C001"] == expected


def test_builder_rejects_original_identifier_embedded_in_visible_text(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    first = benchmark_cases[0]
    leaking_candidate = replace(
        first.candidate,
        proposition=f"{first.candidate.proposition} {first.case_id}",
    )
    leaking_case = replace(first, candidate=leaking_candidate)

    with pytest.raises(ValueError, match="original identifier.*model-visible"):
        build_inference_artifacts(
            (leaking_case, *benchmark_cases[1:]),
            opaque_namespace=OPAQUE_NAMESPACE,
        )


@pytest.mark.parametrize("schedule_seed", [17, 29, 47])
def test_schedule_is_source_blocked_balanced_and_uses_one_shared_evidence_order(
    benchmark_cases: tuple[BenchmarkCase, ...], schedule_seed: int
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    schedule = build_inference_schedule(manifest, outer_mapping, schedule_seed)

    assert schedule.decoding_seed == DECODING_SEED == 17
    assert schedule.schedule_seed == schedule_seed
    assert schedule.inference_manifest_sha256 == manifest.sha256
    assert schedule.outer_mapping_sha256 == outer_mapping.sha256
    assert len(schedule.cases) == 36
    assert {item.case_id for item in schedule.cases} == {
        item.case_id for item in manifest.cases
    }

    first_support_roles = [item.request_roles[1] for item in schedule.cases]
    assert first_support_roles.count("atomic_support") == 18
    assert first_support_roles.count("holistic_support") == 18

    manifest_by_id = {item.case_id: item for item in manifest.cases}
    outer_by_id = {item.opaque_case_id: item for item in outer_mapping.cases}
    block_sequence = [
        outer_by_id[item.case_id].source_block_identity for item in schedule.cases
    ]
    assert _blocks_are_contiguous(block_sequence)
    expected_blocks = sorted(
        {item.source_block_identity for item in outer_mapping.cases},
        key=lambda block_id: (
            sha256(f"{schedule_seed}|{block_id}".encode("utf-8")).hexdigest(),
            block_id,
        ),
    )
    expected_case_ids = tuple(
        case_id
        for block_id in expected_blocks
        for case_id in sorted(
            (
                item.opaque_case_id
                for item in outer_mapping.cases
                if item.source_block_identity == block_id
            ),
            key=lambda case_id: (
                sha256(
                    f"{schedule_seed}|{block_id}|{case_id}".encode("utf-8")
                ).hexdigest(),
                case_id,
            ),
        )
    )
    assert tuple(item.case_id for item in schedule.cases) == expected_case_ids

    role_ranked = sorted(
        manifest.cases,
        key=lambda item: (
            sha256(
                f"{schedule_seed}|role|{item.case_id}".encode("utf-8")
            ).hexdigest(),
            item.case_id,
        ),
    )
    expected_atomic_first = {
        item.case_id for item in role_ranked[: len(role_ranked) // 2]
    }
    for item in schedule.cases:
        assert item.request_roles[0] == "claim_form"
        assert set(item.request_roles[1:]) == {"atomic_support", "holistic_support"}
        assert (item.request_roles[1] == "atomic_support") == (
            item.case_id in expected_atomic_first
        )
        expected_evidence_order = tuple(
            evidence.span_id
            for evidence in sorted(
                manifest_by_id[item.case_id].evidence,
                key=lambda evidence: (
                    sha256(
                        (
                            f"{schedule_seed}|{item.case_id}|"
                            f"{evidence.span_id}"
                        ).encode("utf-8")
                    ).hexdigest(),
                    evidence.span_id,
                ),
            )
        )
        assert item.evidence_order == expected_evidence_order
        assert len(item.evidence_order) == len(set(item.evidence_order))


def test_schedule_seed_changes_only_schedule_not_manifest_or_mapping(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    schedule_17 = build_inference_schedule(manifest, outer_mapping, 17)
    repeated_17 = build_inference_schedule(manifest, outer_mapping, 17)
    schedule_29 = build_inference_schedule(manifest, outer_mapping, 29)

    assert schedule_17.canonical_bytes() == repeated_17.canonical_bytes()
    assert schedule_17.sha256 == repeated_17.sha256
    assert schedule_17.canonical_bytes() != schedule_29.canonical_bytes()
    assert schedule_17.sha256 != schedule_29.sha256

    rebuilt_manifest, rebuilt_mapping = build_inference_artifacts(
        tuple(reversed(benchmark_cases)), opaque_namespace=OPAQUE_NAMESPACE
    )
    assert manifest.canonical_bytes() == rebuilt_manifest.canonical_bytes()
    assert outer_mapping.canonical_bytes() == rebuilt_mapping.canonical_bytes()


def test_schedule_frozen_hash_formulas_have_independent_golden_vectors() -> None:
    assert sha256(b"17|abc").hexdigest() == (
        "e5294436c73a8ed3b38c42dfc5540fb054d041edcc40a703453800be4724bcb9"
    )
    assert sha256(b"17|abc|case_0123456789ab").hexdigest() == (
        "482ca923e11354463b9c6ce5060fb77562e00231f5a237bd46265025d353f859"
    )
    assert sha256(b"17|case_0123456789ab|span_001").hexdigest() == (
        "6e84edbe6a53ef31b1e5d84de26e53526adc5c7a5bd4e4e946b3cc34291e96ff"
    )
    assert sha256(b"17|role|case_0123456789ab").hexdigest() == (
        "4fd3bc4a7777c12fc2b0c51604e629f6e37e28e5d4f00945240e05d840551869"
    )


def test_frozen_benchmark_schedule_hash_and_role_assignment_are_exact(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    schedule = build_inference_schedule(manifest, outer_mapping, 17)

    assert manifest.sha256 == (
        "7616dd358514530de07a68dd2929bcfb462b35b550aec03717a98258069cbd89"
    )
    assert outer_mapping.sha256 == (
        "f196dfdaa870a09a023406ca9bde17dff955e35ffd74c482f56b5f1b666564b0"
    )
    assert schedule.sha256 == (
        "317e58fea49e0c0c68d793176a5709ac208c38904084fce5260852246a10a5bf"
    )

    role_ranked = sorted(
        schedule.cases,
        key=lambda item: sha256(
            f"17|role|{item.case_id}".encode("utf-8")
        ).hexdigest(),
    )
    atomic_first = {item.case_id for item in role_ranked[:18]}
    assert all(
        (item.request_roles[1] == "atomic_support") == (item.case_id in atomic_first)
        for item in schedule.cases
    )


def test_schedule_rejects_outer_claim_or_span_mapping_drift(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    first_mapping = outer_mapping.cases[0]
    wrong_span_mapping = replace(
        first_mapping,
        span_ids=(
            OpaqueSpanIdPair(
                "span_999",
                first_mapping.span_ids[0].original_id,
                first_mapping.span_ids[0].original_paragraph_id,
            ),
            *first_mapping.span_ids[1:],
        ),
    )
    drifted_mapping = replace(
        outer_mapping,
        cases=(wrong_span_mapping, *outer_mapping.cases[1:]),
    )

    with pytest.raises(ValueError, match="opaque claim/span mapping"):
        build_inference_schedule(manifest, drifted_mapping, 17)


def test_artifacts_round_trip_through_strict_parsers(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    schedule = build_inference_schedule(manifest, outer_mapping, 17)

    assert parse_inference_manifest(json.loads(manifest.canonical_bytes())) == manifest
    assert parse_outer_mapping(json.loads(outer_mapping.canonical_bytes())) == outer_mapping
    assert parse_inference_schedule(json.loads(schedule.canonical_bytes())) == schedule


def test_inference_parser_rejects_unknown_fields_at_every_level(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, _ = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    pristine = json.loads(manifest.canonical_bytes())
    mutations: tuple[Callable[[dict], None], ...] = (
        lambda value: value.update({"oracle": {}}),
        lambda value: value["cases"][0].update({"case_family": "leak"}),
        lambda value: value["cases"][0]["atomic_claims"][0].update(
            {"support_cells": []}
        ),
        lambda value: value["cases"][0]["atomic_claims"][0]["qualifiers"][0].update(
            {"reason": "leak"}
        ),
        lambda value: value["cases"][0]["evidence"][0].update(
            {"paragraph_id": "leak"}
        ),
    )

    for mutate in mutations:
        payload = json.loads(json.dumps(pristine))
        mutate(payload)
        with pytest.raises(ValueError, match="unknown fields"):
            parse_inference_manifest(payload)


def test_outer_and_schedule_parsers_reject_unknown_fields(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    schedule = build_inference_schedule(manifest, outer_mapping, 17)

    outer_payload = json.loads(outer_mapping.canonical_bytes())
    outer_payload["cases"][0]["oracle"] = "leak"
    with pytest.raises(ValueError, match="unknown fields"):
        parse_outer_mapping(outer_payload)

    schedule_payload = json.loads(schedule.canonical_bytes())
    schedule_payload["cases"][0]["source_block_identity"] = "leak"
    with pytest.raises(ValueError, match="unknown fields"):
        parse_inference_schedule(schedule_payload)


def test_outer_parser_rejects_namespace_that_does_not_authenticate_case_ids(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    _, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    payload = json.loads(outer_mapping.canonical_bytes())
    payload["opaque_namespace"] = OTHER_OPAQUE_NAMESPACE

    with pytest.raises(ValueError, match="opaque_namespace.*case IDs"):
        parse_outer_mapping(payload)


def test_dataclasses_fail_closed_on_mutable_or_wrong_exact_types(
    benchmark_cases: tuple[BenchmarkCase, ...],
) -> None:
    manifest, outer_mapping = build_inference_artifacts(
        benchmark_cases, opaque_namespace=OPAQUE_NAMESPACE
    )
    schedule = build_inference_schedule(manifest, outer_mapping, 17)

    with pytest.raises(TypeError, match="cases must be a tuple"):
        InferenceManifest(manifest.schema_version, list(manifest.cases))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="schedule_seed must be an integer"):
        InferenceSchedule(
            schedule.schema_version,
            schedule.inference_manifest_sha256,
            schedule.outer_mapping_sha256,
            True,  # type: ignore[arg-type]
            schedule.decoding_seed,
            schedule.cases,
        )
    with pytest.raises(ValueError, match="decoding_seed must be 17"):
        InferenceSchedule(
            schedule.schema_version,
            schedule.inference_manifest_sha256,
            schedule.outer_mapping_sha256,
            schedule.schedule_seed,
            29,
            schedule.cases,
        )


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            child_key for child in value.values() for child_key in _all_keys(child)
        }
    if isinstance(value, list):
        return {child_key for child in value for child_key in _all_keys(child)}
    return set()


def _blocks_are_contiguous(blocks: list[str]) -> bool:
    completed: set[str] = set()
    current: str | None = None
    for block in blocks:
        if block != current:
            if block in completed:
                return False
            if current is not None:
                completed.add(current)
            current = block
    return True
