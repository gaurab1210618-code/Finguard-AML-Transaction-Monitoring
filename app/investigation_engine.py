"""
FinGuard Investigation Engine

Separates AML alert investigation into three analytical scopes:

1. Alert Evidence
   - The transactions explicitly linked to the alert.
   - Defines why the alert was generated.

2. Investigation Context
   - A configurable transaction window around the alert evidence.
   - Used to identify additional contextual risk indicators.

3. Historical Customer Context
   - Customer profile and prior case history.
   - Used for interpretation, not to re-trigger transaction rules.

Design principle:

Data → Rules → Evidence → AI interpretation → Human decision

The LLM should receive the structured evidence package produced here.
It should not query the database, calculate metrics, or determine
the final case disposition.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INVESTIGATION_WINDOW_DAYS = 7
BASELINE_WINDOW_DAYS = 90


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from app.rules_engine import (
    check_amount_clustering,
    check_baseline_deviation,
    check_high_velocity,
    check_multiple_counterparties,
    check_rapid_in_out,
)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _parse_timestamp(value: str | datetime) -> datetime:
    """Convert supported timestamp formats to datetime."""

    if isinstance(value, datetime):
        return value

    value = str(value)

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unsupported timestamp format: {value}")


def _normalise_transactions(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Return transactions sorted chronologically.

    The original dictionaries are not modified.
    """

    return sorted(
        transactions,
        key=lambda x: _parse_timestamp(x["timestamp"]),
    )


def _get_customer_transactions(
    transactions: list[dict[str, Any]],
    customer_id: str,
) -> list[dict[str, Any]]:
    """Return transactions belonging to the investigation customer."""

    return [
        txn
        for txn in transactions
        if str(txn.get("customer_id")) == str(customer_id)
    ]


def _find_transaction_by_id(
    transactions: list[dict[str, Any]],
    transaction_id: str,
) -> dict[str, Any] | None:
    """Find one transaction by transaction_id."""

    for txn in transactions:
        if txn.get("transaction_id") == transaction_id:
            return txn

    return None


def _parse_evidence_ids(alert: dict[str, Any]) -> list[str]:
    """
    Parse alert.evidence_transaction_ids.

    Supports both comma-separated and pipe-separated formats.
    """

    raw = alert.get("evidence_transaction_ids", "")

    if raw is None:
        return []

    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]

    raw = str(raw).strip()

    if not raw:
        return []

    # Current dataset uses "|" as the multi-ID separator.
    # Comma support is retained for robustness.
    raw = raw.replace("|", ",")

    return [
        item.strip()
        for item in raw.split(",")
        if item.strip()
    ]


# ---------------------------------------------------------------------------
# Ring 1 — Alert Evidence
# ---------------------------------------------------------------------------

def resolve_alert_evidence(
    alert: dict[str, Any],
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Resolve the transactions explicitly attached to the alert.

    These transactions define the alert evidence and are not replaced
    by a re-scan of the customer's entire transaction history.
    """

    evidence_ids = _parse_evidence_ids(alert)

    evidence_transactions = []

    for transaction_id in evidence_ids:
        txn = _find_transaction_by_id(
            transactions,
            transaction_id,
        )

        if txn is not None:
            evidence_transactions.append(txn)

    missing_ids = [
        transaction_id
        for transaction_id in evidence_ids
        if _find_transaction_by_id(
            transactions,
            transaction_id,
        ) is None
    ]

    evidence_transactions = _normalise_transactions(
        evidence_transactions
    )

    evidence_timestamps = [
        _parse_timestamp(txn["timestamp"])
        for txn in evidence_transactions
    ]

    return {
        "alert_id": alert.get("alert_id"),
        "customer_id": alert.get("customer_id"),
        "trigger_rule": alert.get("trigger_rule"),
        "alert_type": alert.get("alert_type"),
        "status": alert.get("status"),
        "priority": alert.get("priority"),
        "evidence_transaction_ids": evidence_ids,
        "evidence_transactions": evidence_transactions,
        "missing_evidence_transaction_ids": missing_ids,
        "evidence_start": (
            min(evidence_timestamps).isoformat()
            if evidence_timestamps
            else None
        ),
        "evidence_end": (
            max(evidence_timestamps).isoformat()
            if evidence_timestamps
            else None
        ),
    }


# ---------------------------------------------------------------------------
# Ring 2 — Investigation Context
# ---------------------------------------------------------------------------

def build_investigation_context(
    alert: dict[str, Any],
    transactions: list[dict[str, Any]],
    days_before: int = INVESTIGATION_WINDOW_DAYS,
    days_after: int = 0,
) -> dict[str, Any]:
    """
    Build the investigation transaction window.

    The window is anchored to the alert's evidence timestamp rather than
    scanning the customer's entire history.

    Default:
        T-7 days → T-0

    Evidence transactions remain part of the context because the pattern
    rules may need to determine whether the alert transaction participates
    in a broader pattern.
    """

    evidence = resolve_alert_evidence(
        alert,
        transactions,
    )

    evidence_transactions = evidence["evidence_transactions"]

    if not evidence_transactions:
        raise ValueError(
            f"No valid evidence transactions found for "
            f"alert {alert.get('alert_id')}."
        )

    evidence_times = [
        _parse_timestamp(txn["timestamp"])
        for txn in evidence_transactions
    ]

    context_start = min(evidence_times) - timedelta(days=days_before)
    context_end = max(evidence_times) + timedelta(days=days_after)

    customer_id = alert["customer_id"]

    customer_transactions = _get_customer_transactions(
        transactions,
        customer_id,
    )

    context_transactions = [
        txn
        for txn in customer_transactions
        if context_start
        <= _parse_timestamp(txn["timestamp"])
        <= context_end
    ]

    context_transactions = _normalise_transactions(
        context_transactions
    )

    return {
        "customer_id": customer_id,
        "alert_id": alert.get("alert_id"),
        "window_start": context_start.isoformat(),
        "window_end": context_end.isoformat(),
        "days_before": days_before,
        "days_after": days_after,
        "transaction_count": len(context_transactions),
        "transaction_ids": [
            txn["transaction_id"]
            for txn in context_transactions
        ],
        "transactions": context_transactions,
    }


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

def evaluate_contextual_rules(
    context_transactions: list[dict[str, Any]],
    customer: dict[str, Any],
    customer_id: str,
) -> dict[str, dict[str, Any]]:
    """
    Run the existing deterministic rules against the investigation context.

    IMPORTANT:
    The rules themselves are unchanged.

    Only the transaction scope supplied to them has changed.
    """

    return {
        "RL-01": check_high_velocity(
            context_transactions,
            customer,
        ),
        "RL-02": check_baseline_deviation(
            context_transactions,
            customer,
        ),
        "RL-03": check_amount_clustering(
            context_transactions,
        ),
        "RL-04": check_rapid_in_out(
            context_transactions,
            customer_id,
        ),
        "RL-05": check_multiple_counterparties(
            context_transactions,
            customer_id,
        ),
    }


# ---------------------------------------------------------------------------
# Historical customer context
# ---------------------------------------------------------------------------

def build_historical_context(
    customer: dict[str, Any],
    case_history: list[dict[str, Any]],
    alert: dict[str, Any],
) -> dict[str, Any]:
    """
    Build customer-level historical context.

    This does NOT run transaction-monitoring rules.

    It provides:
        - customer profile
        - prior case count
        - prior dispositions
        - prior escalations
    """

    customer_id = alert["customer_id"]

    customer_cases = [
        case
        for case in case_history
        if str(case.get("customer_id")) == str(customer_id)
    ]

    dispositions = [
        case.get("disposition")
        for case in customer_cases
        if case.get("disposition")
    ]

    escalated_count = sum(
        1
        for disposition in dispositions
        if str(disposition).upper() == "ESCALATED"
    )

    return {
        "customer_id": customer_id,
        "risk_tier": customer.get("risk_tier"),
        "occupation": customer.get("occupation"),
        "country": customer.get("country"),
        "account_age_months": customer.get("account_age_months"),
        "monthly_avg_volume": customer.get("monthly_avg_volume"),
        "monthly_avg_txn_count": customer.get("monthly_avg_txn_count"),
        "prior_case_count": len(customer_cases),
        "prior_dispositions": dispositions,
        "prior_escalation_count": escalated_count,
    }


# ---------------------------------------------------------------------------
# Evidence Package
# ---------------------------------------------------------------------------

def build_evidence_package(
    alert: dict[str, Any],
    transactions: list[dict[str, Any]],
    customer: dict[str, Any],
    case_history: list[dict[str, Any]],
    days_before: int = INVESTIGATION_WINDOW_DAYS,
    days_after: int = 0,
) -> dict[str, Any]:
    """
    Build the canonical FinGuard Evidence Package.

    This is the object that can later be passed to:
        - Streamlit UI
        - AI investigation summarizer
        - case manager
        - audit logger

    It deliberately separates:
        alert_trigger
        contextual_indicators
        historical_signals
    """

    # ---------------------------------------------------------------
    # Ring 1 — Alert Evidence
    # ---------------------------------------------------------------

    evidence = resolve_alert_evidence(
        alert,
        transactions,
    )

    # ---------------------------------------------------------------
    # Ring 2 — Investigation Context
    # ---------------------------------------------------------------

    context = build_investigation_context(
        alert,
        transactions,
        days_before=days_before,
        days_after=days_after,
    )

    # ---------------------------------------------------------------
    # Run existing deterministic rules on context
    # ---------------------------------------------------------------

    rule_results = evaluate_contextual_rules(
        context["transactions"],
        customer,
        alert["customer_id"],
    )

    # ---------------------------------------------------------------
    # Identify contextual findings
    # ---------------------------------------------------------------

    contextual_indicators = []

    alert_evidence_ids = set(
        evidence["evidence_transaction_ids"]
    )

    for rule_id, result in rule_results.items():

        # ---------------------------------------------------------------
        # Avoid duplicating the alert trigger as a contextual finding.
        #
        # Example:
        # ALT-0001 was already triggered by:
        # RL-02 → TXN-11988
        #
        # If RL-02 only finds TXN-11988 inside the investigation window,
        # it should remain the primary alert trigger rather than appearing
        # again as a contextual finding.
        #
        # If RL-02 finds additional transactions, however, the contextual
        # finding remains relevant.
        # ---------------------------------------------------------------

        if rule_id == "RL-02" and result.get("triggered"):

            flagged_ids = set(
                result.get("flagged_transaction_ids", [])
            )

            additional_ids = flagged_ids - alert_evidence_ids

            if not additional_ids:
                continue

        contextual_indicators.append(
            {
                "rule_id": rule_id,
                "rule_name": result.get("rule_name"),
                "triggered": result.get("triggered"),
                "reason": result.get("reason"),
                "result": result,
                "scope": {
                    "type": "INVESTIGATION_CONTEXT",
                    "window_start": context["window_start"],
                    "window_end": context["window_end"],
                    "transaction_count": context["transaction_count"],
                },
            }
        )

    # ---------------------------------------------------------------
    # Ring 3 — Historical Context
    # ---------------------------------------------------------------

    historical_context = build_historical_context(
        customer,
        case_history,
        alert,
    )

    # ---------------------------------------------------------------
    # Final evidence package
    # ---------------------------------------------------------------

    return {
        "schema_version": "1.0",

        "alert": {
            "alert_id": alert.get("alert_id"),
            "customer_id": alert.get("customer_id"),
            "alert_type": alert.get("alert_type"),
            "trigger_rule": alert.get("trigger_rule"),
            "status": alert.get("status"),
            "priority": alert.get("priority"),
        },

        "alert_trigger": {
            "scope": "ALERT_EVIDENCE",
            "rule": alert.get("trigger_rule"),
            "evidence_transaction_ids": evidence[
                "evidence_transaction_ids"
            ],
            "evidence_transactions": evidence[
                "evidence_transactions"
            ],
            "missing_evidence_transaction_ids": evidence[
                "missing_evidence_transaction_ids"
            ],
        },

        "investigation_context": {
            "scope": "INVESTIGATION_CONTEXT",
            "window_start": context["window_start"],
            "window_end": context["window_end"],
            "transaction_count": context["transaction_count"],
            "transaction_ids": context["transaction_ids"],
        },

        "contextual_indicators": contextual_indicators,

        "historical_signals": {
            "scope": "HISTORICAL_CUSTOMER_CONTEXT",
            **historical_context,
        },
    }


# ---------------------------------------------------------------------------
# Convenience function for CLI / tests
# ---------------------------------------------------------------------------

def investigate_alert(
    alert: dict[str, Any],
    transactions: list[dict[str, Any]],
    customer: dict[str, Any],
    case_history: list[dict[str, Any]],
    days_before: int = INVESTIGATION_WINDOW_DAYS,
    days_after: int = 0,
) -> dict[str, Any]:
    """
    Public entry point for a FinGuard alert investigation.
    """

    return build_evidence_package(
        alert=alert,
        transactions=transactions,
        customer=customer,
        case_history=case_history,
        days_before=days_before,
        days_after=days_after,
    )