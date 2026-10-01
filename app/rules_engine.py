"""
FinGuard - Deterministic AML Risk Indicator Engine

Purpose:
    Analyze transaction activity for an AML investigation and calculate
    objective, evidence-based risk indicators.

Important:
    This module does NOT make a final AML decision.
    It produces indicators and evidence for downstream investigation
    and human review.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any


# ============================================================
# Rule Configuration
# ============================================================

RULE_CONFIG = {
    "RL-01": {
        "name": "HIGH VELOCITY",
        "window_hours": 24,
        "multiplier": 2.0,
    },
    "RL-02": {
        "name": "BASELINE DEVIATION",
        "multiplier": 2.5,
        "minimum_amount": 10000,
    },
    "RL-03": {
        "name": "AMOUNT CLUSTERING",
        "window_hours": 48,
        "cv_threshold": 0.12,
        "minimum_transactions": 3,
    },
    "RL-04": {
        "name": "RAPID IN-OUT",
        "window_hours": 12,
        "inbound_minimum_amount": 50000,
        "outbound_minimum_amount": 40000,
    },
    "RL-05": {
        "name": "MULTIPLE COUNTERPARTIES",
        "window_hours": 24,
        "minimum_counterparties": 3,
    },
}


# ============================================================
# Utility Functions
# ============================================================

def _to_float(value: Any) -> float:
    """Convert a value to float safely."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_timestamp(transaction: dict[str, Any]):
    """Parse a transaction timestamp into a datetime object."""

    value = transaction.get("timestamp", "")

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (ValueError, TypeError):
        return None


def _sort_transactions(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return transactions with valid timestamps sorted chronologically."""

    valid_transactions = [
        transaction
        for transaction in transactions
        if _parse_timestamp(transaction) is not None
    ]

    return sorted(
        valid_transactions,
        key=_parse_timestamp,
    )


def _transactions_in_window(
    transactions: list[dict[str, Any]],
    end_time: datetime,
    hours: int,
) -> list[dict[str, Any]]:
    """
    Return transactions occurring within a backward-looking
    time window ending at end_time.
    """

    start_time = end_time - timedelta(hours=hours)

    return [
        transaction
        for transaction in transactions
        if (
            _parse_timestamp(transaction) is not None
            and start_time
            <= _parse_timestamp(transaction)
            <= end_time
        )
    ]


# ============================================================
# RL-01 — High Transaction Velocity
# ============================================================

def check_high_velocity(
    transactions: list[dict[str, Any]],
    customer: dict[str, Any],
) -> dict[str, Any]:
    """
    Check whether transaction frequency is materially higher
    than the customer's expected frequency.

    Expected 24-hour transaction count is derived from the
    customer's monthly average transaction count.

    Rule:
        observed 24h transaction count >
        expected 24h transaction count × 2.0
    """

    config = RULE_CONFIG["RL-01"]

    transactions = _sort_transactions(transactions)

    if not transactions:
        return {
            "rule_id": "RL-01",
            "rule_name": config["name"],
            "triggered": False,
            "reason": "No valid transactions available.",
        }

    monthly_avg_count = _to_float(
        customer.get("monthly_avg_txn_count")
    )

    expected_24h = monthly_avg_count / 30

    if expected_24h <= 0:
        return {
            "rule_id": "RL-01",
            "rule_name": config["name"],
            "triggered": False,
            "reason": "Customer transaction baseline is unavailable.",
        }

    maximum_count = 0
    maximum_window_end = None

    for transaction in transactions:

        timestamp = _parse_timestamp(transaction)

        window = _transactions_in_window(
            transactions,
            timestamp,
            config["window_hours"],
        )

        if len(window) > maximum_count:
            maximum_count = len(window)
            maximum_window_end = timestamp

    threshold = expected_24h * config["multiplier"]

    triggered = maximum_count > threshold

    return {
        "rule_id": "RL-01",
        "rule_name": config["name"],
        "triggered": triggered,
        "observed_transaction_count": maximum_count,
        "expected_transaction_count_24h": round(
            expected_24h,
            2,
        ),
        "threshold_transaction_count": round(
            threshold,
            2,
        ),
        "window_hours": config["window_hours"],
        "window_end": (
            maximum_window_end.isoformat()
            if maximum_window_end
            else None
        ),
        "reason": (
            f"{maximum_count} transactions observed in a "
            f"{config['window_hours']}-hour window versus an "
            f"expected {expected_24h:.2f}."
        ),
    }


# ============================================================
# RL-02 — Baseline Deviation
# ============================================================

def check_baseline_deviation(
    transactions: list[dict[str, Any]],
    customer: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare observed transaction amounts against the customer's
    profile average transaction amount.

    Baseline:
        monthly_avg_volume / monthly_avg_txn_count

    Rule:
        transaction amount >= minimum amount
        AND
        transaction amount > profile average × 2.5

    This mirrors the RL-02 definition used by the dataset
    monitoring logic.
    """

    config = RULE_CONFIG["RL-02"]

    monthly_avg_volume = _to_float(
        customer.get("monthly_avg_volume")
    )

    monthly_avg_count = _to_float(
        customer.get("monthly_avg_txn_count")
    )

    if monthly_avg_count <= 0:
        return {
            "rule_id": "RL-02",
            "rule_name": config["name"],
            "triggered": False,
            "reason": "Customer transaction baseline is unavailable.",
        }

    profile_average = (
        monthly_avg_volume / monthly_avg_count
    )

    threshold = (
        profile_average * config["multiplier"]
    )

    minimum_amount = config["minimum_amount"]

    flagged_transactions = []

    for transaction in transactions:

        amount = _to_float(
            transaction.get("amount")
        )

        if (
            amount >= minimum_amount
            and amount > threshold
        ):
            flagged_transactions.append(
                transaction
            )

    maximum_amount = max(
        (
            _to_float(transaction.get("amount"))
            for transaction in transactions
        ),
        default=0.0,
    )

    deviation_multiple = (
        maximum_amount / profile_average
        if profile_average > 0
        else 0
    )

    triggered = len(flagged_transactions) > 0

    return {
        "rule_id": "RL-02",
        "rule_name": config["name"],
        "triggered": triggered,
        "profile_average_amount": round(
            profile_average,
            2,
        ),
        "multiplier_threshold": config["multiplier"],
        "threshold_amount": round(
            threshold,
            2,
        ),
        "minimum_amount": minimum_amount,
        "maximum_observed_amount": round(
            maximum_amount,
            2,
        ),
        "maximum_deviation_multiple": round(
            deviation_multiple,
            2,
        ),
        "flagged_transaction_ids": [
            transaction["transaction_id"]
            for transaction in flagged_transactions
        ],
        "reason": (
            f"Transactions must be at least "
            f"{minimum_amount:.0f} and exceed "
            f"{config['multiplier']:.1f}x the customer "
            f"profile average. Maximum observed amount "
            f"was {deviation_multiple:.2f}x the profile average."
        ),
    }


# ============================================================
# RL-03 — Amount Clustering
# ============================================================

def check_amount_clustering(
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Detect closely grouped transaction amounts within a
    48-hour window.

    Clustering is measured using coefficient of variation:

        CV = standard deviation / mean

    Lower CV indicates more closely grouped transaction amounts.
    """

    config = RULE_CONFIG["RL-03"]

    transactions = _sort_transactions(transactions)

    if len(transactions) < config["minimum_transactions"]:
        return {
            "rule_id": "RL-03",
            "rule_name": config["name"],
            "triggered": False,
            "reason": (
                f"At least "
                f"{config['minimum_transactions']} "
                f"transactions are required."
            ),
        }

    best_window = []
    best_cv = None

    for transaction in transactions:

        timestamp = _parse_timestamp(transaction)

        window = _transactions_in_window(
            transactions,
            timestamp,
            config["window_hours"],
        )

        if len(window) < config["minimum_transactions"]:
            continue

        amounts = [
            _to_float(item.get("amount"))
            for item in window
        ]

        mean_amount = (
            sum(amounts) / len(amounts)
        )

        if mean_amount <= 0:
            continue

        variance = (
            sum(
                (amount - mean_amount) ** 2
                for amount in amounts
            )
            / len(amounts)
        )

        standard_deviation = math.sqrt(
            variance
        )

        coefficient_of_variation = (
            standard_deviation / mean_amount
        )

        if (
            best_cv is None
            or coefficient_of_variation < best_cv
        ):
            best_cv = coefficient_of_variation
            best_window = window

    if best_cv is None:
        return {
            "rule_id": "RL-03",
            "rule_name": config["name"],
            "triggered": False,
            "reason": "No qualifying transaction window found.",
        }

    triggered = (
        best_cv < config["cv_threshold"]
    )

    return {
        "rule_id": "RL-03",
        "rule_name": config["name"],
        "triggered": triggered,
        "coefficient_of_variation": round(
            best_cv,
            4,
        ),
        "cv_threshold": config["cv_threshold"],
        "transaction_count": len(best_window),
        "transaction_ids": [
            transaction["transaction_id"]
            for transaction in best_window
        ],
        "reason": (
            f"Lowest observed coefficient of variation "
            f"was {best_cv:.4f}."
        ),
    }


# ============================================================
# RL-04 — Rapid Inbound / Outbound
# ============================================================

def check_rapid_in_out(
    transactions: list[dict[str, Any]],
    customer_id: str,
) -> dict[str, Any]:
    """
    Detect a large inbound transaction followed by a large
    outbound transaction within the configured time window.

    Direction is determined from the customer's position
    in the transaction:

        receiver_id == customer_id -> INBOUND
        sender_id == customer_id   -> OUTBOUND

    RL-04 thresholds:
        inbound  >= configured inbound minimum
        outbound >= configured outbound minimum

    The outbound transaction must occur after the inbound
    transaction and within the configured time window.

    Transaction type is deliberately not used to determine
    direction because the dataset contains transaction types
    whose labels alone do not establish direction.
    """

    config = RULE_CONFIG["RL-04"]

    transactions = _sort_transactions(
        transactions
    )

    inbound_minimum_amount = float(
        config["inbound_minimum_amount"]
    )

    outbound_minimum_amount = float(
        config["outbound_minimum_amount"]
    )

    inbound_transactions = [
        transaction
        for transaction in transactions
        if str(
            transaction.get("receiver_id", "")
        ).strip()
        == customer_id
        and _to_float(transaction.get("amount"))
        >= inbound_minimum_amount
    ]

    outbound_transactions = [
        transaction
        for transaction in transactions
        if str(
            transaction.get("sender_id", "")
        ).strip()
        == customer_id
        and _to_float(transaction.get("amount"))
        >= outbound_minimum_amount
    ]

    matched_pairs = []

    for inbound in inbound_transactions:

        inbound_time = _parse_timestamp(
            inbound
        )

        if inbound_time is None:
            continue

        for outbound in outbound_transactions:

            outbound_time = _parse_timestamp(
                outbound
            )

            if outbound_time is None:
                continue

            time_difference = (
                outbound_time - inbound_time
            )

            if (
                timedelta(0)
                <= time_difference
                <= timedelta(
                    hours=config["window_hours"]
                )
            ):
                matched_pairs.append(
                    {
                        "inbound_transaction_id": (
                            inbound["transaction_id"]
                        ),
                        "outbound_transaction_id": (
                            outbound["transaction_id"]
                        ),
                        "inbound_amount": _to_float(
                            inbound.get("amount")
                        ),
                        "outbound_amount": _to_float(
                            outbound.get("amount")
                        ),
                        "hours_between": round(
                            time_difference.total_seconds()
                            / 3600,
                            2,
                        ),
                    }
                )

    triggered = len(matched_pairs) > 0

    return {
        "rule_id": "RL-04",
        "rule_name": config["name"],
        "triggered": triggered,
        "window_hours": config["window_hours"],
        "inbound_minimum_amount": inbound_minimum_amount,
        "outbound_minimum_amount": outbound_minimum_amount,
        "matched_pairs": matched_pairs,
        "reason": (
            f"{len(matched_pairs)} inbound/outbound "
            f"sequence(s) found within "
            f"{config['window_hours']} hours using "
            f"minimum amounts of "
            f"₹{inbound_minimum_amount:,.0f} inbound and "
            f"₹{outbound_minimum_amount:,.0f} outbound."
        ),
    }


# ============================================================
# RL-05 — Multiple Counterparties
# ============================================================

def check_multiple_counterparties(
    transactions: list[dict[str, Any]],
    customer_id: str,
) -> dict[str, Any]:
    """
    Detect multiple distinct counterparties within a
    24-hour window.

    The customer under investigation is excluded from the
    counterparty set.
    """

    config = RULE_CONFIG["RL-05"]

    transactions = _sort_transactions(
        transactions
    )

    if not transactions:
        return {
            "rule_id": "RL-05",
            "rule_name": config["name"],
            "triggered": False,
            "reason": "No valid transactions available.",
        }

    maximum_counterparties = 0
    maximum_window_transactions = []

    for transaction in transactions:

        timestamp = _parse_timestamp(
            transaction
        )

        window = _transactions_in_window(
            transactions,
            timestamp,
            config["window_hours"],
        )

        counterparties = set()

        for item in window:

            sender = str(
                item.get("sender_id", "")
            ).strip()

            receiver = str(
                item.get("receiver_id", "")
            ).strip()

            if sender and sender != customer_id:
                counterparties.add(sender)

            if receiver and receiver != customer_id:
                counterparties.add(receiver)

        if (
            len(counterparties)
            > maximum_counterparties
        ):
            maximum_counterparties = (
                len(counterparties)
            )
            maximum_window_transactions = window

    triggered = (
        maximum_counterparties
        >= config["minimum_counterparties"]
    )

    return {
        "rule_id": "RL-05",
        "rule_name": config["name"],
        "triggered": triggered,
        "counterparty_count": maximum_counterparties,
        "minimum_counterparties": (
            config["minimum_counterparties"]
        ),
        "transaction_ids": [
            transaction["transaction_id"]
            for transaction in maximum_window_transactions
        ],
        "reason": (
            f"{maximum_counterparties} distinct "
            f"counterparties identified in the maximum "
            f"{config['window_hours']}-hour window."
        ),
    }


# ============================================================
# Master Rules Evaluation
# ============================================================

def evaluate_rules(
    transactions: list[dict[str, Any]],
    customer: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute all deterministic AML indicators for a
    customer investigation.

    This function returns structured evidence only.
    It does not make a final AML disposition.
    """

    customer_id = str(
        customer.get("customer_id", "")
    ).strip()

    results = {
        "RL-01": check_high_velocity(
            transactions,
            customer,
        ),
        "RL-02": check_baseline_deviation(
            transactions,
            customer,
        ),
        "RL-03": check_amount_clustering(
            transactions,
        ),
        "RL-04": check_rapid_in_out(
            transactions,
            customer_id,
        ),
        "RL-05": check_multiple_counterparties(
            transactions,
            customer_id,
        ),
    }

    triggered_rules = [
        rule_id
        for rule_id, result in results.items()
        if result["triggered"]
    ]

    return {
        "rules": results,
        "triggered_rule_ids": triggered_rules,
        "triggered_rule_count": len(
            triggered_rules
        ),
    }