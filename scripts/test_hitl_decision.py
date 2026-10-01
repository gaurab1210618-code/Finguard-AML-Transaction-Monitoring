from app.hitl_decision import (
    create_hitl_decision,
)


print()
print("=" * 80)
print("FinGuard HITL Decision Layer — Test")
print("=" * 80)


# ---------------------------------------------------------------------
# Test 1 — Analyst accepts AI recommendation
# ---------------------------------------------------------------------

print()
print("TEST 1 — CLOSE")
print("-" * 80)

decision = create_hitl_decision(
    alert_id="ALT-0001",
    customer_id="CUST-0001",
    ai_provider="nvidia",
    ai_recommendation="CLOSE_REVIEW",
    ai_risk_assessment="LOW",
    analyst_decision="CLOSE",
    analyst_reason=(
        "Reviewed the supplied evidence and agree "
        "with the AI-assisted assessment."
    ),
)

print(f"Alert:              {decision.alert_id}")
print(f"Customer:            {decision.customer_id}")
print(f"AI Provider:         {decision.ai_provider}")
print(f"AI Risk:             {decision.ai_risk_assessment}")
print(
    f"AI Recommendation:   "
    f"{decision.ai_recommendation}"
)
print(
    f"Analyst Decision:    "
    f"{decision.analyst_decision}"
)
print(
    f"Analyst Reason:      "
    f"{decision.analyst_reason}"
)
print(
    f"Decision Timestamp:  "
    f"{decision.decided_at}"
)


# ---------------------------------------------------------------------
# Test 2 — Analyst escalates
# ---------------------------------------------------------------------

print()
print("TEST 2 — ESCALATE")
print("-" * 80)

decision = create_hitl_decision(
    alert_id="ALT-0002",
    customer_id="CUST-0002",
    ai_provider="nvidia",
    ai_recommendation="ESCALATE_FOR_REVIEW",
    ai_risk_assessment="HIGH",
    analyst_decision="ESCALATE",
    analyst_reason=(
        "Multiple corroborating transaction indicators "
        "require further analyst review."
    ),
)

print(f"Alert:              {decision.alert_id}")
print(f"Customer:            {decision.customer_id}")
print(f"AI Provider:         {decision.ai_provider}")
print(f"AI Risk:             {decision.ai_risk_assessment}")
print(
    f"AI Recommendation:   "
    f"{decision.ai_recommendation}"
)
print(
    f"Analyst Decision:    "
    f"{decision.analyst_decision}"
)
print(
    f"Analyst Reason:      "
    f"{decision.analyst_reason}"
)
print(
    f"Decision Timestamp:  "
    f"{decision.decided_at}"
)


# ---------------------------------------------------------------------
# Test 3 — Analyst overrides AI
# ---------------------------------------------------------------------

print()
print("TEST 3 — OVERRIDE")
print("-" * 80)

decision = create_hitl_decision(
    alert_id="ALT-0002",
    customer_id="CUST-0002",
    ai_provider="nvidia",
    ai_recommendation="ESCALATE_FOR_REVIEW",
    ai_risk_assessment="HIGH",
    analyst_decision="OVERRIDE",
    analyst_reason=(
        "Analyst review identified additional customer "
        "context that changes the recommended handling."
    ),
)

print(f"Alert:              {decision.alert_id}")
print(f"Customer:            {decision.customer_id}")
print(f"AI Provider:         {decision.ai_provider}")
print(f"AI Risk:             {decision.ai_risk_assessment}")
print(
    f"AI Recommendation:   "
    f"{decision.ai_recommendation}"
)
print(
    f"Analyst Decision:    "
    f"{decision.analyst_decision}"
)
print(
    f"Analyst Reason:      "
    f"{decision.analyst_reason}"
)
print(
    f"Decision Timestamp:  "
    f"{decision.decided_at}"
)


# ---------------------------------------------------------------------
# Test 4 — Override without reason must fail
# ---------------------------------------------------------------------

print()
print("TEST 4 — INVALID OVERRIDE")
print("-" * 80)

try:

    create_hitl_decision(
        alert_id="ALT-0002",
        customer_id="CUST-0002",
        ai_provider="nvidia",
        ai_recommendation="ESCALATE_FOR_REVIEW",
        ai_risk_assessment="HIGH",
        analyst_decision="OVERRIDE",
        analyst_reason="",
    )

    print("ERROR: Invalid override was accepted.")

except ValueError as error:

    print("Expected validation failure:")
    print(f"  {error}")


print()
print("=" * 80)
print("HITL decision layer test completed.")
print("=" * 80)