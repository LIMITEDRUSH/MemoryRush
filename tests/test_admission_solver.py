from memoryrush.admission import (
    AtomicClaim,
    CandidateClaim,
    EvidenceSpan,
    InclusionMinimalSolver,
    MinimumCardinalitySolver,
    QualifierKind,
    QualifierSlot,
    SupportCell,
    SupportLabel,
    SupportMatrix,
    audit_evidence_deletions,
    evaluate_sufficiency,
)


def _span(span_id: str, text: str) -> EvidenceSpan:
    return EvidenceSpan(
        span_id=span_id,
        document_id="doc-001",
        paragraph_id=f"p_{span_id}",
        text=text,
        start_char=0,
        end_char=len(text),
        source_sha256="c" * 64,
    )


def _cross_span_matrix() -> SupportMatrix:
    candidate = CandidateClaim(
        candidate_id="candidate-cross-span",
        proposition="The 120-person trial ended in 2025.",
        atomic_claims=(
            AtomicClaim(
                claim_id="participants",
                text="The trial had 120 participants.",
                qualifiers=(QualifierSlot(QualifierKind.QUANTIFIER, "120"),),
            ),
            AtomicClaim(
                claim_id="end-date",
                text="The trial ended in 2025.",
                qualifiers=(QualifierSlot(QualifierKind.TIME, "2025"),),
            ),
        ),
    )
    participants = _span("001", "The trial enrolled 120 participants.")
    end_date = _span("002", "Follow-up ended in 2025.")
    return SupportMatrix(
        candidate=candidate,
        evidence_spans=(participants, end_date),
        cells=(
            SupportCell(
                "participants",
                "001",
                SupportLabel.SUPPORTS,
                supported_qualifiers=(QualifierKind.QUANTIFIER,),
            ),
            SupportCell("participants", "002", SupportLabel.INSUFFICIENT),
            SupportCell("end-date", "001", SupportLabel.INSUFFICIENT),
            SupportCell(
                "end-date",
                "002",
                SupportLabel.SUPPORTS,
                supported_qualifiers=(QualifierKind.TIME,),
            ),
        ),
    )


def test_solver_requires_joint_cross_span_support() -> None:
    matrix = _cross_span_matrix()

    solutions = InclusionMinimalSolver().solve(matrix)

    assert [solution.selected_span_ids for solution in solutions] == [("001", "002")]
    assert solutions[0].sufficiency.is_sufficient


def test_deletion_audit_proves_each_selected_span_is_necessary() -> None:
    matrix = _cross_span_matrix()
    solution = InclusionMinimalSolver().solve(matrix)[0]

    audit = audit_evidence_deletions(matrix, solution.selected_span_ids)

    assert audit.is_inclusion_minimal
    assert {trial.deleted_span_id: trial.remains_sufficient for trial in audit.trials} == {
        "001": False,
        "002": False,
    }


def test_inclusion_minimal_retains_larger_alternative_but_cardinality_solver_does_not() -> None:
    candidate = CandidateClaim(
        candidate_id="candidate-alternatives",
        proposition="A and B are supported.",
        atomic_claims=(
            AtomicClaim("claim-a", "A is supported."),
            AtomicClaim("claim-b", "B is supported."),
        ),
    )
    span_a = _span("a", "A is supported.")
    span_b = _span("b", "B is supported.")
    span_joint = _span("joint", "A and B are supported.")
    matrix = SupportMatrix(
        candidate=candidate,
        evidence_spans=(span_a, span_b, span_joint),
        cells=(
            SupportCell("claim-a", "a", SupportLabel.SUPPORTS),
            SupportCell("claim-a", "b", SupportLabel.INSUFFICIENT),
            SupportCell("claim-a", "joint", SupportLabel.SUPPORTS),
            SupportCell("claim-b", "a", SupportLabel.INSUFFICIENT),
            SupportCell("claim-b", "b", SupportLabel.SUPPORTS),
            SupportCell("claim-b", "joint", SupportLabel.SUPPORTS),
        ),
    )

    inclusion_solutions = InclusionMinimalSolver().solve(matrix)
    cardinality_solutions = MinimumCardinalitySolver().solve(matrix)

    assert {solution.selected_span_ids for solution in inclusion_solutions} == {
        ("a", "b"),
        ("joint",),
    }
    assert [solution.selected_span_ids for solution in cardinality_solutions] == [("joint",)]


def test_contradicting_selected_evidence_blocks_sufficiency() -> None:
    matrix = _cross_span_matrix()
    contradiction = _span("003", "The trial did not end in 2025.")
    extended = SupportMatrix(
        candidate=matrix.candidate,
        evidence_spans=(*matrix.evidence_spans, contradiction),
        cells=(
            *matrix.cells,
            SupportCell("participants", "003", SupportLabel.INSUFFICIENT),
            SupportCell("end-date", "003", SupportLabel.CONTRADICTS),
        ),
    )

    result = evaluate_sufficiency(extended, ("001", "002", "003"))

    assert not result.is_sufficient
    assert result.contradicted_claim_ids == ("end-date",)


def test_missing_qualifier_support_is_reported_separately() -> None:
    matrix = _cross_span_matrix()
    cells = tuple(
        SupportCell(cell.claim_id, cell.span_id, cell.label)
        if cell.claim_id == "end-date" and cell.span_id == "002"
        else cell
        for cell in matrix.cells
    )
    without_time_support = SupportMatrix(
        candidate=matrix.candidate,
        evidence_spans=matrix.evidence_spans,
        cells=cells,
    )

    result = evaluate_sufficiency(without_time_support, ("001", "002"))

    assert not result.is_sufficient
    assert result.missing_qualifiers == {"end-date": (QualifierKind.TIME,)}

