"""Materialize the frozen Direction 1 synthetic case catalog as canonical JSONL.

The catalog is research-authored, not human gold.  This builder preserves that
provenance distinction and derives offsets, source digests, the total support
matrix, and inclusion-minimal evidence certificates deterministically.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

# Support both ``python -m scripts...`` and the documented direct invocation
# ``python scripts/build_...py`` without requiring an editable installation.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from memoryrush.admission.benchmark import (
    SUPPORTED_SCHEMA_VERSION,
    parse_benchmark_case,
)
from memoryrush.admission.models import (
    AtomicClaim,
    CandidateClaim,
    EvidenceSpan,
    QualifierKind,
    QualifierSlot,
    SupportCell,
    SupportLabel,
    SupportMatrix,
)
from memoryrush.admission.solver import InclusionMinimalSolver


DEFAULT_OUTPUT = REPOSITORY_ROOT / "data/benchmarks/direction1_synthetic_v0_1.jsonl"

# The prose catalog uses readable upper-case operator names.  The loader uses
# these stable lower-case identifiers.  This explicit map prevents silent drift.
CATALOG_OPERATOR_MAP = {
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

SOURCE_BLOCKS = {
    "B-DUP-01": ("MSG-C001", "MSG-C022"),
    "B-ENTITY-01": ("MSG-C005", "MSG-C006", "MSG-C031"),
    "B-NUMDATE-01": ("MSG-C007", "MSG-C008", "MSG-C009"),
    "B-NEG-01": ("MSG-C010", "MSG-C011", "MSG-C030"),
    "B-EPI-MODCOND-01": ("MSG-C012", "MSG-C013", "MSG-C016", "MSG-C032"),
    "B-DEONTIC-01": ("MSG-C014", "MSG-C015"),
    "B-SCOPE-01": ("MSG-C017", "MSG-C018"),
    "B-ATTR-01": ("MSG-C019", "MSG-C020"),
    "B-OVERCOMPOSE-01": ("MSG-C034", "MSG-C035"),
}

HIGH_RISK_NOT_HUMAN_GOLD = {"MSG-C014", "MSG-C023", "MSG-C026"}
# These positive shams preserve semantics only by an agent-authored judgment;
# they retain paired operator metadata but are not mechanical-label oracles.
AGENT_AUTHORED_SEMANTIC_SHAMS = {"MSG-C030", "MSG-C031", "MSG-C032"}
# These cases contain a registered surface edit, but their expected semantic
# label is not mechanically entailed by that edit alone.  Preserve the pair
# metadata while keeping the annotation agent-authored and provisional.
NON_MECHANICAL_SEMANTIC_CASES = {"MSG-C014", "MSG-C034"}


@dataclass(frozen=True)
class ClaimSpec:
    text: str
    qualifiers: tuple[tuple[str, str], ...] = ()
    required_support_parts: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceSpec:
    paragraph: int
    excerpt: str | None = None


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    family: str
    block_id: str
    proposition: str
    claims: tuple[ClaimSpec, ...]
    evidence: tuple[EvidenceSpec, ...]
    labels: tuple[tuple[str, ...], ...]
    decision: str
    reason: str
    base_case_id: str | None = None
    catalog_operator: str | None = None
    self_sufficiency: str = "PASS"
    minimality: str = "PASS"
    # Optional claim x span matrix of qualifier indexes that remain supported
    # even when the whole cell is partial/contradictory/ambiguous.
    qualifier_support: tuple[tuple[tuple[int, ...], ...], ...] | None = None


def q(*slots: tuple[str, str]) -> tuple[tuple[str, str], ...]:
    return slots


DOCUMENTS: dict[str, tuple[str, ...]] = {
    "B-DUP-01": (
        "The Harbor Learning Lab replaces the blue intake filter every 30 days during routine operation.",
    ),
    "C002": ("On weekdays, the Maple Archive opens its quiet study room at 08:30.",),
    "C003": (
        "The Willow trial enrolled 120 volunteers.",
        "Follow-up for the Willow trial ended on 18 September 2025.",
    ),
    "C004": (
        "The Cedar greenhouse controller closes the roof vent only when wind speed exceeds 40 kilometers per hour.",
        "On 14 May 2026, the sensor recorded 46 kilometers per hour at 14:10, and the controller log recorded a completed roof-vent closure at 14:11.",
    ),
    "B-ENTITY-01": (
        "The North Workshop stores the calibrated torque wrench in cabinet 4 after each inspection.",
    ),
    "B-NUMDATE-01": (
        "The Amber ferry drill began on 12 March 2026 with 48 participants.",
    ),
    "B-NEG-01": (
        "At no point during the overnight test did the rainwater pump operate.",
    ),
    "B-EPI-MODCOND-01": (
        "During peak load, the new scheduler may reduce queue latency by up to 15 percent.",
    ),
    "B-DEONTIC-01": (
        "Before entering the clean room, visitors must wear sealed shoe covers.",
    ),
    "B-SCOPE-01": (
        "Only staff assigned to the night shift may unlock the west entrance after 22:00.",
    ),
    "B-ATTR-01": (
        "In her inspection note, engineer Mira Sol described the western seal as likely to need replacement before winter.",
    ),
    "C021": (
        "The Quartz observatory installed a new humidity sensor beside the telescope dome.",
        "Its maintenance handbook explains how humidity can affect mirror coatings.",
    ),
    "C023": (
        "The Lark clinic's backup generator successfully completed its weekly self-test on Friday.",
        "Friday's weekly diagnostic for the Lark clinic backup generator finished successfully.",
    ),
    "C024": (
        "The first status bulletin says the River Gate inspection finished on 2 June 2026.",
        "A later status bulletin says the River Gate inspection finished on 3 June 2026, and it does not state that the earlier bulletin was corrected.",
    ),
    "C025": (
        "An early notice listed the Solace Hall rehearsal at 18:00.",
        "The final notice explicitly cancels the 18:00 listing and reschedules the Solace Hall rehearsal to 19:30.",
    ),
    "C026": (
        "Mara spoke with Lia after the sensor review. She said the calibration note was incomplete.",
    ),
    "C027": (
        "The checklist says the auxiliary fan starts when temperature is above 30 degrees Celsius.",
        "The event log records exactly 30.0 degrees Celsius and a fan-start event at the same timestamp, but it does not identify whether the auxiliary or main fan started.",
    ),
    "C028": ("The Aurora sampling cart reached Bay 6 at noon.",),
    "C029": (
        "The Pine courier delivered two sealed sample boxes to Lab C.",
        "The delivery log records arrival at 16:20.",
    ),
    "C033": (
        "The Delta Field Team collected 18 soil cores.",
        "The collection log dates that batch to 7 April 2026.",
        "Analyst Nia Verne recorded that all 18 cores were transferred to cold storage.",
    ),
    "B-OVERCOMPOSE-01": (
        "The safety guide says an alert should be sent if tank pressure exceeds 8 bar.",
        "Operator Jo Lin recorded a pressure of 8.6 bar at 11:05 and wrote that an alert was sent.",
    ),
    "C036": (
        "The Elm survey included 64 households.",
        "The field note dates the Elm survey to October 2025.",
        "A summary card states that the 64-household Elm survey was conducted in October 2025.",
    ),
}


CASES: tuple[CaseSpec, ...] = (
    CaseSpec(
        "MSG-C001", "F01 fully supported single-span", "B-DUP-01",
        "During routine operation, the Harbor Learning Lab replaces its blue intake filter every 30 days.",
        (ClaimSpec("Harbor Learning Lab replaces the blue intake filter", q(("scope", "during routine operation"), ("quantifier", "every 30 days"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C002", "F01 fully supported single-span", "C002",
        "The Maple Archive's quiet study room opens at 08:30 on weekdays.",
        (ClaimSpec("Maple Archive opens its quiet study room", q(("time", "08:30"), ("scope", "weekdays"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C003", "F02 jointly supported cross-span", "C003",
        "The Willow trial enrolled 120 volunteers and ended follow-up on 18 September 2025.",
        (
            ClaimSpec("The Willow trial enrolled volunteers", q(("quantifier", "120 volunteers"),)),
            ClaimSpec("The Willow trial ended follow-up", q(("time", "18 September 2025"),)),
        ),
        (EvidenceSpec(0), EvidenceSpec(1)),
        (("supports", "insufficient"), ("insufficient", "supports")),
        "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C004", "F02 jointly supported cross-span", "C004",
        "On 14 May 2026, the Cedar greenhouse controller closed the roof vent after the recorded wind speed exceeded its 40-kilometer-per-hour threshold.",
        (
            ClaimSpec("The controller's closure threshold is wind above 40 kilometers per hour", q(("condition", "only when wind exceeds 40 kilometers per hour"),)),
            ClaimSpec("A 46-kilometer-per-hour reading preceded a completed roof-vent closure", q(("time", "14 May 2026"),)),
        ),
        (
            EvidenceSpec(0),
            EvidenceSpec(1),
        ),
        (("supports", "insufficient"), ("insufficient", "supports")),
        "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C005", "F03 entity replacement", "B-ENTITY-01",
        "After each inspection, the North Workshop stores the calibrated torque wrench in cabinet 4.",
        (ClaimSpec("North Workshop stores the calibrated torque wrench", q(("entity", "North Workshop"), ("object", "cabinet 4"), ("time", "after each inspection"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C006", "F03 entity replacement", "B-ENTITY-01",
        "After each inspection, the South Workshop stores the calibrated torque wrench in cabinet 4.",
        (ClaimSpec("South Workshop stores the calibrated torque wrench", q(("entity", "South Workshop"), ("object", "cabinet 4"), ("time", "after each inspection"))),),
        (EvidenceSpec(0),), (("insufficient",),), "REJECT", "insufficient_evidence",
        "MSG-C005", "ENTITY_REPLACE", qualifier_support=(((1, 2),),),
    ),
    CaseSpec(
        "MSG-C007", "F04 number/date replacement", "B-NUMDATE-01",
        "Forty-eight participants joined the Amber ferry drill when it began on 12 March 2026.",
        (ClaimSpec("The Amber ferry drill began with participants", q(("quantifier", "48 participants"), ("time", "12 March 2026"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C008", "F04 number/date replacement", "B-NUMDATE-01",
        "Eighty-four participants joined the Amber ferry drill when it began on 12 March 2026.",
        (ClaimSpec("The Amber ferry drill began with participants", q(("quantifier", "84 participants"), ("time", "12 March 2026"))),),
        (EvidenceSpec(0),),
        (("contradicts",),), "REJECT", "contradicted", "MSG-C007", "NUMBER_REPLACE",
        qualifier_support=(((1,),),),
    ),
    CaseSpec(
        "MSG-C009", "F04 number/date replacement", "B-NUMDATE-01",
        "Forty-eight participants joined the Amber ferry drill when it began on 21 March 2026.",
        (ClaimSpec("The Amber ferry drill began with participants", q(("quantifier", "48 participants"), ("time", "21 March 2026"))),),
        (EvidenceSpec(0),), (("contradicts",),), "REJECT", "contradicted",
        "MSG-C007", "DATE_REPLACE", qualifier_support=(((0,),),),
    ),
    CaseSpec(
        "MSG-C010", "F05 negation flip", "B-NEG-01",
        "During the overnight test, the rainwater pump did not operate.",
        (ClaimSpec("The rainwater pump did not operate", q(("negation", "not operate"), ("scope", "overnight test"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C011", "F05 negation flip", "B-NEG-01",
        "During the overnight test, the rainwater pump operated.",
        (ClaimSpec("The rainwater pump operated", q(("negation", "affirmed operation"), ("scope", "overnight test"))),),
        (EvidenceSpec(0),), (("contradicts",),), "REJECT", "contradicted",
        "MSG-C010", "NEGATION_FLIP", qualifier_support=(((1,),),),
    ),
    CaseSpec(
        "MSG-C012", "F06 modality strengthening/weakening", "B-EPI-MODCOND-01",
        "During peak load, the new scheduler may reduce queue latency by up to 15 percent.",
        (ClaimSpec("The new scheduler may reduce queue latency", q(("condition", "during peak load"), ("modality", "may"), ("quantifier", "up to 15 percent"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C013", "F06 modality strengthening/weakening", "B-EPI-MODCOND-01",
        "During peak load, the new scheduler reduces queue latency by up to 15 percent.",
        (ClaimSpec("The new scheduler reduces queue latency", q(("condition", "during peak load"), ("modality", "asserted actual"), ("quantifier", "up to 15 percent"))),),
        (EvidenceSpec(0),), (("supports",),), "REJECT", "partially_supported",
        "MSG-C012", "MODALITY_STRENGTHEN", qualifier_support=(((0, 2),),),
    ),
    CaseSpec(
        "MSG-C014", "F06 modality strengthening/weakening", "B-DEONTIC-01",
        "Before entering the clean room, visitors may wear sealed shoe covers.",
        (ClaimSpec("Visitors may wear sealed shoe covers", q(("condition", "before entering the clean room"), ("modality", "permission"))),),
        (EvidenceSpec(0),), (("contradicts",),), "REJECT", "contradicted",
        "MSG-C015", "MODALITY_WEAKEN", qualifier_support=(((0,),),),
    ),
    CaseSpec(
        "MSG-C015", "F06 modality strengthening/weakening", "B-DEONTIC-01",
        "Visitors must wear sealed shoe covers before they enter the clean room.",
        (ClaimSpec("Visitors must wear sealed shoe covers", q(("condition", "before entering the clean room"), ("modality", "must"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C016", "F07 deleted condition/temporal scope/quantifier", "B-EPI-MODCOND-01",
        "The new scheduler may reduce queue latency by up to 15 percent.",
        (ClaimSpec("The new scheduler may reduce queue latency", q(("condition", "unrestricted operating conditions"), ("modality", "may"), ("quantifier", "up to 15 percent"))),),
        (EvidenceSpec(0),), (("supports",),), "REJECT", "partially_supported",
        "MSG-C012", "CONDITION_DELETE",
        qualifier_support=(((1, 2),),),
    ),
    CaseSpec(
        "MSG-C017", "F07 deleted condition/temporal scope/quantifier", "B-SCOPE-01",
        "After 22:00, only night-shift staff may unlock the west entrance.",
        (ClaimSpec("Staff may unlock the west entrance", q(("time", "after 22:00"), ("scope", "night-shift staff only"), ("modality", "may"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C018", "F07 deleted condition/temporal scope/quantifier", "B-SCOPE-01",
        "After 22:00, staff may unlock the west entrance.",
        (ClaimSpec("Staff may unlock the west entrance", q(("time", "after 22:00"), ("scope", "all staff"), ("modality", "may"))),),
        (EvidenceSpec(0),), (("supports",),), "REJECT", "partially_supported",
        "MSG-C017", "SCOPE_EXPAND_QUANTIFIER",
        qualifier_support=(((0, 2),),),
    ),
    CaseSpec(
        "MSG-C019", "F08 attribution transfer", "B-ATTR-01",
        "Engineer Mira Sol wrote that the western seal would likely need replacement before winter.",
        (ClaimSpec("The western seal likely needs replacement", q(("time", "before winter"), ("modality", "likely"), ("attribution", "Mira Sol's inspection note"))),),
        (EvidenceSpec(0),),
        (("supports",),), "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C020", "F08 attribution transfer", "B-ATTR-01",
        "Engineer Tomas Reed wrote that the western seal would likely need replacement before winter.",
        (ClaimSpec("The western seal likely needs replacement", q(("time", "before winter"), ("modality", "likely"), ("attribution", "Tomas Reed"))),),
        (EvidenceSpec(0),),
        (("insufficient",),), "REJECT", "insufficient_evidence", "MSG-C019", "ATTRIBUTION_TRANSFER",
        qualifier_support=(((0, 1),),),
    ),
    CaseSpec(
        "MSG-C021", "F09 topic-related but non-supporting evidence", "C021",
        "The new humidity sensor automatically closes the Quartz observatory's telescope dome.",
        (ClaimSpec("The humidity sensor closes the telescope dome", q(("modality", "automatically"),)),),
        (
            EvidenceSpec(0),
            EvidenceSpec(1),
        ),
        (("insufficient", "insufficient"),), "REJECT", "insufficient_evidence",
    ),
    CaseSpec(
        "MSG-C022", "F10 redundant evidence", "B-DUP-01",
        "During routine operation, the Harbor Learning Lab replaces its blue intake filter every 30 days.",
        (ClaimSpec("Harbor Learning Lab replaces the blue intake filter", q(("scope", "during routine operation"), ("quantifier", "every 30 days"))),),
        (EvidenceSpec(0), EvidenceSpec(0)), (("supports", "supports"),),
        "ADMIT", "fully_supported", "MSG-C001", "EVIDENCE_DUPLICATE",
    ),
    CaseSpec(
        "MSG-C023", "F10 redundant evidence", "C023",
        "The Lark clinic backup generator successfully completed its weekly self-test on Friday.",
        (ClaimSpec("The backup generator successfully completed its self-test", q(("quantifier", "weekly"), ("time", "Friday"))),),
        (EvidenceSpec(0), EvidenceSpec(1)), (("supports", "supports"),),
        "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C024", "F11 contradictory spans", "C024",
        "The River Gate inspection finished on 3 June 2026.",
        (ClaimSpec("The River Gate inspection finished", q(("time", "3 June 2026"),)),),
        (
            EvidenceSpec(0),
            EvidenceSpec(1),
        ),
        (("contradicts", "supports"),), "REVIEW", "ambiguous",
    ),
    CaseSpec(
        "MSG-C025", "F11 contradictory spans", "C025",
        "The final scheduled time for the Solace Hall rehearsal is 19:30.",
        (ClaimSpec("The final Solace Hall rehearsal time is 19:30", q(("time", "19:30"), ("scope", "final schedule"))),),
        (EvidenceSpec(0), EvidenceSpec(1)), (("insufficient", "supports"),),
        "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C026", "F12 genuinely ambiguous evidence", "C026",
        "Mara said that the calibration note was incomplete.",
        (ClaimSpec("The calibration note was incomplete", q(("attribution", "Mara"),)),),
        (EvidenceSpec(0),), (("ambiguous",),), "REVIEW", "ambiguous",
    ),
    CaseSpec(
        "MSG-C027", "F12 genuinely ambiguous evidence", "C027",
        "At 30.0 degrees Celsius, the auxiliary fan started.",
        (ClaimSpec("The auxiliary fan started", q(("quantifier", "30.0 degrees Celsius"), ("scope", "auxiliary fan"))),),
        (
            EvidenceSpec(0),
            EvidenceSpec(1),
        ),
        (("ambiguous", "ambiguous"),), "REVIEW", "ambiguous",
    ),
    CaseSpec(
        "MSG-C028", "F13 claim fragment not self-sufficient", "C028",
        "It reached Bay 6 at noon.",
        (ClaimSpec("An unresolved entity reached Bay 6", q(("entity", "unresolved pronoun: It"), ("time", "noon"))),),
        (EvidenceSpec(0),), (("insufficient",),), "REJECT", "partially_supported",
        self_sufficiency="FAIL",
    ),
    CaseSpec(
        "MSG-C029", "F14 over-composed claim with unsupported atom", "C029",
        "At 16:20, the Pine courier delivered two sealed sample boxes to Lab C, and both boxes passed contamination screening.",
        (
            ClaimSpec("The Pine courier delivered sealed sample boxes to Lab C", q(("quantifier", "two boxes"),)),
            ClaimSpec("The delivery arrived", q(("time", "16:20"),)),
            ClaimSpec("Both boxes passed contamination screening"),
        ),
        (EvidenceSpec(0), EvidenceSpec(1)),
        (
            ("supports", "insufficient"),
            ("insufficient", "supports"),
            ("insufficient", "insufficient"),
        ),
        "REJECT", "partially_supported", minimality="FAIL",
    ),
    CaseSpec(
        "MSG-C030", "F05 paired control", "B-NEG-01",
        "The rainwater pump remained inactive throughout the overnight test.",
        (ClaimSpec("The rainwater pump remained inactive", q(("negation", "non-operating state"), ("scope", "overnight test"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
        "MSG-C010", "MEANING_PRESERVING_PARAPHRASE",
    ),
    CaseSpec(
        "MSG-C031", "F03 paired control", "B-ENTITY-01",
        "After every inspection, the calibrated torque wrench is placed in cabinet 4 by the North Workshop.",
        (ClaimSpec("North Workshop places the calibrated torque wrench", q(("entity", "North Workshop"), ("object", "cabinet 4"), ("time", "after every inspection"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
        "MSG-C005", "MEANING_PRESERVING_PARAPHRASE",
    ),
    CaseSpec(
        "MSG-C032", "F07 paired control", "B-EPI-MODCOND-01",
        "When load is at its peak, the new scheduler may reduce queue latency by as much as 15 percent.",
        (ClaimSpec("The new scheduler may reduce queue latency", q(("condition", "peak load"), ("modality", "may"), ("quantifier", "up to 15 percent"))),),
        (EvidenceSpec(0),), (("supports",),), "ADMIT", "fully_supported",
        "MSG-C012", "CONDITION_PRESERVING_PARAPHRASE",
    ),
    CaseSpec(
        "MSG-C033", "F02 jointly supported cross-span", "C033",
        "Analyst Nia Verne recorded that the Delta Field Team's 18 soil cores, collected on 7 April 2026, were transferred to cold storage.",
        (
            ClaimSpec("The Delta Field Team collected soil cores", q(("quantifier", "18 cores"),)),
            ClaimSpec("The batch was collected", q(("time", "7 April 2026"),)),
            ClaimSpec("All cores were transferred to cold storage", q(("attribution", "Nia Verne"),)),
        ),
        (EvidenceSpec(0), EvidenceSpec(1), EvidenceSpec(2)),
        (
            ("supports", "insufficient", "insufficient"),
            ("insufficient", "supports", "insufficient"),
            ("insufficient", "insufficient", "supports"),
        ),
        "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C034", "F14 over-composed claim with unsupported atom", "B-OVERCOMPOSE-01",
        "Operator Jo Lin recorded that at 11:05 the tank pressure exceeded the 8-bar alert threshold and that an alert was sent; additionally, the automated controller initiated the response.",
        (
            ClaimSpec("The alert threshold is above 8 bar", q(("condition", "pressure exceeds 8 bar"),)),
            ClaimSpec("Jo Lin recorded 8.6 bar and an alert", q(("time", "11:05"), ("attribution", "Operator Jo Lin"))),
            ClaimSpec("The automated controller initiated the response"),
        ),
        (EvidenceSpec(0), EvidenceSpec(1)),
        (
            ("supports", "insufficient"),
            ("insufficient", "supports"),
            ("insufficient", "insufficient"),
        ),
        "REJECT", "partially_supported", "MSG-C035", "OVERCOMPOSE_UNSUPPORTED_ATOM",
        minimality="FAIL",
    ),
    CaseSpec(
        "MSG-C035", "F02 jointly supported cross-span", "B-OVERCOMPOSE-01",
        "Operator Jo Lin recorded that at 11:05 the tank pressure exceeded the 8-bar alert threshold and that an alert was sent.",
        (
            ClaimSpec("The alert threshold is above 8 bar", q(("condition", "pressure exceeds 8 bar"),)),
            ClaimSpec("Jo Lin recorded 8.6 bar and an alert", q(("time", "11:05"), ("attribution", "Operator Jo Lin"))),
        ),
        (EvidenceSpec(0), EvidenceSpec(1)),
        (("supports", "insufficient"), ("insufficient", "supports")),
        "ADMIT", "fully_supported",
    ),
    CaseSpec(
        "MSG-C036", "F10 redundant evidence", "C036",
        "The Elm survey included 64 households and was conducted in October 2025.",
        (
            ClaimSpec("The Elm survey included households", q(("quantifier", "64 households"),)),
            ClaimSpec("The Elm survey was conducted", q(("time", "October 2025"),)),
        ),
        (EvidenceSpec(0), EvidenceSpec(1), EvidenceSpec(2)),
        (
            ("supports", "insufficient", "supports"),
            ("insufficient", "supports", "supports"),
        ),
        "ADMIT", "fully_supported",
    ),
)


def _paragraph_payloads(paragraphs: tuple[str, ...]) -> tuple[str, list[dict]]:
    snapshot = "\n\n".join(paragraphs)
    offset = 0
    payloads = []
    for index, paragraph in enumerate(paragraphs, 1):
        start = offset
        end = start + len(paragraph)
        payloads.append(
            {
                "paragraph_id": f"P{index}",
                "text": paragraph,
                "snapshot_start": start,
                "snapshot_end": end,
            }
        )
        offset = end + 2
    return snapshot, payloads


def _compile_case(spec: CaseSpec) -> dict:
    paragraphs = DOCUMENTS[spec.block_id]
    snapshot, paragraph_payloads = _paragraph_payloads(paragraphs)
    digest = sha256(snapshot.encode("utf-8")).hexdigest()
    document_id = f"direction1-{spec.block_id.lower()}"

    candidate = CandidateClaim(
        candidate_id=f"{spec.case_id}-candidate",
        proposition=spec.proposition,
        atomic_claims=tuple(
            AtomicClaim(
                claim_id=f"A{index}",
                text=claim.text,
                qualifiers=tuple(
                    QualifierSlot(QualifierKind(kind), value)
                    for kind, value in claim.qualifiers
                ),
                required_support_parts=claim.required_support_parts,
            )
            for index, claim in enumerate(spec.claims, 1)
        ),
    )

    evidence_spans: list[EvidenceSpan] = []
    evidence_payloads = []
    for index, evidence in enumerate(spec.evidence, 1):
        paragraph = paragraphs[evidence.paragraph]
        excerpt = evidence.excerpt or paragraph
        start = paragraph.index(excerpt)
        span_id = f"E{index}"
        evidence_spans.append(
            EvidenceSpan(
                span_id=span_id,
                document_id=document_id,
                paragraph_id=f"P{evidence.paragraph + 1}",
                text=excerpt,
                start_char=start,
                end_char=start + len(excerpt),
                source_sha256=digest,
            )
        )
        evidence_payloads.append(
            {
                "span_id": span_id,
                "paragraph_id": f"P{evidence.paragraph + 1}",
                "start_char": start,
                "end_char": start + len(excerpt),
                "text": excerpt,
            }
        )

    if len(spec.labels) != len(candidate.atomic_claims):
        raise ValueError(f"{spec.case_id}: support rows must match atomic claims")
    cells: list[SupportCell] = []
    cell_payloads = []
    for claim_index, (claim, row) in enumerate(
        zip(candidate.atomic_claims, spec.labels, strict=True)
    ):
        if len(row) != len(evidence_spans):
            raise ValueError(f"{spec.case_id}: support columns must match evidence spans")
        for span_index, (span, raw_label) in enumerate(
            zip(evidence_spans, row, strict=True)
        ):
            label = SupportLabel(raw_label)
            if spec.qualifier_support is not None:
                qualifier_indexes = spec.qualifier_support[claim_index][span_index]
                supported_qualifiers = tuple(
                    claim.qualifiers[index] for index in qualifier_indexes
                )
            else:
                supported_qualifiers = (
                    claim.qualifiers if label is SupportLabel.SUPPORTS else ()
                )
            supported_parts = (
                claim.required_support_parts if label is SupportLabel.SUPPORTS else ()
            )
            cell = SupportCell(
                claim_id=claim.claim_id,
                span_id=span.span_id,
                label=label,
                rationale=f"Frozen catalog annotation for {spec.case_id}.",
                supported_qualifiers=supported_qualifiers,
                supported_claim_parts=supported_parts,
            )
            cells.append(cell)
            cell_payloads.append(
                {
                    "claim_id": cell.claim_id,
                    "span_id": cell.span_id,
                    "label": cell.label.value,
                    "rationale": cell.rationale,
                    "supported_qualifiers": [
                        {"kind": slot.kind.value, "value": slot.value}
                        for slot in cell.supported_qualifiers
                    ],
                    "supported_claim_parts": list(cell.supported_claim_parts),
                }
            )

    matrix = SupportMatrix(candidate, tuple(evidence_spans), tuple(cells))
    minimal_sets = [
        list(solution.selected_span_ids)
        for solution in InclusionMinimalSolver().solve(matrix)
    ]
    is_programmatic = (
        spec.catalog_operator is not None
        and spec.case_id not in AGENT_AUTHORED_SEMANTIC_SHAMS
        and spec.case_id not in NON_MECHANICAL_SEMANTIC_CASES
    )
    payload = {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "case_id": spec.case_id,
        "case_family": spec.family,
        "document": {
            "document_id": document_id,
            "title": f"Direction 1 synthetic source block {spec.block_id}",
            "snapshot_text": snapshot,
            "source_sha256": digest,
            "paragraphs": paragraph_payloads,
        },
        "candidate": {
            "candidate_id": candidate.candidate_id,
            "proposition": candidate.proposition,
            "atomic_claims": [
                {
                    "claim_id": claim.claim_id,
                    "text": claim.text,
                    "qualifiers": [
                        {"kind": slot.kind.value, "value": slot.value}
                        for slot in claim.qualifiers
                    ],
                    "required_support_parts": list(claim.required_support_parts),
                }
                for claim in candidate.atomic_claims
            ],
        },
        "evidence_spans": evidence_payloads,
        "oracle": {
            "decision": spec.decision,
            "reason_codes": [
                spec.reason,
                *(
                    ["agent_authored_semantic_sham_not_programmatic_oracle"]
                    if spec.case_id in AGENT_AUTHORED_SEMANTIC_SHAMS
                    else []
                ),
                *(
                    [
                        "deontic_label_not_mechanically_provable"
                        if spec.case_id == "MSG-C014"
                        else "unsupported_atom_non_support_not_mechanically_provable"
                    ]
                    if spec.case_id in NON_MECHANICAL_SEMANTIC_CASES
                    else []
                ),
                *(
                    ["high_risk_not_human_gold"]
                    if spec.case_id in HIGH_RISK_NOT_HUMAN_GOLD
                    else []
                ),
            ],
            "minimal_evidence_sets": minimal_sets,
            "claim_form": {
                "self_sufficiency": spec.self_sufficiency,
                "minimality": spec.minimality,
                "reason_codes": ["frozen_catalog_audit"],
                "auditor_name": "codex_catalog_materializer",
                "auditor_version": "v0.1",
            },
            "support_cells": cell_payloads,
            "label_source": "programmatic_oracle" if is_programmatic else "llm_generated",
            "adjudication_status": "synthetic_oracle" if is_programmatic else "provisional",
        },
        "provenance": {
            "construction": "project_authored_synthetic",
            "base_case_id": spec.base_case_id,
            "perturbation_operator": (
                CATALOG_OPERATOR_MAP[spec.catalog_operator]
                if spec.catalog_operator is not None
                else None
            ),
            "generator": "codex_catalog_materializer_v0.1",
            "generator_type": "programmatic" if is_programmatic else "llm_or_agent",
        },
    }
    parse_benchmark_case(payload)
    return payload


def render_benchmark() -> bytes:
    if len(CASES) != 36 or len({case.case_id for case in CASES}) != 36:
        raise ValueError("the frozen catalog must contain exactly 36 unique cases")
    payloads = [_compile_case(case) for case in CASES]
    case_ids = {payload["case_id"] for payload in payloads}
    for payload in payloads:
        base_case_id = payload["provenance"]["base_case_id"]
        if base_case_id is not None and base_case_id not in case_ids:
            raise ValueError(f"unknown base_case_id: {base_case_id}")
    lines = [
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for payload in payloads
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_benchmark(output: str | Path = DEFAULT_OUTPUT) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(render_benchmark())
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render_benchmark()
    if args.check:
        if not args.output.exists() or args.output.read_bytes() != rendered:
            print(f"stale or missing benchmark: {args.output}")
            return 1
        print(f"benchmark is canonical: {args.output}")
        return 0
    build_benchmark(args.output)
    print(
        f"wrote {len(CASES)} cases, {len(rendered)} bytes, "
        f"sha256={sha256(rendered).hexdigest()} to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
