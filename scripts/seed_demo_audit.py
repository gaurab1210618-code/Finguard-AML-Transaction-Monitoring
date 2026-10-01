from app.hitl_decision import create_hitl_decision
from app.audit_db import save_hitl_decision


print()
print("=" * 80)
print("FinGuard — Synthetic Demo Audit Data Seeder")
print("=" * 80)


demo_cases = [
    {
        "alert_id": "ALT-0001",
        "customer_id": "CUST-0001",
        "ai_provider": "nvidia",
        "ai_recommendation": "CLOSE_REVIEW",
        "ai_risk_assessment": "LOW",
        "analyst_decision": "CLOSE",
        "analyst_reason": (
            "Analyst reviewed the evidence and determined "
            "the activity was an explainable deviation."
        ),
    },
    {
        "alert_id": "ALT-0002",
        "customer_id": "CUST-0002",
        "ai_provider": "nvidia",
        "ai_recommendation": "ESCALATE_FOR_REVIEW",
        "ai_risk_assessment": "HIGH",
        "analyst_decision": "ESCALATE",
        "analyst_reason": (
            "Multiple corroborating transaction indicators "
            "require further investigation."
        ),
    },
    {
        "alert_id": "ALT-0003",
        "customer_id": "CUST-0003",
        "ai_provider": "nvidia",
        "ai_recommendation": "ESCALATE_FOR_REVIEW",
        "ai_risk_assessment": "HIGH",
        "analyst_decision": "ESCALATE",
        "analyst_reason": (
            "Rapid inbound and outbound movement requires "
            "additional analyst review."
        ),
    },
    {
        "alert_id": "ALT-0002",
        "customer_id": "CUST-0002",
        "ai_provider": "nvidia",
        "ai_recommendation": "ESCALATE_FOR_REVIEW",
        "ai_risk_assessment": "HIGH",
        "analyst_decision": "OVERRIDE",
        "analyst_reason": (
            "Analyst reviewed additional customer context "
            "and changed the recommended handling."
        ),
    },
    {
        "alert_id": "ALT-0001",
        "customer_id": "CUST-0001",
        "ai_provider": "nvidia",
        "ai_recommendation": "CLOSE_REVIEW",
        "ai_risk_assessment": "LOW",
        "analyst_decision": "CLOSE",
        "analyst_reason": (
            "Analyst confirmed the activity was consistent "
            "with an isolated explainable deviation."
        ),
    },
    {
        "alert_id": "ALT-0003",
        "customer_id": "CUST-0003",
        "ai_provider": "nvidia",
        "ai_recommendation": "ESCALATE_FOR_REVIEW",
        "ai_risk_assessment": "HIGH",
        "analyst_decision": "OVERRIDE",
        "analyst_reason": (
            "Analyst considered additional context before "
            "selecting an alternative disposition."
        ),
    },
]


print()
print("Creating synthetic demonstration audit records...")
print("NOTE: These records are for dashboard demonstration only.")
print()


for index, case in enumerate(demo_cases, start=1):

    decision = create_hitl_decision(
        alert_id=case["alert_id"],
        customer_id=case["customer_id"],
        ai_provider=case["ai_provider"],
        ai_recommendation=case["ai_recommendation"],
        ai_risk_assessment=case["ai_risk_assessment"],
        analyst_decision=case["analyst_decision"],
        analyst_reason=case["analyst_reason"],
    )

    case_id = save_hitl_decision(decision)

    print(
        f"{index}. {case_id} | "
        f"{case['alert_id']} | "
        f"{case['ai_risk_assessment']} | "
        f"{case['analyst_decision']}"
    )


print()
print("=" * 80)
print("DEMO AUDIT DATA SEEDING COMPLETE")
print("=" * 80)