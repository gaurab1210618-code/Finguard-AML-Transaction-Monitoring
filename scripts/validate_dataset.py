import csv
from pathlib import Path


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FILES = {
    "customers": DATA_DIR / "customers.csv",
    "transactions": DATA_DIR / "transactions.csv",
    "alerts": DATA_DIR / "alerts.csv",
    "case_history": DATA_DIR / "case_history.csv",
    "scenario_metadata": DATA_DIR / "scenario_metadata.csv",
}


# ---------------------------------------------------------
# CSV loader
# ---------------------------------------------------------

def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


# ---------------------------------------------------------
# Load datasets
# ---------------------------------------------------------

customers = load_csv(FILES["customers"])
transactions = load_csv(FILES["transactions"])
alerts = load_csv(FILES["alerts"])
case_history = load_csv(FILES["case_history"])
scenarios = load_csv(FILES["scenario_metadata"])


# ---------------------------------------------------------
# Basic counts
# ---------------------------------------------------------

print("=" * 60)
print("FinGuard Dataset Validation")
print("=" * 60)

print(f"Customers:          {len(customers)}")
print(f"Transactions:       {len(transactions)}")
print(f"Alerts:             {len(alerts)}")
print(f"Case History:       {len(case_history)}")
print(f"Scenarios:          {len(scenarios)}")


# ---------------------------------------------------------
# Expected row counts
# ---------------------------------------------------------

expected_counts = {
    "Customers": 300,
    "Transactions": 12000,
    "Alerts": 200,
    "Case History": 100,
    "Scenarios": 3,
}

actual_counts = {
    "Customers": len(customers),
    "Transactions": len(transactions),
    "Alerts": len(alerts),
    "Case History": len(case_history),
    "Scenarios": len(scenarios),
}

print("\nRow-count validation:")

for name, expected in expected_counts.items():
    actual = actual_counts[name]

    if actual == expected:
        print(f"  PASS  {name}: {actual}")
    else:
        print(f"  FAIL  {name}: expected {expected}, found {actual}")


# ---------------------------------------------------------
# Build ID sets
# ---------------------------------------------------------

customer_ids = {row["customer_id"] for row in customers}
transaction_ids = {row["transaction_id"] for row in transactions}
alert_ids = {row["alert_id"] for row in alerts}


# ---------------------------------------------------------
# Customer references
# ---------------------------------------------------------

print("\nCustomer reference validation:")

transaction_customers = {
    row["customer_id"] for row in transactions
}

alert_customers = {
    row["customer_id"] for row in alerts
}

case_customers = {
    row["customer_id"] for row in case_history
}

invalid_transaction_customers = transaction_customers - customer_ids
invalid_alert_customers = alert_customers - customer_ids
invalid_case_customers = case_customers - customer_ids


def report_reference_check(name, invalid_ids):
    if not invalid_ids:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}: {len(invalid_ids)} invalid references")
        print(f"        {sorted(invalid_ids)[:10]}")


report_reference_check(
    "Transactions → Customers",
    invalid_transaction_customers,
)

report_reference_check(
    "Alerts → Customers",
    invalid_alert_customers,
)

report_reference_check(
    "Case History → Customers",
    invalid_case_customers,
)


# ---------------------------------------------------------
# Historical alert references
# ---------------------------------------------------------

print("\nHistorical alert validation:")

invalid_previous_alerts = set()

for row in case_history:
    previous_alert_id = row["previous_alert_id"].strip()

    if previous_alert_id and previous_alert_id not in alert_ids:
        invalid_previous_alerts.add(previous_alert_id)

report_reference_check(
    "Case History → Previous Alert",
    invalid_previous_alerts,
)


# ---------------------------------------------------------
# Alert status
# ---------------------------------------------------------

print("\nAlert status validation:")

status_counts = {}

for row in alerts:
    status = row["status"]
    status_counts[status] = status_counts.get(status, 0) + 1

for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")

if all(row["status"] == "OPEN" for row in alerts):
    print("  PASS  All alerts are OPEN")
else:
    print("  INFO  Some alerts are not OPEN")


# ---------------------------------------------------------
# Canonical scenarios
# ---------------------------------------------------------

print("\nCanonical scenario validation:")

expected_scenarios = {
    "SCN_001",
    "SCN_002",
    "SCN_003",
}

actual_scenarios = {
    row["scenario_id"] for row in scenarios
}

missing_scenarios = expected_scenarios - actual_scenarios

if not missing_scenarios:
    print("  PASS  SCN_001, SCN_002 and SCN_003 present")
else:
    print(f"  FAIL  Missing scenarios: {missing_scenarios}")


# ---------------------------------------------------------
# Scenario → Alert → Customer consistency
# ---------------------------------------------------------

print("\nScenario relationship validation:")

alerts_by_id = {
    row["alert_id"]: row
    for row in alerts
}

customers_by_id = {
    row["customer_id"]: row
    for row in customers
}

scenario_failures = []

for scenario in scenarios:
    scenario_id = scenario["scenario_id"]
    customer_id = scenario["customer_id"]
    alert_id = scenario["alert_id"]

    alert = alerts_by_id.get(alert_id)

    if alert is None:
        scenario_failures.append(
            f"{scenario_id}: alert {alert_id} not found"
        )
        continue

    if alert["customer_id"] != customer_id:
        scenario_failures.append(
            f"{scenario_id}: customer mismatch"
        )

if not scenario_failures:
    print("  PASS  Scenario → Alert → Customer relationships")
else:
    print("  FAIL")
    for failure in scenario_failures:
        print(f"{failure}")

# ---------------------------------------------------------
# Alert evidence validation
# ---------------------------------------------------------

print("\nAlert evidence validation:")

transactions_by_id = {
    row["transaction_id"]: row
    for row in transactions
}

evidence_failures = []

for alert in alerts:
    evidence_ids = [
        x.strip()
        for x in alert["evidence_transaction_ids"].split("|")
        if x.strip()
    ]

    if not evidence_ids:
        evidence_failures.append(
            f"{alert['alert_id']}: no evidence transaction IDs"
        )
        continue

    for transaction_id in evidence_ids:
        transaction = transactions_by_id.get(transaction_id)

        if transaction is None:
            evidence_failures.append(
                f"{alert['alert_id']}: transaction {transaction_id} not found"
            )
            continue

        if transaction["customer_id"] != alert["customer_id"]:
            evidence_failures.append(
                f"{alert['alert_id']}: evidence transaction "
                f"{transaction_id} belongs to another customer"
            )

if not evidence_failures:
    print("  PASS  All alert evidence references are valid")
else:
    print(f"  FAIL  {len(evidence_failures)} evidence problems found")

    for failure in evidence_failures[:20]:
        print(f"{failure}")


# ---------------------------------------------------------
# Historical case timing validation
# ---------------------------------------------------------

print("\nHistorical case timing validation:")

from datetime import datetime

alerts_by_id = {
    row["alert_id"]: row
    for row in alerts
}

history_failures = []

for case in case_history:

    previous_alert_id = case["previous_alert_id"].strip()

    if not previous_alert_id:
        continue

    previous_alert = alerts_by_id.get(previous_alert_id)

    if previous_alert is None:
        continue

    try:
        case_time = datetime.fromisoformat(
            case["created_at"].replace("Z", "+00:00")
        )

        alert_time = datetime.fromisoformat(
            previous_alert["created_at"].replace("Z", "+00:00")
        )

        if case_time < alert_time:
            history_failures.append(
                f"{case['case_id']}: case created before its previous alert"
            )

    except ValueError:
        history_failures.append(
            f"{case['case_id']}: invalid timestamp format"
        )


if not history_failures:
    print("  PASS  Historical case timestamps are valid")
else:
    print(f"  FAIL  {len(history_failures)} timing problems found")

    for failure in history_failures[:20]:
        print(f"{failure}")
# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("Validation complete.")
print("=" * 60)