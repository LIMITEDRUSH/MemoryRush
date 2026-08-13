import pytest

from memoryrush.admission import (
    AtomicClaim,
    CandidateClaim,
    EvidenceSpan,
    ExactCopyVerifier,
    IdOnlyVerifier,
    QualifierKind,
    QualifierSlot,
    StaticOracleVerifier,
    SupportCell,
    SupportLabel,
    Verifier,
)


def _span(span_id: str, text: str) -> EvidenceSpan:
    return EvidenceSpan(
        span_id=span_id,
        document_id="doc-001",
        paragraph_id=f"p_{span_id}",
        text=text,
        start_char=0,
        end_char=len(text),
        source_sha256="a" * 64,
    )


def _candidate() -> CandidateClaim:
    return CandidateClaim(
        candidate_id="candidate-001",
        proposition="The system may reduce latency. The trial ended in 2025.",
        atomic_claims=(
            AtomicClaim(
                claim_id="latency",
                text="The system may reduce latency.",
                qualifiers=(
                    QualifierSlot(QualifierKind.MODALITY, "may"),
                    QualifierSlot(QualifierKind.CONDITION, "under peak load"),
                ),
            ),
            AtomicClaim(
                claim_id="end-date",
                text="The trial ended in 2025.",
                qualifiers=(QualifierSlot(QualifierKind.TIME, "2025"),),
            ),
        ),
    )


def test_id_only_is_explicit_total_structural_false_positive_baseline() -> None:
    candidate = _candidate()
    spans = (_span("001", "Unrelated text."), _span("002", "More unrelated text."))
    verifier = IdOnlyVerifier()

    matrix = verifier.build_support_matrix(candidate, spans)

    assert isinstance(verifier, Verifier)
    assert len(matrix.cells) == len(candidate.atomic_claims) * len(spans)
    for claim in candidate.atomic_claims:
        for span in spans:
            cell = matrix.cell(claim.claim_id, span.span_id)
            assert cell.label is SupportLabel.SUPPORTS
            assert cell.supported_qualifiers == claim.qualifiers
            assert "structural false-positive baseline" in cell.rationale


def test_exact_copy_supports_normalized_boundary_copy_only() -> None:
    candidate = _candidate()
    span = _span(
        "001",
        "Finding: THE   system may reduce latency. The condition was not reported.",
    )

    matrix = ExactCopyVerifier().build_support_matrix(candidate, (span,))

    latency = matrix.cell("latency", "001")
    assert latency.label is SupportLabel.SUPPORTS
    assert latency.supported_qualifiers == (
        QualifierSlot(QualifierKind.MODALITY, "may"),
    )
    assert matrix.cell("end-date", "001").label is SupportLabel.INSUFFICIENT


def test_exact_copy_rejects_semantic_paraphrase_without_inference() -> None:
    candidate = CandidateClaim(
        candidate_id="candidate-paraphrase",
        proposition="The system may reduce latency.",
        atomic_claims=(
            AtomicClaim(
                claim_id="latency",
                text="The system may reduce latency.",
                qualifiers=(QualifierSlot(QualifierKind.MODALITY, "may"),),
            ),
        ),
    )
    paraphrase = _span("001", "Latency could be reduced by the system.")

    cell = ExactCopyVerifier().build_support_matrix(candidate, (paraphrase,)).cells[0]

    assert cell.label is SupportLabel.INSUFFICIENT
    assert cell.supported_qualifiers == ()


def test_exact_copy_requires_text_boundaries() -> None:
    candidate = CandidateClaim(
        candidate_id="candidate-boundary",
        proposition="cat",
        atomic_claims=(AtomicClaim(claim_id="short", text="cat"),),
    )

    cell = ExactCopyVerifier().build_support_matrix(
        candidate,
        (_span("001", "The category is concatenate."),),
    ).cells[0]

    assert cell.label is SupportLabel.INSUFFICIENT


def test_static_oracle_returns_the_supplied_total_matrix() -> None:
    candidate = _candidate()
    spans = (_span("001", "First span."), _span("002", "Second span."))
    annotations = (
        SupportCell("latency", "001", SupportLabel.SUPPORTS),
        SupportCell("latency", "002", SupportLabel.INSUFFICIENT),
        SupportCell("end-date", "001", SupportLabel.CONTRADICTS),
        SupportCell(
            "end-date",
            "002",
            SupportLabel.SUPPORTS,
            supported_qualifiers=(QualifierSlot(QualifierKind.TIME, "2025"),),
        ),
    )

    matrix = StaticOracleVerifier(annotations).build_support_matrix(candidate, spans)

    assert matrix.candidate is candidate
    assert matrix.evidence_spans == spans
    assert matrix.cells == annotations


def test_static_oracle_rejects_missing_annotations() -> None:
    candidate = _candidate()
    spans = (_span("001", "First span."), _span("002", "Second span."))
    incomplete = (
        SupportCell("latency", "001", SupportLabel.SUPPORTS),
        SupportCell("latency", "002", SupportLabel.INSUFFICIENT),
        SupportCell("end-date", "001", SupportLabel.CONTRADICTS),
    )

    with pytest.raises(ValueError, match="missing oracle annotations"):
        StaticOracleVerifier(incomplete).build_support_matrix(candidate, spans)


def test_static_oracle_rejects_duplicate_annotations() -> None:
    candidate = _candidate()
    spans = (_span("001", "First span."),)
    duplicate = SupportCell("latency", "001", SupportLabel.INSUFFICIENT)
    annotations = (
        duplicate,
        duplicate,
        SupportCell("end-date", "001", SupportLabel.INSUFFICIENT),
    )

    with pytest.raises(ValueError, match="duplicate oracle annotations"):
        StaticOracleVerifier(annotations).build_support_matrix(candidate, spans)


@pytest.mark.parametrize(
    "bad_cell",
    [
        SupportCell("unknown-claim", "001", SupportLabel.SUPPORTS),
        SupportCell("latency", "unknown-span", SupportLabel.SUPPORTS),
    ],
)
def test_static_oracle_rejects_unknown_claim_or_span_references(
    bad_cell: SupportCell,
) -> None:
    candidate = _candidate()
    spans = (_span("001", "First span."),)
    annotations = (
        bad_cell,
        SupportCell("latency", "001", SupportLabel.INSUFFICIENT),
        SupportCell("end-date", "001", SupportLabel.INSUFFICIENT),
    )

    with pytest.raises(ValueError, match="unknown oracle references"):
        StaticOracleVerifier(annotations).build_support_matrix(candidate, spans)
