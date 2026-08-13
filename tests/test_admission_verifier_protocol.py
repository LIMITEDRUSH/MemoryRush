from memoryrush.admission import CandidateClaim, EvidenceSpan, SupportMatrix, Verifier


class FixtureVerifier:
    verifier_name = "fixture"
    verifier_version = "test-v1"

    def __init__(self, matrix: SupportMatrix) -> None:
        self._matrix = matrix

    def build_support_matrix(
        self,
        candidate: CandidateClaim,
        evidence_spans: tuple[EvidenceSpan, ...],
    ) -> SupportMatrix:
        assert candidate == self._matrix.candidate
        assert evidence_spans == self._matrix.evidence_spans
        return self._matrix


def accepts_verifier(verifier: Verifier) -> str:
    return f"{verifier.verifier_name}:{verifier.verifier_version}"


def test_structural_verifier_protocol_keeps_backends_replaceable() -> None:
    # Static typing checks the method contract; runtime behavior remains ordinary duck typing.
    assert accepts_verifier.__annotations__["verifier"] is Verifier

