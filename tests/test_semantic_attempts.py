import base64
import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path

import pytest

import memoryrush.admission.semantic_attempts as semantic_attempts
from memoryrush.admission.semantic_attempts import (
    ArtifactHash,
    ArtifactIntegrityError,
    AttemptSnapshot,
    AttemptState,
    AttemptStore,
    PreparedAttempt,
    ReturnedAttempt,
    TransportFailedAttempt,
    canonical_json_bytes,
)
from memoryrush.admission.semantic_judges import claim_form_response_schema
from memoryrush.admission.semantic_judges import holistic_response_schema
from memoryrush.admission.ollama_verifier import semantic_support_response_schema


def _request_bytes(
    *,
    method: str = "shared_claim_form_v0",
    prompt_role: str = "claim_form",
    response_schema: dict[str, object] | None = None,
) -> bytes:
    return canonical_json_bytes(
        {
            "decoding_seed": 17,
            "method": method,
            "ollama": {
                "endpoint": "http://localhost:11434/api/generate",
                "payload": {
                    "format": response_schema or claim_form_response_schema(),
                    "model": "qwen3:8b",
                    "options": {
                        "num_ctx": 8192,
                        "num_predict": 2048,
                        "seed": 17,
                        "temperature": 0.0,
                    },
                    "prompt": "Judge this proposition.\n<UNTRUSTED_JSON>\n{}\n</UNTRUSTED_JSON>",
                    "stream": False,
                    "think": False,
                },
                "timeout_seconds": 120,
            },
            "opaque_case_id": "case_012345abcdef",
            "prompt_role": prompt_role,
            "schedule_position": 0,
            "schedule_seed": 17,
            "schema_version": "semantic_ollama_request.v0.1",
        }
    )


def _prepared(attempt_id: str = "attempt_001") -> PreparedAttempt:
    return PreparedAttempt(
        experiment_id="direction1_semantic_pilot_v0_1",
        run_id="run_debug_seed17",
        attempt_id=attempt_id,
        run_class="DEBUGGING",
        method="shared_claim_form_v0",
        prompt_role="claim_form",
        decoding_seed=17,
        schedule_seed=17,
        schedule_position=0,
        opaque_case_id="case_012345abcdef",
        started_at="2026-08-14T05:30:00+08:00",
        started_monotonic_ns=1_000_000,
        canonical_request_bytes=_request_bytes(),
        artifact_hashes=(
            ArtifactHash("prompt_template", "a" * 64),
            ArtifactHash("inference_manifest", "b" * 64),
        ),
    )


def _returned(prepared_sha256: str, raw: bytes = b'{"done":true}') -> ReturnedAttempt:
    return ReturnedAttempt(
        attempt_id="attempt_001",
        prepared_record_sha256=prepared_sha256,
        returned_at="2026-08-14T05:30:01+08:00",
        ended_monotonic_ns=1_500_000,
        http_status=200,
        raw_http_body=raw,
        exit_code=None,
    )


def _failed(prepared_sha256: str) -> TransportFailedAttempt:
    return TransportFailedAttempt(
        attempt_id="attempt_001",
        prepared_record_sha256=prepared_sha256,
        failed_at="2026-08-14T05:30:01+08:00",
        ended_monotonic_ns=1_250_000,
        exception_type="TimeoutError",
        exception_message="local endpoint timed out",
        raw_http_body=None,
        http_status=None,
        exit_code=None,
    )


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_value_objects_are_frozen_and_reject_type_coercion() -> None:
    digest = ArtifactHash("prompt_template", "a" * 64)
    with pytest.raises(FrozenInstanceError):
        digest.name = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="schedule_position must be an integer"):
        replace(_prepared(), schedule_position=True)

    with pytest.raises(TypeError, match="artifact_hashes must be a tuple"):
        replace(_prepared(), artifact_hashes=[digest])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone-aware"):
        replace(_prepared(), started_at="2026-08-14T05:30:00")

    noncanonical = b'{"z":1, "a":2}\n'
    with pytest.raises(ValueError, match="canonical JSON"):
        replace(_prepared(), canonical_request_bytes=noncanonical)


def test_prepared_record_is_canonical_hash_verified_and_contains_exact_request(
    tmp_path: Path,
) -> None:
    store = AttemptStore(tmp_path)

    stored = store.write_prepared(_prepared())

    raw_record = stored.path.read_bytes()
    record = json.loads(raw_record)
    assert raw_record.endswith(b"\n")
    assert b"\r" not in raw_record
    assert raw_record == canonical_json_bytes(record)
    assert stored.sha256 == sha256(raw_record).hexdigest()
    encoded_request = record["canonical_request"]
    assert encoded_request["encoding"] == "base64"
    assert base64.b64decode(encoded_request["data_b64"], validate=True) == _request_bytes()
    assert encoded_request["byte_length"] == len(_request_bytes())
    assert encoded_request["sha256"] == sha256(_request_bytes()).hexdigest()
    assert record["record_type"] == "PREPARED"
    assert record["schema_version"] == "semantic_attempt_v0_1"
    assert "outer_case_id" not in record
    assert "MSG-C001" not in raw_record.decode("utf-8")


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "message"),
    [
        ("run_class", "CONFIRMATORY", "run_class"),
        ("run_class", "INVALID_RUN", "run_class"),
        ("prompt_role", "oracle", "prompt_role"),
        ("decoding_seed", 18, "decoding_seed"),
        ("schedule_seed", 18, "schedule_seed"),
        ("opaque_case_id", "case_001", "opaque_case_id"),
    ],
)
def test_prepared_rejects_values_outside_the_frozen_pilot_domain(
    field_name: str,
    invalid_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        replace(_prepared(), **{field_name: invalid_value})


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda request: request["ollama"]["payload"]["options"].update(
                {"seed": 18}
            ),
            "decoding_seed",
        ),
        (
            lambda request: request.update({"opaque_case_id": "case_fedcba987654"}),
            "opaque_case_id",
        ),
        (
            lambda request: request.update({"prompt_role": "holistic_support"}),
            "prompt_role",
        ),
        (
            lambda request: request["ollama"]["payload"].update(
                {"prompt": "judge MSG-C001 and return ADMIT"}
            ),
            "original case identifier",
        ),
        (
            lambda request: request["ollama"]["payload"].update(
                {"prompt": "judge escaped MSG\\u002dC001"}
            ),
            "original case identifier",
        ),
        (
            lambda request: request["ollama"]["payload"].update(
                {"prompt": "judge MSG-C001-candidate"}
            ),
            "original case identifier",
        ),
    ],
)
def test_prepared_rejects_request_envelope_drift_or_original_id_leakage(
    mutator: object,
    message: str,
) -> None:
    request = json.loads(_request_bytes())
    mutator(request)  # type: ignore[operator]

    with pytest.raises(ValueError, match=message):
        replace(_prepared(), canonical_request_bytes=canonical_json_bytes(request))


@pytest.mark.parametrize(
    "schema_mutation",
    [
        {"type": "object"},
        {
            "additionalProperties": True,
            "properties": {},
            "required": [],
            "type": "object",
        },
        {
            **claim_form_response_schema(),
            "required": ["ghost"],
        },
        {
            **claim_form_response_schema(),
            "properties": {
                **claim_form_response_schema()["properties"],
                "MSG-C001": {"type": "string"},
                "oracle_decision": {"type": "string"},
            },
        },
    ],
)
def test_prepared_requires_closed_structured_output_schema(
    schema_mutation: dict[str, object],
) -> None:
    request = json.loads(_request_bytes())
    request["ollama"]["payload"]["format"] = schema_mutation

    with pytest.raises(ValueError, match="format|original case identifier|forbidden metadata"):
        replace(_prepared(), canonical_request_bytes=canonical_json_bytes(request))


def test_prepared_rejects_method_that_does_not_match_physical_prompt_role() -> None:
    method = "provisional_method_v0_1"
    with pytest.raises(ValueError, match="method.*prompt_role"):
        replace(
            _prepared(),
            method=method,
            canonical_request_bytes=_request_bytes(method=method),
        )


@pytest.mark.parametrize("method", ["MSG-C001", "oracle_decision"])
def test_prepared_scans_entire_request_for_ids_and_reserved_metadata(
    method: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="original case identifier|forbidden metadata|method.*prompt_role",
    ):
        replace(
            _prepared(),
            method=method,
            canonical_request_bytes=_request_bytes(method=method),
        )


@pytest.mark.parametrize(
    ("prompt_role", "method", "response_schema"),
    [
        ("claim_form", "shared_claim_form_v0", claim_form_response_schema()),
        (
            "atomic_support",
            "atomic_semantic_support_v0",
            semantic_support_response_schema(),
        ),
        (
            "holistic_support",
            "holistic_detail_matched_v0",
            holistic_response_schema(),
        ),
    ],
)
def test_prepared_accepts_only_the_exact_committed_schema_for_each_role(
    prompt_role: str,
    method: str,
    response_schema: dict[str, object],
) -> None:
    attempt = replace(
        _prepared(),
        prompt_role=prompt_role,
        method=method,
        canonical_request_bytes=_request_bytes(
            prompt_role=prompt_role,
            method=method,
            response_schema=response_schema,
        ),
    )

    assert attempt.prompt_role == prompt_role
    assert attempt.method == method


def test_returned_record_links_prepared_and_preserves_invalid_json_before_parse(
    tmp_path: Path,
) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())
    invalid_raw = b'not-json\x00\xff'

    with pytest.raises((UnicodeDecodeError, json.JSONDecodeError)):
        store.write_returned_then_parse(
            _returned(prepared.sha256, invalid_raw),
            lambda raw: json.loads(raw.decode("utf-8")),
        )

    terminal_path = tmp_path / "attempt_001" / "terminal.json"
    terminal = _load(terminal_path)
    assert terminal["record_type"] == "RETURNED"
    assert terminal["prepared_record_sha256"] == prepared.sha256
    assert terminal["duration_monotonic_ns"] == 500_000
    assert terminal["http_status"] == 200
    assert base64.b64decode(
        terminal["raw_http_body"]["data_b64"], validate=True
    ) == invalid_raw
    assert terminal["raw_http_body"]["sha256"] == sha256(invalid_raw).hexdigest()
    assert store.scan_attempts() == (
        AttemptSnapshot(
            attempt_id="attempt_001",
            state=AttemptState.RETURNED,
            prepared_sha256=prepared.sha256,
            terminal_sha256=sha256(terminal_path.read_bytes()).hexdigest(),
        ),
    )


def test_transport_failure_explicitly_records_absent_envelope_and_exception(
    tmp_path: Path,
) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())

    store.write_transport_failed(_failed(prepared.sha256))

    terminal = _load(tmp_path / "attempt_001" / "terminal.json")
    assert terminal["record_type"] == "TRANSPORT_FAILED"
    assert terminal["raw_http_body"] is None
    assert terminal["http_status"] is None
    assert terminal["exception_type"] == "TimeoutError"
    assert terminal["exception_message"] == "local endpoint timed out"
    assert terminal["duration_monotonic_ns"] == 250_000
    assert store.scan_attempts()[0].state is AttemptState.TRANSPORT_FAILED


def test_transport_failure_preserves_multiline_exception_message(tmp_path: Path) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())
    message = "first line\nsecond\tline"

    failed = replace(_failed(prepared.sha256), exception_message=message)
    store.write_transport_failed(failed)

    terminal = _load(tmp_path / "attempt_001" / "terminal.json")
    assert terminal["exception_message"] == message


def test_prepared_without_terminal_scans_as_incomplete_not_review(tmp_path: Path) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())

    snapshots = store.scan_attempts()

    assert snapshots == (
        AttemptSnapshot(
            attempt_id="attempt_001",
            state=AttemptState.INCOMPLETE_ATTEMPT,
            prepared_sha256=prepared.sha256,
            terminal_sha256=None,
        ),
    )
    assert "REVIEW" not in {state.value for state in AttemptState}


def test_attempt_and_terminal_records_are_append_only(tmp_path: Path) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())

    with pytest.raises(FileExistsError, match="attempt already exists"):
        store.write_prepared(_prepared())

    store.write_returned(_returned(prepared.sha256))
    with pytest.raises(FileExistsError, match="terminal record already exists"):
        store.write_returned(_returned(prepared.sha256))
    with pytest.raises(FileExistsError, match="terminal record already exists"):
        store.write_transport_failed(_failed(prepared.sha256))


def test_concurrent_terminal_writers_publish_exactly_one_record(tmp_path: Path) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())
    returned = _returned(prepared.sha256, b'{"winner":"returned"}')
    failed = _failed(prepared.sha256)

    def publish(kind: str) -> str:
        try:
            if kind == "returned":
                store.write_returned(returned)
            else:
                store.write_transport_failed(failed)
            return "written"
        except FileExistsError:
            return "exists"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = tuple(executor.map(publish, ("returned", "failed")))

    assert sorted(outcomes) == ["exists", "written"]
    assert store.scan_attempts()[0].state in {
        AttemptState.RETURNED,
        AttemptState.TRANSPORT_FAILED,
    }


def test_wrong_parent_hash_and_tampered_prepared_fail_closed(tmp_path: Path) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())

    with pytest.raises(ArtifactIntegrityError, match="prepared record hash mismatch"):
        store.write_returned(_returned("c" * 64))

    prepared.path.write_bytes(
        prepared.path.read_bytes().replace(
            b"case_012345abcdef",
            b"case_fedcba987654",
        )
    )
    with pytest.raises(ArtifactIntegrityError, match="prepared record"):
        store.write_returned(_returned(prepared.sha256))


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("run_class", "CONFIRMATORY"),
        ("run_class", "INVALID_RUN"),
        ("prompt_role", "oracle"),
        ("decoding_seed", 18),
        ("schedule_seed", 18),
        ("opaque_case_id", "case_001"),
    ],
)
def test_scan_rejects_self_consistent_prepared_domain_tampering(
    tmp_path: Path,
    field_name: str,
    invalid_value: object,
) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())
    record = _load(prepared.path)
    record[field_name] = invalid_value
    prepared.path.write_bytes(canonical_json_bytes(record))

    with pytest.raises(ArtifactIntegrityError, match=f"prepared {field_name}"):
        store.scan_attempts()


def test_scan_rejects_self_consistent_but_noncanonical_embedded_request(
    tmp_path: Path,
) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())
    record = _load(prepared.path)
    noncanonical = b'{"z":1, "a":2}\n'
    record["canonical_request"] = {
        "byte_length": len(noncanonical),
        "data_b64": base64.b64encode(noncanonical).decode("ascii"),
        "encoding": "base64",
        "sha256": sha256(noncanonical).hexdigest(),
    }
    prepared.path.write_bytes(canonical_json_bytes(record))

    with pytest.raises(ArtifactIntegrityError, match="canonical_request"):
        store.scan_attempts()


def test_scan_rejects_self_consistent_request_envelope_drift_and_id_leak(
    tmp_path: Path,
) -> None:
    store = AttemptStore(tmp_path)
    prepared = store.write_prepared(_prepared())
    record = _load(prepared.path)
    request = json.loads(_request_bytes())
    request["ollama"]["payload"]["options"]["seed"] = 18
    request["ollama"]["payload"]["prompt"] = "inspect MSG-C001"
    request_bytes = canonical_json_bytes(request)
    record["canonical_request"] = {
        "byte_length": len(request_bytes),
        "data_b64": base64.b64encode(request_bytes).decode("ascii"),
        "encoding": "base64",
        "sha256": sha256(request_bytes).hexdigest(),
    }
    prepared.path.write_bytes(canonical_json_bytes(record))

    with pytest.raises(ArtifactIntegrityError, match="canonical_request.*frozen"):
        store.scan_attempts()


@pytest.mark.parametrize("status", [None, True])
def test_returned_requires_exact_integer_http_status(status: object) -> None:
    with pytest.raises(TypeError, match="http_status must be an integer"):
        replace(_returned("a" * 64), http_status=status)  # type: ignore[arg-type]


def test_parent_and_attempt_directory_rules_reject_ambiguous_targets(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError, match="artifact root"):
        AttemptStore(missing)

    store = AttemptStore(tmp_path)
    with pytest.raises(ValueError, match="safe opaque identifier"):
        store.write_prepared(_prepared("../escape"))

    occupied = tmp_path / "attempt_occupied"
    occupied.mkdir()
    (occupied / "foreign.txt").write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(FileExistsError, match="attempt already exists"):
        store.write_prepared(_prepared("attempt_occupied"))


def test_scan_rejects_terminal_nonfile_entry(tmp_path: Path) -> None:
    store = AttemptStore(tmp_path)
    store.write_prepared(_prepared())
    terminal = tmp_path / "attempt_001" / "terminal.json"
    terminal.mkdir()

    with pytest.raises(ArtifactIntegrityError, match="terminal record"):
        store.scan_attempts()


def test_atomic_writer_failure_never_reports_prepared_success(tmp_path: Path) -> None:
    def failing_writer(path: Path, data: bytes) -> None:
        raise OSError("injected durable-write failure")

    store = AttemptStore(tmp_path, atomic_writer=failing_writer)

    with pytest.raises(OSError, match="injected durable-write failure"):
        store.write_prepared(_prepared())

    assert not (tmp_path / "attempt_001" / "prepared.json").exists()


def test_atomic_publication_never_overwrites_a_racing_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    competing_bytes = b"competing immutable record\n"

    def publish_competitor_then_fail(source: os.PathLike[str], target: os.PathLike[str]) -> None:
        del source
        destination = Path(target)
        descriptor = os.open(
            destination,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(competing_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        raise FileExistsError("simulated competing publication")

    monkeypatch.setattr(semantic_attempts.os, "link", publish_competitor_then_fail)
    store = AttemptStore(tmp_path)

    with pytest.raises(FileExistsError, match="simulated competing publication"):
        store.write_prepared(_prepared())

    final_path = tmp_path / "attempt_001" / "prepared.json"
    assert final_path.read_bytes() == competing_bytes


def test_terminal_readback_failure_prevents_parser_execution(tmp_path: Path) -> None:
    parser_called = False

    def terminal_corrupting_reader(path: Path) -> bytes:
        raw = path.read_bytes()
        return raw + b"corrupt" if path.name == "terminal.json" else raw

    store = AttemptStore(tmp_path, reader=terminal_corrupting_reader)
    prepared = store.write_prepared(_prepared())

    def parser(raw: bytes) -> dict:
        nonlocal parser_called
        parser_called = True
        return json.loads(raw)

    with pytest.raises(ArtifactIntegrityError, match="readback mismatch"):
        store.write_returned_then_parse(_returned(prepared.sha256), parser)

    assert parser_called is False
    assert (tmp_path / "attempt_001" / "terminal.json").exists()


def test_readback_fault_is_detected_after_write(tmp_path: Path) -> None:
    def test_writer(path: Path, data: bytes) -> None:
        path.write_bytes(data)

    def corrupting_reader(path: Path) -> bytes:
        return path.read_bytes() + b"corrupt"

    store = AttemptStore(
        tmp_path,
        atomic_writer=test_writer,
        reader=corrupting_reader,
    )

    with pytest.raises(ArtifactIntegrityError, match="readback mismatch"):
        store.write_prepared(_prepared())


def test_nonfinite_json_and_duplicate_hash_names_are_rejected() -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        canonical_json_bytes({"temperature": float("nan")})

    duplicate_hashes = (
        ArtifactHash("prompt_template", "a" * 64),
        ArtifactHash("prompt_template", "b" * 64),
    )
    with pytest.raises(ValueError, match="artifact hash names must be unique"):
        replace(_prepared(), artifact_hashes=duplicate_hashes)
