"""Append-only raw-attempt artifacts for the Direction 1 semantic pilot.

This module deliberately stops at durable transport evidence.  It does not
parse model output, assign a prediction, or turn an incomplete attempt into a
review outcome.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Any, TypeVar

from memoryrush.admission.ollama_verifier import semantic_support_response_schema
from memoryrush.admission.semantic_judges import (
    claim_form_response_schema,
    holistic_response_schema,
)


SCHEMA_VERSION = "semantic_attempt_v0_1"
_SAFE_ATTEMPT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_OPAQUE_CASE_ID = re.compile(r"case_[0-9a-f]{12}\Z")
_RUN_CLASSES = frozenset({"DEBUGGING", "EXPLORATORY"})
_PROMPT_ROLES = frozenset(
    {"claim_form", "atomic_support", "holistic_support"}
)
_SCHEDULE_SEEDS = frozenset({17, 29, 47})
_DECODING_SEED = 17
_REQUEST_SCHEMA_VERSION = "semantic_ollama_request.v0.1"
_REQUEST_MODEL = "qwen3:8b"
_REQUEST_ENDPOINT = "http://localhost:11434/api/generate"
_REQUEST_TIMEOUT_SECONDS = 120
_REQUEST_NUM_CTX = 8192
_REQUEST_NUM_PREDICT = 2048
_MAX_PROMPT_BYTES = 4_096
_ORIGINAL_CASE_ID = re.compile(r"MSG(?:-|\\u002[dD])C[0-9]{3,}")
_METHOD_BY_ROLE = {
    "claim_form": "shared_claim_form_v0",
    "atomic_support": "atomic_semantic_support_v0",
    "holistic_support": "holistic_detail_matched_v0",
}
_FORBIDDEN_REQUEST_KEYS = frozenset(
    {
        "adjudication_status",
        "base_case_id",
        "case_family",
        "generator_type",
        "label_source",
        "minimal_evidence_sets",
        "oracle",
        "oracle_decision",
        "perturbation_operator",
        "support_cells",
    }
)
_T = TypeVar("_T")

AtomicWriter = Callable[[Path, bytes], None]
Reader = Callable[[Path], bytes]


class ArtifactIntegrityError(RuntimeError):
    """Raised when an attempt artifact cannot be proven intact."""


class AttemptState(str, Enum):
    """Persisted transport states; intentionally contains no REVIEW state."""

    RETURNED = "RETURNED"
    TRANSPORT_FAILED = "TRANSPORT_FAILED"
    INCOMPLETE_ATTEMPT = "INCOMPLETE_ATTEMPT"


def _require_text(value: Any, field_name: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a string")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _require_prompt_text(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("canonical request prompt must be a string")
    if not value.strip():
        raise ValueError("canonical request prompt must not be empty")
    if "\r" in value or any(
        ord(character) < 32 and character not in {"\n", "\t"}
        for character in value
    ):
        raise ValueError(
            "canonical request prompt must use LF text without forbidden controls"
        )
    return value


def _require_exception_message(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("exception_message must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("exception_message must be valid UTF-8 text") from exc
    return value


def _require_int(value: Any, field_name: str, *, minimum: int = 0) -> int:
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer")
    if value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return value


def _require_optional_int(
    value: Any,
    field_name: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise TypeError(f"{field_name} must be an integer or None")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{field_name} must be at most {maximum}")
    return value


def _require_sha256(value: Any, field_name: str) -> str:
    _require_text(value, field_name)
    if _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")
    return value


def _require_timestamp(value: Any, field_name: str) -> str:
    _require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _require_attempt_id(value: Any) -> str:
    _require_text(value, "attempt_id")
    if value in {".", ".."} or _SAFE_ATTEMPT_ID.fullmatch(value) is None:
        raise ValueError("attempt_id must be a safe opaque identifier")
    return value


def _require_run_class(value: Any) -> str:
    _require_text(value, "run_class")
    if value not in _RUN_CLASSES:
        raise ValueError("run_class must be DEBUGGING or EXPLORATORY")
    return value


def _require_prompt_role(value: Any) -> str:
    _require_text(value, "prompt_role")
    if value not in _PROMPT_ROLES:
        raise ValueError(
            "prompt_role must be claim_form, atomic_support, or holistic_support"
        )
    return value


def _require_decoding_seed(value: Any) -> int:
    _require_int(value, "decoding_seed")
    if value != _DECODING_SEED:
        raise ValueError(f"decoding_seed must be exactly {_DECODING_SEED}")
    return value


def _require_schedule_seed(value: Any) -> int:
    _require_int(value, "schedule_seed")
    if value not in _SCHEDULE_SEEDS:
        raise ValueError("schedule_seed must be one of 17, 29, or 47")
    return value


def _require_opaque_case_id(value: Any) -> str:
    _require_text(value, "opaque_case_id")
    if _OPAQUE_CASE_ID.fullmatch(value) is None:
        raise ValueError("opaque_case_id must match case_[0-9a-f]{12}")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Return canonical UTF-8 JSON with LF termination and no non-finite values."""

    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return (rendered + "\n").encode("utf-8")


def _validate_canonical_json_object(raw: Any, field_name: str) -> bytes:
    if type(raw) is not bytes:
        raise TypeError(f"{field_name} must be bytes")
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{field_name} must contain canonical JSON") from exc
    if type(decoded) is not dict or canonical_json_bytes(decoded) != raw:
        raise ValueError(f"{field_name} must contain a canonical JSON object")
    return raw


def _require_exact_mapping_fields(
    value: Any,
    expected: set[str],
    field_name: str,
) -> dict[str, Any]:
    if type(value) is not dict:
        raise TypeError(f"{field_name} must be an object")
    if set(value) != expected:
        raise ValueError(f"{field_name} fields do not match the frozen schema")
    return value


def _expected_response_schema(prompt_role: str) -> dict[str, Any]:
    if prompt_role == "claim_form":
        return claim_form_response_schema()
    if prompt_role == "atomic_support":
        return semantic_support_response_schema()
    if prompt_role == "holistic_support":
        return holistic_response_schema()
    raise ValueError("canonical request prompt_role has no committed response schema")


def _audit_request_tree(value: Any) -> None:
    """Reject outer identifiers and reserved metadata anywhere in the request tree."""

    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise TypeError("canonical request object keys must be strings")
            if _ORIGINAL_CASE_ID.search(key):
                raise ValueError("canonical request contains an original case identifier")
            if key in _FORBIDDEN_REQUEST_KEYS:
                raise ValueError(f"canonical request contains forbidden metadata key: {key}")
            _audit_request_tree(child)
        return
    if type(value) is list:
        for child in value:
            _audit_request_tree(child)
        return
    if type(value) is str and _ORIGINAL_CASE_ID.search(value):
        raise ValueError("canonical request contains an original case identifier")


def _validate_frozen_request(
    raw: bytes,
    *,
    method: str,
    prompt_role: str,
    decoding_seed: int,
    schedule_seed: int,
    schedule_position: int,
    opaque_case_id: str,
) -> None:
    """Bind a canonical request to its PREPARED metadata and frozen envelope."""

    _validate_canonical_json_object(raw, "canonical_request_bytes")
    request = json.loads(raw.decode("utf-8"))
    _audit_request_tree(request)
    request = _require_exact_mapping_fields(
        request,
        {
            "decoding_seed",
            "method",
            "ollama",
            "opaque_case_id",
            "prompt_role",
            "schedule_position",
            "schedule_seed",
            "schema_version",
        },
        "canonical request",
    )
    if request["schema_version"] != _REQUEST_SCHEMA_VERSION:
        raise ValueError("canonical request schema_version is not frozen")
    bindings = {
        "method": method,
        "prompt_role": prompt_role,
        "decoding_seed": decoding_seed,
        "schedule_seed": schedule_seed,
        "schedule_position": schedule_position,
        "opaque_case_id": opaque_case_id,
    }
    for field_name, expected in bindings.items():
        if request[field_name] != expected or type(request[field_name]) is not type(expected):
            raise ValueError(
                f"canonical request {field_name} does not match PREPARED metadata"
            )
    expected_method = _METHOD_BY_ROLE[prompt_role]
    if method != expected_method:
        raise ValueError(
            "canonical request method does not match the physical prompt_role"
        )

    ollama = _require_exact_mapping_fields(
        request["ollama"],
        {"endpoint", "payload", "timeout_seconds"},
        "canonical request ollama",
    )
    if ollama["endpoint"] != _REQUEST_ENDPOINT:
        raise ValueError("canonical request endpoint is not frozen")
    if type(ollama["timeout_seconds"]) is not int or (
        ollama["timeout_seconds"] != _REQUEST_TIMEOUT_SECONDS
    ):
        raise ValueError("canonical request timeout_seconds is not frozen")
    payload = _require_exact_mapping_fields(
        ollama["payload"],
        {"format", "model", "options", "prompt", "stream", "think"},
        "canonical request Ollama payload",
    )
    if payload["model"] != _REQUEST_MODEL:
        raise ValueError("canonical request model is not frozen")
    if payload["stream"] is not False or payload["think"] is not False:
        raise ValueError("canonical request stream/think options are not frozen")
    response_schema = payload["format"]
    if type(response_schema) is not dict or canonical_json_bytes(
        response_schema
    ) != canonical_json_bytes(_expected_response_schema(prompt_role)):
        raise ValueError(
            "canonical request format does not match the committed role schema"
        )
    prompt = _require_prompt_text(payload["prompt"])
    if len(prompt.encode("utf-8")) > _MAX_PROMPT_BYTES:
        raise ValueError("canonical request prompt exceeds 4096 UTF-8 bytes")

    options = _require_exact_mapping_fields(
        payload["options"],
        {"num_ctx", "num_predict", "seed", "temperature"},
        "canonical request Ollama options",
    )
    if type(options["seed"]) is not int or options["seed"] != decoding_seed:
        raise ValueError("canonical request decoding_seed does not match Ollama seed")
    if type(options["temperature"]) is not float or options["temperature"] != 0.0:
        raise ValueError("canonical request temperature is not frozen at 0.0")
    if type(options["num_ctx"]) is not int or options["num_ctx"] != _REQUEST_NUM_CTX:
        raise ValueError("canonical request num_ctx is not frozen")
    if (
        type(options["num_predict"]) is not int
        or options["num_predict"] != _REQUEST_NUM_PREDICT
    ):
        raise ValueError("canonical request num_predict is not frozen")


@dataclass(frozen=True, slots=True)
class ArtifactHash:
    name: str
    sha256: str

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        _require_sha256(self.sha256, "sha256")


@dataclass(frozen=True, slots=True)
class PreparedAttempt:
    experiment_id: str
    run_id: str
    attempt_id: str
    run_class: str
    method: str
    prompt_role: str
    decoding_seed: int
    schedule_seed: int
    schedule_position: int
    opaque_case_id: str
    started_at: str
    started_monotonic_ns: int
    canonical_request_bytes: bytes
    artifact_hashes: tuple[ArtifactHash, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "experiment_id",
            "run_id",
            "method",
        ):
            _require_text(getattr(self, field_name), field_name)
        _require_attempt_id(self.attempt_id)
        _require_run_class(self.run_class)
        _require_prompt_role(self.prompt_role)
        _require_decoding_seed(self.decoding_seed)
        _require_schedule_seed(self.schedule_seed)
        _require_opaque_case_id(self.opaque_case_id)
        _require_int(self.schedule_position, "schedule_position")
        _require_timestamp(self.started_at, "started_at")
        _require_int(self.started_monotonic_ns, "started_monotonic_ns")
        _validate_canonical_json_object(
            self.canonical_request_bytes,
            "canonical_request_bytes",
        )
        _validate_frozen_request(
            self.canonical_request_bytes,
            method=self.method,
            prompt_role=self.prompt_role,
            decoding_seed=self.decoding_seed,
            schedule_seed=self.schedule_seed,
            schedule_position=self.schedule_position,
            opaque_case_id=self.opaque_case_id,
        )
        if type(self.artifact_hashes) is not tuple:
            raise TypeError("artifact_hashes must be a tuple")
        if any(type(item) is not ArtifactHash for item in self.artifact_hashes):
            raise TypeError("artifact_hashes must contain only ArtifactHash values")
        names = tuple(item.name for item in self.artifact_hashes)
        if len(names) != len(set(names)):
            raise ValueError("artifact hash names must be unique")


@dataclass(frozen=True, slots=True)
class ReturnedAttempt:
    attempt_id: str
    prepared_record_sha256: str
    returned_at: str
    ended_monotonic_ns: int
    http_status: int
    raw_http_body: bytes
    exit_code: int | None

    def __post_init__(self) -> None:
        _require_attempt_id(self.attempt_id)
        _require_sha256(self.prepared_record_sha256, "prepared_record_sha256")
        _require_timestamp(self.returned_at, "returned_at")
        _require_int(self.ended_monotonic_ns, "ended_monotonic_ns")
        _require_int(self.http_status, "http_status", minimum=100)
        if self.http_status > 599:
            raise ValueError("http_status must be at most 599")
        if type(self.raw_http_body) is not bytes:
            raise TypeError("raw_http_body must be bytes")
        _require_optional_int(self.exit_code, "exit_code")


@dataclass(frozen=True, slots=True)
class TransportFailedAttempt:
    attempt_id: str
    prepared_record_sha256: str
    failed_at: str
    ended_monotonic_ns: int
    exception_type: str
    exception_message: str
    raw_http_body: bytes | None
    http_status: int | None
    exit_code: int | None

    def __post_init__(self) -> None:
        _require_attempt_id(self.attempt_id)
        _require_sha256(self.prepared_record_sha256, "prepared_record_sha256")
        _require_timestamp(self.failed_at, "failed_at")
        _require_int(self.ended_monotonic_ns, "ended_monotonic_ns")
        _require_text(self.exception_type, "exception_type")
        _require_exception_message(self.exception_message)
        if self.raw_http_body is not None and type(self.raw_http_body) is not bytes:
            raise TypeError("raw_http_body must be bytes or None")
        _require_optional_int(self.http_status, "http_status", minimum=100, maximum=599)
        _require_optional_int(self.exit_code, "exit_code")


@dataclass(frozen=True, slots=True)
class StoredRecord:
    path: Path
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("path must be a Path")
        _require_sha256(self.sha256, "sha256")


@dataclass(frozen=True, slots=True)
class AttemptSnapshot:
    attempt_id: str
    state: AttemptState
    prepared_sha256: str
    terminal_sha256: str | None

    def __post_init__(self) -> None:
        _require_attempt_id(self.attempt_id)
        if type(self.state) is not AttemptState:
            raise TypeError("state must be an AttemptState")
        _require_sha256(self.prepared_sha256, "prepared_sha256")
        if self.terminal_sha256 is not None:
            _require_sha256(self.terminal_sha256, "terminal_sha256")


def _encoded_bytes(raw: bytes) -> dict[str, Any]:
    return {
        "byte_length": len(raw),
        "data_b64": base64.b64encode(raw).decode("ascii"),
        "encoding": "base64",
        "sha256": sha256(raw).hexdigest(),
    }


def _decode_bytes(value: Any, field_name: str) -> bytes:
    if type(value) is not dict or set(value) != {
        "byte_length",
        "data_b64",
        "encoding",
        "sha256",
    }:
        raise ArtifactIntegrityError(f"{field_name} has an invalid byte encoding")
    if value["encoding"] != "base64" or type(value["data_b64"]) is not str:
        raise ArtifactIntegrityError(f"{field_name} has an invalid byte encoding")
    if type(value["byte_length"]) is not int or value["byte_length"] < 0:
        raise ArtifactIntegrityError(f"{field_name} has an invalid byte length")
    try:
        raw = base64.b64decode(value["data_b64"], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ArtifactIntegrityError(f"{field_name} is not valid base64") from exc
    if len(raw) != value["byte_length"]:
        raise ArtifactIntegrityError(f"{field_name} byte length mismatch")
    if type(value["sha256"]) is not str or sha256(raw).hexdigest() != value["sha256"]:
        raise ArtifactIntegrityError(f"{field_name} hash mismatch")
    return raw


def _prepared_record(attempt: PreparedAttempt) -> dict[str, Any]:
    return {
        "artifact_hashes": [
            {"name": item.name, "sha256": item.sha256}
            for item in sorted(attempt.artifact_hashes, key=lambda item: item.name)
        ],
        "attempt_id": attempt.attempt_id,
        "canonical_request": _encoded_bytes(attempt.canonical_request_bytes),
        "decoding_seed": attempt.decoding_seed,
        "experiment_id": attempt.experiment_id,
        "method": attempt.method,
        "opaque_case_id": attempt.opaque_case_id,
        "prompt_role": attempt.prompt_role,
        "record_type": "PREPARED",
        "run_class": attempt.run_class,
        "run_id": attempt.run_id,
        "schedule_position": attempt.schedule_position,
        "schedule_seed": attempt.schedule_seed,
        "schema_version": SCHEMA_VERSION,
        "started_at": attempt.started_at,
        "started_monotonic_ns": attempt.started_monotonic_ns,
    }


def _returned_record(attempt: ReturnedAttempt, duration_ns: int) -> dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "duration_monotonic_ns": duration_ns,
        "ended_monotonic_ns": attempt.ended_monotonic_ns,
        "exit_code": attempt.exit_code,
        "http_status": attempt.http_status,
        "prepared_record_sha256": attempt.prepared_record_sha256,
        "raw_http_body": _encoded_bytes(attempt.raw_http_body),
        "record_type": "RETURNED",
        "returned_at": attempt.returned_at,
        "schema_version": SCHEMA_VERSION,
    }


def _transport_failed_record(
    attempt: TransportFailedAttempt,
    duration_ns: int,
) -> dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "duration_monotonic_ns": duration_ns,
        "ended_monotonic_ns": attempt.ended_monotonic_ns,
        "exception_message": attempt.exception_message,
        "exception_type": attempt.exception_type,
        "exit_code": attempt.exit_code,
        "failed_at": attempt.failed_at,
        "http_status": attempt.http_status,
        "prepared_record_sha256": attempt.prepared_record_sha256,
        "raw_http_body": (
            None if attempt.raw_http_body is None else _encoded_bytes(attempt.raw_http_body)
        ),
        "record_type": "TRANSPORT_FAILED",
        "schema_version": SCHEMA_VERSION,
    }


def _fsync_directory(path: Path) -> None:
    """Best-effort directory fsync; Windows does not expose a portable equivalent."""

    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def _atomic_write_once(path: Path, data: bytes) -> None:
    lock_path = path.parent / f".{path.name}.lock"
    try:
        lock_descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
    except FileExistsError as exc:
        raise FileExistsError(f"refuse concurrent immutable write: {path.name}") from exc
    temporary_path: Path | None = None
    try:
        with os.fdopen(lock_descriptor, "wb") as lock_handle:
            lock_handle.write(b"append-only publication lock\n")
            lock_handle.flush()
            os.fsync(lock_handle.fileno())
        _fsync_directory(path.parent)
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"refuse to overwrite immutable record: {path.name}")
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"refuse to overwrite immutable record: {path.name}")
        # A same-directory hard link publishes the fully fsynced inode only if the
        # destination is still absent.  Unlike os.replace(), it cannot overwrite a
        # writer that wins the race after our existence check.  If a filesystem
        # cannot provide hard links, fail closed instead of weakening immutability.
        os.link(temporary_path, path)
        _fsync_directory(path.parent)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
        if lock_path.exists():
            lock_path.unlink()
            _fsync_directory(path.parent)


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _strict_record(raw: bytes, path: Path) -> dict[str, Any]:
    if type(raw) is not bytes:
        raise ArtifactIntegrityError(f"record reader did not return bytes: {path}")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactIntegrityError(f"record is not valid UTF-8 JSON: {path}") from exc
    if type(value) is not dict or canonical_json_bytes(value) != raw:
        raise ArtifactIntegrityError(f"record is not canonical JSON: {path}")
    return value


def _expect_keys(record: Mapping[str, Any], expected: set[str], record_name: str) -> None:
    if set(record) != expected:
        raise ArtifactIntegrityError(f"{record_name} record fields do not match schema")


_PREPARED_KEYS = {
    "artifact_hashes",
    "attempt_id",
    "canonical_request",
    "decoding_seed",
    "experiment_id",
    "method",
    "opaque_case_id",
    "prompt_role",
    "record_type",
    "run_class",
    "run_id",
    "schedule_position",
    "schedule_seed",
    "schema_version",
    "started_at",
    "started_monotonic_ns",
}
_RETURNED_KEYS = {
    "attempt_id",
    "duration_monotonic_ns",
    "ended_monotonic_ns",
    "exit_code",
    "http_status",
    "prepared_record_sha256",
    "raw_http_body",
    "record_type",
    "returned_at",
    "schema_version",
}
_FAILED_KEYS = {
    "attempt_id",
    "duration_monotonic_ns",
    "ended_monotonic_ns",
    "exception_message",
    "exception_type",
    "exit_code",
    "failed_at",
    "http_status",
    "prepared_record_sha256",
    "raw_http_body",
    "record_type",
    "schema_version",
}


class AttemptStore:
    """Persist and audit one directory per immutable transport attempt."""

    def __init__(
        self,
        root: Path,
        *,
        atomic_writer: AtomicWriter | None = None,
        reader: Reader | None = None,
    ) -> None:
        if not isinstance(root, Path):
            raise TypeError("root must be a Path")
        if not root.exists():
            raise FileNotFoundError(f"artifact root does not exist: {root}")
        if root.is_symlink() or not root.is_dir():
            raise NotADirectoryError(f"artifact root must be a real directory: {root}")
        if atomic_writer is not None and not callable(atomic_writer):
            raise TypeError("atomic_writer must be callable")
        if reader is not None and not callable(reader):
            raise TypeError("reader must be callable")
        self._root = root.resolve(strict=True)
        self._atomic_writer = atomic_writer or _atomic_write_once
        self._reader = reader or _read_bytes

    def write_prepared(self, attempt: PreparedAttempt) -> StoredRecord:
        if type(attempt) is not PreparedAttempt:
            raise TypeError("attempt must be a PreparedAttempt")
        attempt_dir = self._attempt_path(attempt.attempt_id)
        try:
            attempt_dir.mkdir()
        except FileExistsError as exc:
            raise FileExistsError(f"attempt already exists: {attempt.attempt_id}") from exc
        _fsync_directory(self._root)
        return self._write_verified(
            attempt_dir / "prepared.json",
            canonical_json_bytes(_prepared_record(attempt)),
        )

    def write_returned(self, attempt: ReturnedAttempt) -> StoredRecord:
        if type(attempt) is not ReturnedAttempt:
            raise TypeError("attempt must be a ReturnedAttempt")
        prepared, prepared_digest = self._load_prepared(attempt.attempt_id)
        self._require_parent_hash(attempt.prepared_record_sha256, prepared_digest)
        duration_ns = self._duration(prepared, attempt.ended_monotonic_ns)
        return self._write_terminal(
            attempt.attempt_id,
            canonical_json_bytes(_returned_record(attempt, duration_ns)),
        )

    def write_returned_then_parse(
        self,
        attempt: ReturnedAttempt,
        parser: Callable[[bytes], _T],
    ) -> _T:
        if not callable(parser):
            raise TypeError("parser must be callable")
        self.write_returned(attempt)
        return parser(attempt.raw_http_body)

    def write_transport_failed(self, attempt: TransportFailedAttempt) -> StoredRecord:
        if type(attempt) is not TransportFailedAttempt:
            raise TypeError("attempt must be a TransportFailedAttempt")
        prepared, prepared_digest = self._load_prepared(attempt.attempt_id)
        self._require_parent_hash(attempt.prepared_record_sha256, prepared_digest)
        duration_ns = self._duration(prepared, attempt.ended_monotonic_ns)
        return self._write_terminal(
            attempt.attempt_id,
            canonical_json_bytes(_transport_failed_record(attempt, duration_ns)),
        )

    def scan_attempts(self) -> tuple[AttemptSnapshot, ...]:
        snapshots: list[AttemptSnapshot] = []
        for attempt_dir in sorted(self._root.iterdir(), key=lambda path: path.name):
            _require_attempt_id(attempt_dir.name)
            if attempt_dir.is_symlink() or not attempt_dir.is_dir():
                raise ArtifactIntegrityError(
                    f"attempt entry is not a real directory: {attempt_dir.name}"
                )
            entries = {entry.name for entry in attempt_dir.iterdir()}
            terminal_inflight = {
                name
                for name in entries
                if name == ".terminal.json.lock"
                or (name.startswith(".terminal.json.") and name.endswith(".tmp"))
            }
            unexpected = entries - {"prepared.json", "terminal.json"} - terminal_inflight
            if unexpected:
                raise ArtifactIntegrityError(
                    f"attempt directory has unexpected entries: {attempt_dir.name}"
                )
            prepared, prepared_digest = self._read_prepared_path(
                attempt_dir / "prepared.json",
                attempt_dir.name,
            )
            terminal_path = attempt_dir / "terminal.json"
            if not terminal_path.exists():
                snapshots.append(
                    AttemptSnapshot(
                        attempt_id=attempt_dir.name,
                        state=AttemptState.INCOMPLETE_ATTEMPT,
                        prepared_sha256=prepared_digest,
                        terminal_sha256=None,
                    )
                )
                continue
            if terminal_path.is_symlink() or not terminal_path.is_file():
                raise ArtifactIntegrityError(
                    f"terminal record is not a real file: {attempt_dir.name}"
                )
            terminal_raw = self._reader(terminal_path)
            if terminal_inflight:
                raise ArtifactIntegrityError(
                    f"terminal publication has orphaned files: {attempt_dir.name}"
                )
            terminal = _strict_record(terminal_raw, terminal_path)
            state = self._validate_terminal(
                terminal,
                attempt_dir.name,
                prepared,
                prepared_digest,
            )
            snapshots.append(
                AttemptSnapshot(
                    attempt_id=attempt_dir.name,
                    state=state,
                    prepared_sha256=prepared_digest,
                    terminal_sha256=sha256(terminal_raw).hexdigest(),
                )
            )
        return tuple(snapshots)

    def _attempt_path(self, attempt_id: str) -> Path:
        _require_attempt_id(attempt_id)
        candidate = self._root / attempt_id
        if candidate.parent != self._root:
            raise ValueError("attempt_id escapes artifact root")
        return candidate

    def _write_verified(self, path: Path, data: bytes) -> StoredRecord:
        if path.exists():
            raise FileExistsError(f"refuse to overwrite immutable record: {path.name}")
        self._atomic_writer(path, data)
        if not path.is_file() or path.is_symlink():
            raise ArtifactIntegrityError(f"atomic writer did not create a real file: {path}")
        readback = self._reader(path)
        if type(readback) is not bytes or readback != data:
            raise ArtifactIntegrityError(f"record readback mismatch: {path}")
        return StoredRecord(path=path, sha256=sha256(readback).hexdigest())

    def _write_terminal(self, attempt_id: str, data: bytes) -> StoredRecord:
        attempt_dir = self._attempt_path(attempt_id)
        terminal_path = attempt_dir / "terminal.json"
        if terminal_path.exists():
            raise FileExistsError(f"terminal record already exists: {attempt_id}")
        return self._write_verified(terminal_path, data)

    def _load_prepared(self, attempt_id: str) -> tuple[dict[str, Any], str]:
        attempt_dir = self._attempt_path(attempt_id)
        if not attempt_dir.exists():
            raise FileNotFoundError(f"attempt does not exist: {attempt_id}")
        if attempt_dir.is_symlink() or not attempt_dir.is_dir():
            raise ArtifactIntegrityError(f"attempt path is not a real directory: {attempt_id}")
        terminal_path = attempt_dir / "terminal.json"
        if terminal_path.exists():
            raise FileExistsError(f"terminal record already exists: {attempt_id}")
        entries = {entry.name for entry in attempt_dir.iterdir()}
        terminal_inflight = any(
            name == ".terminal.json.lock"
            or (name.startswith(".terminal.json.") and name.endswith(".tmp"))
            for name in entries
        )
        if terminal_inflight:
            raise FileExistsError(f"terminal record already exists or is in progress: {attempt_id}")
        if not entries.issubset({"prepared.json"}):
            raise ArtifactIntegrityError(
                f"attempt directory has unexpected entries: {attempt_id}"
            )
        return self._read_prepared_path(attempt_dir / "prepared.json", attempt_id)

    def _read_prepared_path(
        self,
        prepared_path: Path,
        attempt_id: str,
    ) -> tuple[dict[str, Any], str]:
        if not prepared_path.is_file() or prepared_path.is_symlink():
            raise ArtifactIntegrityError(f"prepared record is missing: {attempt_id}")
        raw = self._reader(prepared_path)
        prepared = _strict_record(raw, prepared_path)
        self._validate_prepared(prepared, attempt_id)
        return prepared, sha256(raw).hexdigest()

    @staticmethod
    def _require_parent_hash(expected: str, observed: str) -> None:
        if expected != observed:
            raise ArtifactIntegrityError("prepared record hash mismatch")

    @staticmethod
    def _duration(prepared: Mapping[str, Any], ended_monotonic_ns: int) -> int:
        started = prepared["started_monotonic_ns"]
        if ended_monotonic_ns < started:
            raise ValueError("ended_monotonic_ns must not precede the prepared start")
        return ended_monotonic_ns - started

    @staticmethod
    def _validate_prepared(record: Mapping[str, Any], attempt_id: str) -> None:
        _expect_keys(record, _PREPARED_KEYS, "PREPARED")
        if record["schema_version"] != SCHEMA_VERSION or record["record_type"] != "PREPARED":
            raise ArtifactIntegrityError("prepared record has wrong schema or type")
        if record["attempt_id"] != attempt_id:
            raise ArtifactIntegrityError("prepared record attempt_id mismatch")
        domain_validators = (
            ("run_class", _require_run_class),
            ("prompt_role", _require_prompt_role),
            ("decoding_seed", _require_decoding_seed),
            ("schedule_seed", _require_schedule_seed),
            ("opaque_case_id", _require_opaque_case_id),
        )
        for field_name, validator in domain_validators:
            try:
                validator(record[field_name])
            except (TypeError, ValueError) as exc:
                raise ArtifactIntegrityError(
                    f"prepared {field_name} is invalid"
                ) from exc
        canonical_request = _decode_bytes(record["canonical_request"], "canonical_request")
        try:
            _validate_frozen_request(
                canonical_request,
                method=record["method"],
                prompt_role=record["prompt_role"],
                decoding_seed=record["decoding_seed"],
                schedule_seed=record["schedule_seed"],
                schedule_position=record["schedule_position"],
                opaque_case_id=record["opaque_case_id"],
            )
        except (TypeError, ValueError) as exc:
            raise ArtifactIntegrityError(
                "prepared record canonical_request violates the frozen request contract"
            ) from exc
        hashes = record["artifact_hashes"]
        if type(hashes) is not list:
            raise ArtifactIntegrityError("prepared artifact_hashes must be a list")
        names: list[str] = []
        for item in hashes:
            if type(item) is not dict or set(item) != {"name", "sha256"}:
                raise ArtifactIntegrityError("prepared artifact hash entry is invalid")
            try:
                name = _require_text(item["name"], "artifact hash name")
                _require_sha256(item["sha256"], "artifact hash sha256")
            except (TypeError, ValueError) as exc:
                raise ArtifactIntegrityError("prepared artifact hash entry is invalid") from exc
            names.append(name)
        if names != sorted(names) or len(names) != len(set(names)):
            raise ArtifactIntegrityError("prepared artifact hash entries are not canonical")
        for field_name in (
            "experiment_id",
            "run_id",
            "method",
        ):
            try:
                _require_text(record[field_name], field_name)
            except (TypeError, ValueError) as exc:
                raise ArtifactIntegrityError(f"prepared {field_name} is invalid") from exc
        try:
            _require_int(record["schedule_position"], "schedule_position")
            _require_timestamp(record["started_at"], "started_at")
            _require_int(record["started_monotonic_ns"], "started_monotonic_ns")
        except (TypeError, ValueError) as exc:
            raise ArtifactIntegrityError("prepared timing or schedule field is invalid") from exc

    @staticmethod
    def _validate_terminal(
        record: Mapping[str, Any],
        attempt_id: str,
        prepared: Mapping[str, Any],
        prepared_digest: str,
    ) -> AttemptState:
        record_type = record.get("record_type")
        if record_type == "RETURNED":
            _expect_keys(record, _RETURNED_KEYS, "RETURNED")
            state = AttemptState.RETURNED
            _decode_bytes(record["raw_http_body"], "raw_http_body")
            timestamp_field = "returned_at"
        elif record_type == "TRANSPORT_FAILED":
            _expect_keys(record, _FAILED_KEYS, "TRANSPORT_FAILED")
            state = AttemptState.TRANSPORT_FAILED
            if record["raw_http_body"] is not None:
                _decode_bytes(record["raw_http_body"], "raw_http_body")
            timestamp_field = "failed_at"
        else:
            raise ArtifactIntegrityError("terminal record has unknown record_type")
        if record["schema_version"] != SCHEMA_VERSION:
            raise ArtifactIntegrityError("terminal record has wrong schema version")
        if record["attempt_id"] != attempt_id:
            raise ArtifactIntegrityError("terminal record attempt_id mismatch")
        if record["prepared_record_sha256"] != prepared_digest:
            raise ArtifactIntegrityError("terminal prepared record hash mismatch")
        try:
            _require_timestamp(record[timestamp_field], timestamp_field)
            ended = _require_int(record["ended_monotonic_ns"], "ended_monotonic_ns")
            duration = _require_int(record["duration_monotonic_ns"], "duration_monotonic_ns")
            if duration != ended - prepared["started_monotonic_ns"] or duration < 0:
                raise ValueError("duration mismatch")
            if state is AttemptState.RETURNED:
                _require_int(record["http_status"], "http_status", minimum=100)
                if record["http_status"] > 599:
                    raise ValueError("http_status must be at most 599")
            else:
                _require_optional_int(
                    record["http_status"],
                    "http_status",
                    minimum=100,
                    maximum=599,
                )
            _require_optional_int(record["exit_code"], "exit_code")
            if state is AttemptState.TRANSPORT_FAILED:
                _require_text(record["exception_type"], "exception_type")
                _require_exception_message(record["exception_message"])
        except (TypeError, ValueError) as exc:
            raise ArtifactIntegrityError("terminal field validation failed") from exc
        return state
