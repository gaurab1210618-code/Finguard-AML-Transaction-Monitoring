import csv

from app.investigation_engine import investigate_alert
from app.ai_investigation import generate_ai_investigation
from app.hitl_decision import create_hitl_decision
from app.audit_db import save_hitl_decision, get_audit_record


def load_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


customers = load_csv("data/customers.csv")
transactions = load_csv("data/transactions.csv")
alerts = load_csv("data/alerts.csv")
case_history = load_csv("data/case_history.csv")


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


ALERT_ID = "ALT-0001"


print()
print("=" * 80)
print("FinGuard — End-to-End HITL + SQLite Audit Test")
print("=" * 80)


# ---------------------------------------------------------------------------
# STEP 1 — ALERT
# ---------------------------------------------------------------------------

alert = get_alert(ALERT_ID)
customer = get_customer(alert["customer_id"])

print()
print("STEP 1 — ALERT")
print("-" * 80)
print(f"Alert ID:        {alert['alert_id']}")
print(f"Customer:        {alert['customer_id']}")
print(f"Alert Type:      {alert['alert_type']}")
print(f"Priority:        {alert['priority']}")
print(f"Trigger Rule:    {alert['trigger_rule']}")


# ---------------------------------------------------------------------------
# STEP 2 — INVESTIGATION ENGINE
# ---------------------------------------------------------------------------

print()
print("STEP 2 — INVESTIGATION ENGINE")
print("-" * 80)

package = investigate_alert(
    alert=alert,
    customer=customer,
    transactions=transactions,
    case_history=case_history,
)

print("Evidence Package: generated successfully.")
print(
    f"Investigation Window: "
    f"{package['investigation_context']['window_start']} → "
    f"{package['investigation_context']['window_end']}"
)
print(
    "Transactions in Context: "
    f"{package['investigation_context']['transaction_count']}"
)


# ---------------------------------------------------------------------------
# STEP 3 — AI INVESTIGATION
# ---------------------------------------------------------------------------

print()
print("STEP 3 — AI INVESTIGATION")
print("-" * 80)

print("Calling configured AI provider routing...")

ai_result = generate_ai_investigation(package)

print("Actual AI Result:")
print(f"Provider:              {ai_result.provider}")
print(f"Risk Assessment:       {ai_result.risk_assessment}")
print(f"Recommended Next Step: {ai_result.recommended_next_step}")


# ---------------------------------------------------------------------------
# STEP 4 — HUMAN ANALYST REVIEW
# ---------------------------------------------------------------------------

print()
print("STEP 4 — HUMAN ANALYST REVIEW")
print("-" * 80)

analyst_decision = "CLOSE"

analyst_reason = (
    "Analyst reviewed the Evidence Package and agrees "
    "with the AI-assisted recommendation for this "
    "isolated baseline deviation."
)

print(
    f"AI Recommendation:     "
    f"{ai_result.recommended_next_step}"
)
print(
    f"AI Risk Assessment:    "
    f"{ai_result.risk_assessment}"
)
print(f"Analyst Decision:      {analyst_decision}")
print(f"Analyst Reason:        {analyst_reason}")


# ---------------------------------------------------------------------------
# STEP 5 — HITL DECISION
# ---------------------------------------------------------------------------

print()
print("STEP 5 — HITL DECISION VALIDATION")
print("-" * 80)

hitl_decision = create_hitl_decision(
    alert_id=alert["alert_id"],
    customer_id=alert["customer_id"],
    ai_provider=ai_result.provider,
    ai_recommendation=ai_result.recommended_next_step,
    ai_risk_assessment=ai_result.risk_assessment,
    analyst_decision=analyst_decision,
    analyst_reason=analyst_reason,
)

print("HITL decision validated successfully.")


# ---------------------------------------------------------------------------
# STEP 6 — SQLITE AUDIT PERSISTENCE
# ---------------------------------------------------------------------------

print()
print("STEP 6 — SQLITE AUDIT PERSISTENCE")
print("-" * 80)

case_id = save_hitl_decision(hitl_decision)

print("HITL decision persisted successfully.")
print(f"Generated Case ID:    {case_id}")


# ---------------------------------------------------------------------------
# STEP 7 — READ BACK FROM SQLITE
# ---------------------------------------------------------------------------

print()
print("STEP 7 — SQLITE AUDIT VERIFICATION")
print("-" * 80)

audit_record = get_audit_record(case_id)

assert audit_record is not None

assert audit_record["case_id"] == case_id
assert audit_record["alert_id"] == hitl_decision.alert_id
assert audit_record["customer_id"] == hitl_decision.customer_id

assert audit_record["ai_provider"] == hitl_decision.ai_provider
assert (
    audit_record["ai_recommendation"]
    == hitl_decision.ai_recommendation
)
assert (
    audit_record["ai_risk_assessment"]
    == hitl_decision.ai_risk_assessment
)

assert (
    audit_record["analyst_decision"]
    == hitl_decision.analyst_decision
)

assert (
    audit_record["analyst_reason"]
    == hitl_decision.analyst_reason
)

assert (
    audit_record["decided_at"]
    == hitl_decision.decided_at
)

print("Audit record retrieved successfully.")
print()
print(f"Case ID:               {audit_record['case_id']}")
print(f"Alert ID:              {audit_record['alert_id']}")
print(f"Customer ID:           {audit_record['customer_id']}")
print(f"AI Provider:           {audit_record['ai_provider']}")
print(f"AI Risk Assessment:    {audit_record['ai_risk_assessment']}")
print(f"AI Recommendation:     {audit_record['ai_recommendation']}")
print(f"Analyst Decision:      {audit_record['analyst_decision']}")
print(f"Analyst Reason:        {audit_record['analyst_reason']}")
print(f"Decision Timestamp:    {audit_record['decided_at']}")
print(f"Recorded At:           {audit_record['recorded_at']}")


# ---------------------------------------------------------------------------
# FINAL VALIDATION
# ---------------------------------------------------------------------------

print()
print("=" * 80)
print("FINAL CASE OUTCOME")
print("=" * 80)

print(f"Alert ID:              {hitl_decision.alert_id}")
print(f"Customer ID:           {hitl_decision.customer_id}")
print(f"Case ID:               {case_id}")
print(f"AI Provider:           {hitl_decision.ai_provider}")
print(f"AI Risk Assessment:    {hitl_decision.ai_risk_assessment}")
print(f"AI Recommendation:     {hitl_decision.ai_recommendation}")
print(f"Analyst Decision:      {hitl_decision.analyst_decision}")
print(f"Analyst Reason:        {hitl_decision.analyst_reason}")
print(f"Decision Timestamp:    {hitl_decision.decided_at}")
print(f"Recorded At:           {audit_record['recorded_at']}")

print()
print("=" * 80)
print("END-TO-END HITL + SQLITE AUDIT TEST PASSED")
print("=" * 80)