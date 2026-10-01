import csv

from app.investigation_engine import investigate_alert
from app.ai_investigation import generate_ai_investigation


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
# AI integration test
# ---------------------------------------------------------------------

ALERT_ID = "ALT-0001"


print()
print("=" * 80)
print("FinGuard AI Investigation — Provider Integration Test")
print("=" * 80)


alert = get_alert(ALERT_ID)
customer = get_customer(alert["customer_id"])


# ---------------------------------------------------------------------
# Build deterministic Evidence Package
# ---------------------------------------------------------------------

package = investigate_alert(
    alert=alert,
    transactions=transactions,
    customer=customer,
    case_history=case_history,
)


print()
print("DETERMINISTIC EVIDENCE PACKAGE")
print("-" * 80)

print(f"Alert ID:       {alert['alert_id']}")
print(f"Customer:       {alert['customer_id']}")
print(f"Trigger Rule:   {alert['trigger_rule']}")
print(
    "Evidence:       "
    f"{alert['evidence_transaction_ids']}"
)


# ---------------------------------------------------------------------
# AI investigation
# ---------------------------------------------------------------------

print()
print("AI INVESTIGATION")
print("-" * 80)

print("Calling configured AI providers...")
print("Primary Provider:  NVIDIA")
print("Fallback Provider: Gemini")


result = generate_ai_investigation(package)


# ---------------------------------------------------------------------
# Display result
# ---------------------------------------------------------------------

print()
print("AI RESULT")
print("-" * 80)

print(
    f"AI Provider Used:       "
    f"{result.provider}"
)

print(
    f"Risk Assessment:        "
    f"{result.risk_assessment}"
)

print(
    f"Recommended Next Step:  "
    f"{result.recommended_next_step}"
)


print()
print("Investigation Summary:")
print(result.investigation_summary)


print()
print("Key Findings:")
print("-" * 80)

for index, finding in enumerate(result.key_findings, start=1):

    print(
        f"{index}. {finding.finding}"
    )

    print(
        f"   Significance: "
        f"{finding.significance}"
    )

    print("   Evidence:")

    for reference in finding.evidence_references:

        print(
            f"      - "
            f"{reference.reference_type}="
            f"{reference.reference_id}"
        )


print()
print("Rationale:")
print(result.rationale)


print()
print("Evidence Gaps:")

if result.evidence_gaps:

    for gap in result.evidence_gaps:
        print(f"  - {gap}")

else:
    print("  None identified.")


print()
print("Analyst Warning:")
print(result.analyst_warning)


print()
print("=" * 80)
print("AI integration test completed successfully.")
print("=" * 80)