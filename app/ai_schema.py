"""
FinGuard — Common AI Investigation Schema

This module contains the provider-independent output contract.

Gemini and NVIDIA must both return this same structure.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    """
    Reference to evidence already present in the Evidence Package.
    """

    reference_type: Literal[
        "TRANSACTION",
        "RULE",
        "CUSTOMER_CONTEXT",
        "HISTORICAL_CONTEXT",
    ]

    reference_id: str = Field(
        description=(
            "Identifier already present in the Evidence Package. "
            "Do not invent identifiers."
        )
    )

    statement: str = Field(
        description=(
            "Short explanation of what this reference supports."
        )
    )


class KeyFinding(BaseModel):
    """
    One material investigation finding.
    """

    finding: str = Field(
        description=(
            "A concise, factual finding based only on the supplied evidence."
        )
    )

    significance: str = Field(
        description=(
            "Why the finding matters for investigation context."
        )
    )

    evidence_references: list[EvidenceReference] = Field(
        default_factory=list,
        description="Evidence references supporting the finding.",
    )


class AIInvestigationResult(BaseModel):
    """
    Provider-independent structured AI investigation result.
    """

    investigation_summary: str = Field(
        description=(
            "A concise analyst-facing summary of the alert, customer "
            "context, and investigation findings."
        )
    )

    risk_assessment: Literal[
        "LOW",
        "MODERATE",
        "HIGH",
        "INSUFFICIENT_EVIDENCE",
    ] = Field(
        description=(
            "AI-assisted assessment based only on supplied evidence. "
            "This is not the final case disposition."
        )
    )

    key_findings: list[KeyFinding] = Field(
        default_factory=list,
        description="Material evidence-based investigation findings.",
    )

    recommended_next_step: Literal[
        "CLOSE_REVIEW",
        "FURTHER_REVIEW",
        "ESCALATE_FOR_REVIEW",
    ] = Field(
        description=(
            "Recommended next investigative action for the human analyst. "
            "This is not the final disposition."
        )
    )

    rationale: str = Field(
        description=(
            "Brief evidence-based rationale for the recommended next step."
        )
    )

    evidence_gaps: list[str] = Field(
        default_factory=list,
        description=(
            "Missing or insufficient information that could affect "
            "the investigation."
        )
    )

    analyst_warning: str = Field(
        description=(
            "Explicit reminder that the human analyst retains final "
            "decision authority."
        )
    )

    # -----------------------------------------------------------------------
    # Provider provenance
    # -----------------------------------------------------------------------

    provider: Literal[
        "gemini",
        "nvidia",
    ] | None = Field(
        default=None,
        description=(
            "AI provider that generated the final investigation result. "
            "Stamped by the application orchestrator after successful "
            "provider execution and validation."
        ),
    )


# ---------------------------------------------------------------------------
# Evidence Reference Validation
# ---------------------------------------------------------------------------


def _extract_rule_ids(
    evidence_package: dict,
) -> set[str]:
    """
    Extract rule IDs legitimately present in the Evidence Package.
    """

    rule_ids: set[str] = set()

    alert_trigger_rule = (
        evidence_package
        .get("alert_trigger", {})
        .get("rule", "")
    )

    if alert_trigger_rule:

        import re

        matches = re.findall(
            r"\bRL-\d{2}\b",
            str(alert_trigger_rule),
        )

        rule_ids.update(matches)

    for indicator in evidence_package.get(
        "contextual_indicators",
        [],
    ):

        rule_id = indicator.get("rule_id")

        if rule_id:
            rule_ids.add(str(rule_id))

    return rule_ids


def allowed_evidence_references(
    evidence_package: dict,
) -> dict[str, set[str]]:
    """
    Build an allow-list of evidence references that the AI
    is permitted to cite.
    """

    transaction_ids: set[str] = set()

    alert_trigger = evidence_package.get(
        "alert_trigger",
        {},
    )

    transaction_ids.update(
        str(txn_id)
        for txn_id in alert_trigger.get(
            "evidence_transaction_ids",
            [],
        )
    )

    investigation_context = evidence_package.get(
        "investigation_context",
        {},
    )

    transaction_ids.update(
        str(txn_id)
        for txn_id in investigation_context.get(
            "transaction_ids",
            [],
        )
    )

    customer_id = (
        evidence_package
        .get("alert", {})
        .get("customer_id")
    )

    return {
        "TRANSACTION": transaction_ids,

        "RULE": _extract_rule_ids(
            evidence_package
        ),

        "CUSTOMER_CONTEXT": {
            str(customer_id)
        }
        if customer_id
        else set(),

        "HISTORICAL_CONTEXT": {
            "CASE_HISTORY",
            "CUSTOMER_PROFILE",
        },
    }


def validate_evidence_references(
    result: AIInvestigationResult,
    evidence_package: dict,
) -> None:
    """
    Reject AI-generated evidence references that are not
    present in the deterministic Evidence Package.
    """

    allowed = allowed_evidence_references(
        evidence_package
    )

    for finding in result.key_findings:

        for reference in finding.evidence_references:

            valid_ids = allowed.get(
                reference.reference_type,
                set(),
            )

            if reference.reference_id not in valid_ids:

                raise ValueError(
                    "AI returned unsupported evidence reference: "
                    f"{reference.reference_type}="
                    f"{reference.reference_id}"
                )