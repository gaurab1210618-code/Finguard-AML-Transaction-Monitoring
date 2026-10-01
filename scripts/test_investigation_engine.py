import csv

from app.investigation_engine import investigate_alert


# ---------------------------------------------------------------------
# Load dataset
# ---------------------------------------------------------------------

def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


customers = load_csv("data/customers.csv")
transactions = load_csv("data/transactions.csv")
alerts = load_csv("data/alerts.csv")
case_history = load_csv("data/case_history.csv")


# ---------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------

def get_customer(customer_id):
    return next(
        customer
        for customer in customers
        if customer["customer_id"] == customer_id
    )


def get_alert(alert_id):
    return next(
        alert
        for alert in alerts
        if alert["alert_id"] == alert_id
    )


# ---------------------------------------------------------------------
# Scenario test
# ---------------------------------------------------------------------

SCENARIOS = [
    {
        "scenario_id": "SCN_001",
        "scenario_name": "Explainable One-off Deviation",
        "alert_id": "ALT-0001",
    },
    {
        "scenario_id": "SCN_002",
        "scenario_name": "Structuring-like Pattern",
        "alert_id": "ALT-0002",
    },
    {
        "scenario_id": "SCN_003",
        "scenario_name": "Rapid Inbound-Outbound Pattern",
        "alert_id": "ALT-0003",
    },
]


print()
print("=" * 80)
print("FinGuard Investigation Engine — Canonical Scenario Test")
print("=" * 80)


for scenario in SCENARIOS:

    alert = get_alert(scenario["alert_id"])
    customer = get_customer(alert["customer_id"])

    package = investigate_alert(
        alert=alert,
        transactions=transactions,
        customer=customer,
        case_history=case_history,
    )

    print()
    print("=" * 80)
    print(
        f"{scenario['scenario_id']} - "
        f"{scenario['scenario_name']}"
    )
    print("=" * 80)

    # -------------------------------------------------------------
    # Alert
    # -------------------------------------------------------------

    print()
    print("ALERT")
    print("-" * 80)

    print(f"Alert ID:       {alert['alert_id']}")
    print(f"Customer:       {alert['customer_id']}")
    print(f"Alert Type:     {alert['alert_type']}")
    print(f"Priority:       {alert['priority']}")
    print(f"Trigger Rule:   {alert['trigger_rule']}")
    print(
        "Evidence:       "
        f"{alert['evidence_transaction_ids']}"
    )

    # -------------------------------------------------------------
    # Primary alert trigger
    # -------------------------------------------------------------

    trigger = package["alert_trigger"]

    print()
    print("PRIMARY ALERT TRIGGER")
    print("-" * 80)

    print(f"Rule:     {trigger['rule']}")
    print(
        "Evidence: "
        f"{', '.join(trigger['evidence_transaction_ids'])}"
    )

    # -------------------------------------------------------------
    # Investigation context
    # -------------------------------------------------------------

    context = package["investigation_context"]

    print()
    print("INVESTIGATION CONTEXT")
    print("-" * 80)

    print(
        f"Window: {context['window_start']} "
        f"→ {context['window_end']}"
    )

    print(
        f"Transactions in context: "
        f"{context['transaction_count']}"
    )

    print(
        "Transaction IDs: "
        f"{', '.join(context['transaction_ids'])}"
    )

    # -------------------------------------------------------------
    # Contextual indicators
    # -------------------------------------------------------------

    print()
    print("CONTEXTUAL INDICATORS")
    print("-" * 80)

    indicators = package["contextual_indicators"]

    if not indicators:
        print("No contextual indicators evaluated.")
    else:

        for indicator in indicators:

            status = (
                "TRIGGERED"
                if indicator["triggered"]
                else "NOT TRIGGERED"
            )

            print(
                f"{indicator['rule_id']} - "
                f"{indicator['rule_name']}: "
                f"{status}"
            )

            print(
                f"  Reason: "
                f"{indicator['reason']}"
            )

    # -------------------------------------------------------------
    # Historical context
    # -------------------------------------------------------------

    history = package["historical_signals"]

    print()
    print("HISTORICAL CUSTOMER CONTEXT")
    print("-" * 80)

    print(
        f"Risk tier:           "
        f"{history['risk_tier']}"
    )

    print(
        f"Prior cases:         "
        f"{history['prior_case_count']}"
    )

    print(
        f"Prior escalations:   "
        f"{history['prior_escalation_count']}"
    )

    print(
        f"Monthly avg volume:  "
        f"{history['monthly_avg_volume']}"
    )

    print(
        f"Monthly avg txns:    "
        f"{history['monthly_avg_txn_count']}"
    )


print()
print("=" * 80)
print("Canonical investigation test completed.")
print("=" * 80)