import csv
import sys
from pathlib import Path

# Allow importing from the app directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"

sys.path.insert(0, str(APP_DIR))

from rules_engine import evaluate_rules


def load_csv(filename):
    """Load a CSV file from the project's data folder."""
    path = PROJECT_ROOT / "data" / filename

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def get_customer(customers, customer_id):
    """Return a customer by customer ID."""
    for customer in customers:
        if customer["customer_id"] == customer_id:
            return customer

    raise ValueError(
        f"Customer not found: {customer_id}"
    )


def get_alert(alerts, alert_id):
    """Return an alert by alert ID."""
    for alert in alerts:
        if alert["alert_id"] == alert_id:
            return alert

    raise ValueError(
        f"Alert not found: {alert_id}"
    )


def get_customer_transactions(
    transactions,
    customer_id,
):
    """
    Return transactions belonging to the customer
    under investigation.
    """

    return [
        transaction
        for transaction in transactions
        if (
            transaction.get("sender_id") == customer_id
            or transaction.get("receiver_id") == customer_id
        )
    ]


def print_rule_result(rule_id, result):
    """Print a readable rule result."""

    status = (
        "TRIGGERED"
        if result["triggered"]
        else "NOT TRIGGERED"
    )

    print(f"\n  {rule_id} - {result['rule_name']}")
    print(f"  Status: {status}")
    print(f"  Reason: {result['reason']}")


def run_scenario(
    scenario_name,
    alert_id,
    customer_id,
    customers,
    alerts,
    transactions,
):
    """Evaluate one canonical investigation scenario."""

    print("\n" + "=" * 70)
    print(f"SCENARIO: {scenario_name}")
    print(f"Alert:    {alert_id}")
    print(f"Customer: {customer_id}")
    print("=" * 70)

    customer = get_customer(
        customers,
        customer_id,
    )

    alert = get_alert(
        alerts,
        alert_id,
    )

    customer_transactions = get_customer_transactions(
        transactions,
        customer_id,
    )

    print(
        f"\nAlert status: {alert.get('status')}"
    )

    print(
        f"Customer transactions loaded: "
        f"{len(customer_transactions)}"
    )

    result = evaluate_rules(
        customer_transactions,
        customer,
    )

    print("\nTriggered rules:")

    if result["triggered_rule_ids"]:
        print(
            ", ".join(
                result["triggered_rule_ids"]
            )
        )
    else:
        print("None")

    print(
        f"\nTotal triggered rules: "
        f"{result['triggered_rule_count']}"
    )

    print("\nDetailed rule results:")

    for rule_id, rule_result in result["rules"].items():
        print_rule_result(
            rule_id,
            rule_result,
        )


def main():
    """Run the deterministic rules-engine test."""

    customers = load_csv("customers.csv")
    alerts = load_csv("alerts.csv")
    transactions = load_csv("transactions.csv")

    print("\nFinGuard Rules Engine Test")
    print("=" * 70)

    print(
        f"Customers loaded:    {len(customers)}"
    )

    print(
        f"Alerts loaded:       {len(alerts)}"
    )

    print(
        f"Transactions loaded: {len(transactions)}"
    )

    # --------------------------------------------------------
    # Canonical Scenario 1
    # --------------------------------------------------------

    run_scenario(
        scenario_name="SCN_001 - False Positive",
        alert_id="ALT-0001",
        customer_id="CUST-0001",
        customers=customers,
        alerts=alerts,
        transactions=transactions,
    )

    # --------------------------------------------------------
    # Canonical Scenario 2
    # --------------------------------------------------------

    run_scenario(
        scenario_name="SCN_002 - Structuring-like Pattern",
        alert_id="ALT-0002",
        customer_id="CUST-0002",
        customers=customers,
        alerts=alerts,
        transactions=transactions,
    )

    # --------------------------------------------------------
    # Canonical Scenario 3
    # --------------------------------------------------------

    run_scenario(
        scenario_name="SCN_003 - Rapid Inbound-Outbound Pattern",
        alert_id="ALT-0003",
        customer_id="CUST-0003",
        customers=customers,
        alerts=alerts,
        transactions=transactions,
    )

    print("\n" + "=" * 70)
    print("Rules engine test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()