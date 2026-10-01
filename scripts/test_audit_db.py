from app.hitl_decision import (
    create_hitl_decision,
)

from app.audit_db import (
    DATABASE_PATH,
    get_audit_record,
    save_hitl_decision,
)


print()
print("=" * 80)
print("FinGuard SQLite Audit Trail — Test")
print("=" * 80)


# ---------------------------------------------------------------------
# 1. Create a realistic HITL decision
# ---------------------------------------------------------------------

print()
print("STEP 1 — CREATE HITL DECISION")
print("-" * 80)

decision = create_hitl_decision(
    alert_id="ALT-0001",
    customer_id="CUST-0001",
    ai_provider="nvidia",
    ai_recommendation="CLOSE_REVIEW",
    ai_risk_assessment="LOW",
    analyst_decision="CLOSE",
    analyst_reason=(
        "Analyst reviewed the Evidence Package and agrees "
        "with the AI-assisted recommendation for this "
        "isolated baseline deviation."
    ),
)

print("HITL decision created successfully.")

print(
    f"Alert:              "
    f"{decision.alert_id}"
)

print(
    f"Customer:           "
    f"{decision.customer_id}"
)

print(
    f"AI Provider:        "
    f"{decision.ai_provider}"
)

print(
    f"AI Risk:             "
    f"{decision.ai_risk_assessment}"
)

print(
    f"AI Recommendation:  "
    f"{decision.ai_recommendation}"
)

print(
    f"Analyst Decision:   "
    f"{decision.analyst_decision}"
)


# ---------------------------------------------------------------------
# 2. Save to SQLite
# ---------------------------------------------------------------------

print()
print("STEP 2 — WRITE AUDIT RECORD")
print("-" * 80)

case_id = save_hitl_decision(
    decision
)

print(
    f"Audit record saved successfully."
)

print(
    f"Case ID:            "
    f"{case_id}"
)

print(
    f"Database:           "
    f"{DATABASE_PATH}"
)


# ---------------------------------------------------------------------
# 3. Read the record back from SQLite
# ---------------------------------------------------------------------

print()
print("STEP 3 — READ AUDIT RECORD")
print("-" * 80)

record = get_audit_record(
    case_id
)


if record is None:

    raise RuntimeError(
        "Audit record could not be retrieved."
    )


print(
    f"Audit ID:            "
    f"{record['audit_id']}"
)

print(
    f"Case ID:             "
    f"{record['case_id']}"
)

print(
    f"Alert ID:            "
    f"{record['alert_id']}"
)

print(
    f"Customer ID:         "
    f"{record['customer_id']}"
)

print(
    f"AI Provider:         "
    f"{record['ai_provider']}"
)

print(
    f"AI Risk Assessment:  "
    f"{record['ai_risk_assessment']}"
)

print(
    f"AI Recommendation:   "
    f"{record['ai_recommendation']}"
)

print(
    f"Analyst Decision:    "
    f"{record['analyst_decision']}"
)

print(
    f"Analyst Reason:      "
    f"{record['analyst_reason']}"
)

print(
    f"Decision Timestamp:  "
    f"{record['decided_at']}"
)

print(
    f"Recorded At:         "
    f"{record['recorded_at']}"
)


# ---------------------------------------------------------------------
# 4. Verify persistence
# ---------------------------------------------------------------------

print()
print("STEP 4 — AUDIT VALIDATION")
print("-" * 80)

assert record["case_id"] == case_id

assert (
    record["alert_id"]
    == decision.alert_id
)

assert (
    record["customer_id"]
    == decision.customer_id
)

assert (
    record["ai_provider"]
    == decision.ai_provider
)

assert (
    record["ai_risk_assessment"]
    == decision.ai_risk_assessment
)

assert (
    record["ai_recommendation"]
    == decision.ai_recommendation
)

assert (
    record["analyst_decision"]
    == decision.analyst_decision
)

assert (
    record["analyst_reason"]
    == decision.analyst_reason
)

assert (
    record["decided_at"]
    == decision.decided_at
)

print(
    "All audit fields verified successfully."
)


print()
print("=" * 80)
print("SQLITE AUDIT TRAIL TEST PASSED")
print("=" * 80)