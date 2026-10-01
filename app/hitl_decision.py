from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


DecisionType = Literal[
    "CLOSE",
    "OVERRIDE",
    "ESCALATE",
]


@dataclass
class HITLDecision:
    """
    Final decision made by the human analyst.

    The AI recommendation and the analyst decision are
    intentionally stored as separate fields.
    """

    alert_id: str
    customer_id: str

    ai_provider: str
    ai_recommendation: str
    ai_risk_assessment: str

    analyst_decision: DecisionType
    analyst_reason: str

    decided_at: str


def validate_hitl_decision(
    decision: HITLDecision,
) -> None:
    """
    Validate the human analyst decision.

    Raises:
        ValueError: if the decision violates HITL rules.
    """

    allowed_decisions = {
        "CLOSE",
        "OVERRIDE",
        "ESCALATE",
    }

    if decision.analyst_decision not in allowed_decisions:
        raise ValueError(
            "Invalid analyst decision. "
            "Allowed values: CLOSE, OVERRIDE, ESCALATE."
        )

    if not decision.alert_id:
        raise ValueError(
            "alert_id is required."
        )

    if not decision.customer_id:
        raise ValueError(
            "customer_id is required."
        )

    if not decision.ai_provider:
        raise ValueError(
            "ai_provider is required."
        )

    if not decision.ai_recommendation:
        raise ValueError(
            "ai_recommendation is required."
        )

    if not decision.ai_risk_assessment:
        raise ValueError(
            "ai_risk_assessment is required."
        )

    if not decision.analyst_reason.strip():
        raise ValueError(
            "Analyst reason is required."
        )


def create_hitl_decision(
    alert_id: str,
    customer_id: str,
    ai_provider: str,
    ai_recommendation: str,
    ai_risk_assessment: str,
    analyst_decision: DecisionType,
    analyst_reason: str,
) -> HITLDecision:
    """
    Create and validate a final human analyst decision.
    """

    decision = HITLDecision(
        alert_id=alert_id,
        customer_id=customer_id,

        ai_provider=ai_provider,
        ai_recommendation=ai_recommendation,
        ai_risk_assessment=ai_risk_assessment,

        analyst_decision=analyst_decision,
        analyst_reason=analyst_reason.strip(),

        decided_at=datetime.now(
            timezone.utc
        ).isoformat(
            timespec="seconds"
        ),
    )

    validate_hitl_decision(decision)

    return decision