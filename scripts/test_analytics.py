from app.analytics import (
    get_total_cases,
    get_decision_distribution,
    get_risk_distribution,
    get_ai_human_outcomes,
    get_override_rate,
    get_escalation_rate,
    get_provider_distribution,
    get_cases_by_date,
)


print()
print("=" * 80)
print("FinGuard SQL Analytics — Test")
print("=" * 80)


# ---------------------------------------------------------------------------
# 1. TOTAL CASES
# ---------------------------------------------------------------------------

print()
print("1. TOTAL CASES")
print("-" * 80)

total_cases = get_total_cases()

print(f"Total cases: {total_cases}")

assert total_cases >= 1


# ---------------------------------------------------------------------------
# 2. DECISION DISTRIBUTION
# ---------------------------------------------------------------------------

print()
print("2. DECISION DISTRIBUTION")
print("-" * 80)

decision_distribution = get_decision_distribution()

for row in decision_distribution:
    print(
        f"{row['analyst_decision']}: "
        f"{row['case_count']}"
    )

decision_total = sum(
    row["case_count"]
    for row in decision_distribution
)

assert decision_total == total_cases


# ---------------------------------------------------------------------------
# 3. AI RISK DISTRIBUTION
# ---------------------------------------------------------------------------

print()
print("3. AI RISK DISTRIBUTION")
print("-" * 80)

risk_distribution = get_risk_distribution()

for row in risk_distribution:
    print(
        f"{row['ai_risk_assessment']}: "
        f"{row['case_count']}"
    )

risk_total = sum(
    row["case_count"]
    for row in risk_distribution
)

assert risk_total == total_cases


# ---------------------------------------------------------------------------
# 4. AI RECOMMENDATION VS HUMAN DECISION
# ---------------------------------------------------------------------------

print()
print("4. AI RECOMMENDATION VS HUMAN DECISION")
print("-" * 80)

ai_human_outcomes = get_ai_human_outcomes()

for row in ai_human_outcomes:
    print(
        f"{row['ai_recommendation']} "
        f"→ "
        f"{row['analyst_decision']}: "
        f"{row['case_count']}"
    )

outcome_total = sum(
    row["case_count"]
    for row in ai_human_outcomes
)

assert outcome_total == total_cases


# ---------------------------------------------------------------------------
# 5. OVERRIDE RATE
# ---------------------------------------------------------------------------

print()
print("5. OVERRIDE RATE")
print("-" * 80)

override_rate = get_override_rate()

print(f"Override rate: {override_rate:.1f}%")

expected_override_rate = (
    next(
        (
            row["case_count"]
            for row in decision_distribution
            if row["analyst_decision"] == "OVERRIDE"
        ),
        0,
    )
    / total_cases
) * 100

assert round(override_rate, 1) == round(
    expected_override_rate,
    1,
)


# ---------------------------------------------------------------------------
# 6. ESCALATION RATE
# ---------------------------------------------------------------------------

print()
print("6. ESCALATION RATE")
print("-" * 80)

escalation_rate = get_escalation_rate()

print(f"Escalation rate: {escalation_rate:.1f}%")

expected_escalation_rate = (
    next(
        (
            row["case_count"]
            for row in decision_distribution
            if row["analyst_decision"] == "ESCALATE"
        ),
        0,
    )
    / total_cases
) * 100

assert round(escalation_rate, 1) == round(
    expected_escalation_rate,
    1,
)


# ---------------------------------------------------------------------------
# 7. PROVIDER DISTRIBUTION
# ---------------------------------------------------------------------------

print()
print("7. PROVIDER DISTRIBUTION")
print("-" * 80)

provider_distribution = get_provider_distribution()

for row in provider_distribution:
    print(
        f"{row['ai_provider']}: "
        f"{row['case_count']}"
    )

provider_total = sum(
    row["case_count"]
    for row in provider_distribution
)

assert provider_total == total_cases


# ---------------------------------------------------------------------------
# 8. CASES BY DATE
# ---------------------------------------------------------------------------

print()
print("8. CASES BY DATE")
print("-" * 80)

cases_by_date = get_cases_by_date()

for row in cases_by_date:
    print(
        f"{row['case_date']}: "
        f"{row['case_count']}"
    )

date_total = sum(
    row["case_count"]
    for row in cases_by_date
)

assert date_total == total_cases


# ---------------------------------------------------------------------------
# Final result
# ---------------------------------------------------------------------------

print()
print("=" * 80)
print("SQL ANALYTICS TEST PASSED")
print("=" * 80)