"""
FinGuard — Illustrative ROI / Business Case Model

Purpose:
    Estimate the potential operational value of the FinGuard
    AI-assisted AML transaction-monitoring investigation workflow.

Important:
    This is an illustrative business-case model, not a measured
    production ROI calculation.

    All inputs are explicit assumptions so that a BA, manager,
    or interviewer can change them and immediately see the
    impact on the business case.

Model:
    Current monthly effort
        = monthly alerts × current minutes per alert

    AI-assisted monthly effort
        = monthly alerts × AI-assisted minutes per alert

    Monthly time saved
        = current monthly effort - AI-assisted monthly effort

    Monthly labor savings
        = monthly time saved × analyst hourly cost

    Annual labor savings
        = monthly labor savings × 12

    Net annual benefit
        = annual labor savings - implementation cost

    ROI
        = (net annual benefit / implementation cost) × 100

    Payback period
        = implementation cost / monthly labor savings
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================
# Default Business-Case Assumptions
# ============================================================

DEFAULT_MONTHLY_ALERTS = 200
DEFAULT_CURRENT_MINUTES_PER_ALERT = 90.0
DEFAULT_AI_ASSISTED_MINUTES_PER_ALERT = 30.0
DEFAULT_ANALYST_HOURLY_COST = 800.0
DEFAULT_IMPLEMENTATION_COST = 250000.0


# ============================================================
# ROI Result
# ============================================================

@dataclass(frozen=True)
class ROIResult:
    """
    Calculated outputs from the FinGuard business-case model.
    """

    monthly_alerts: int

    current_minutes_per_alert: float
    ai_assisted_minutes_per_alert: float

    analyst_hourly_cost: float
    implementation_cost: float

    current_monthly_hours: float
    ai_assisted_monthly_hours: float
    monthly_hours_saved: float

    monthly_labor_savings: float
    annual_labor_savings: float

    net_annual_benefit: float
    roi_percentage: float
    payback_months: float


# ============================================================
# Validation
# ============================================================

def validate_assumptions(
    monthly_alerts: int,
    current_minutes_per_alert: float,
    ai_assisted_minutes_per_alert: float,
    analyst_hourly_cost: float,
    implementation_cost: float,
) -> None:
    """
    Validate business-case assumptions.

    Raises:
        ValueError: if any assumption is invalid.
    """

    if monthly_alerts <= 0:
        raise ValueError(
            "Monthly alert volume must be greater than zero."
        )

    if current_minutes_per_alert <= 0:
        raise ValueError(
            "Current minutes per alert must be greater than zero."
        )

    if ai_assisted_minutes_per_alert <= 0:
        raise ValueError(
            "AI-assisted minutes per alert must be greater than zero."
        )

    if ai_assisted_minutes_per_alert > current_minutes_per_alert:
        raise ValueError(
            "AI-assisted investigation time cannot exceed "
            "current investigation time in this efficiency model."
        )

    if analyst_hourly_cost <= 0:
        raise ValueError(
            "Analyst hourly cost must be greater than zero."
        )

    if implementation_cost <= 0:
        raise ValueError(
            "Implementation cost must be greater than zero."
        )


# ============================================================
# ROI Calculation
# ============================================================

def calculate_roi(
    monthly_alerts: int = DEFAULT_MONTHLY_ALERTS,
    current_minutes_per_alert: float = DEFAULT_CURRENT_MINUTES_PER_ALERT,
    ai_assisted_minutes_per_alert: float = DEFAULT_AI_ASSISTED_MINUTES_PER_ALERT,
    analyst_hourly_cost: float = DEFAULT_ANALYST_HOURLY_COST,
    implementation_cost: float = DEFAULT_IMPLEMENTATION_COST,
) -> ROIResult:
    """
    Calculate the illustrative FinGuard business case.

    Args:
        monthly_alerts:
            Assumed number of alerts investigated per month.

        current_minutes_per_alert:
            Assumed analyst investigation time before FinGuard.

        ai_assisted_minutes_per_alert:
            Assumed analyst investigation time with FinGuard.

        analyst_hourly_cost:
            Assumed fully loaded analyst cost per hour.

        implementation_cost:
            Assumed one-time implementation cost.

    Returns:
        ROIResult containing the calculated business-case metrics.
    """

    validate_assumptions(
        monthly_alerts=monthly_alerts,
        current_minutes_per_alert=current_minutes_per_alert,
        ai_assisted_minutes_per_alert=ai_assisted_minutes_per_alert,
        analyst_hourly_cost=analyst_hourly_cost,
        implementation_cost=implementation_cost,
    )

    # --------------------------------------------------------
    # Monthly investigation effort
    # --------------------------------------------------------

    current_monthly_hours = (
        monthly_alerts
        * current_minutes_per_alert
        / 60
    )

    ai_assisted_monthly_hours = (
        monthly_alerts
        * ai_assisted_minutes_per_alert
        / 60
    )

    monthly_hours_saved = (
        current_monthly_hours
        - ai_assisted_monthly_hours
    )

    # --------------------------------------------------------
    # Labor savings
    # --------------------------------------------------------

    monthly_labor_savings = (
        monthly_hours_saved
        * analyst_hourly_cost
    )

    annual_labor_savings = (
        monthly_labor_savings
        * 12
    )

    # --------------------------------------------------------
    # Net benefit and ROI
    # --------------------------------------------------------

    net_annual_benefit = (
        annual_labor_savings
        - implementation_cost
    )

    roi_percentage = (
        net_annual_benefit
        / implementation_cost
        * 100
    )

    # --------------------------------------------------------
    # Payback period
    # --------------------------------------------------------

    if monthly_labor_savings > 0:
        payback_months = (
            implementation_cost
            / monthly_labor_savings
        )
    else:
        payback_months = float("inf")

    return ROIResult(
        monthly_alerts=monthly_alerts,
        current_minutes_per_alert=current_minutes_per_alert,
        ai_assisted_minutes_per_alert=ai_assisted_minutes_per_alert,
        analyst_hourly_cost=analyst_hourly_cost,
        implementation_cost=implementation_cost,
        current_monthly_hours=round(
            current_monthly_hours,
            2,
        ),
        ai_assisted_monthly_hours=round(
            ai_assisted_monthly_hours,
            2,
        ),
        monthly_hours_saved=round(
            monthly_hours_saved,
            2,
        ),
        monthly_labor_savings=round(
            monthly_labor_savings,
            2,
        ),
        annual_labor_savings=round(
            annual_labor_savings,
            2,
        ),
        net_annual_benefit=round(
            net_annual_benefit,
            2,
        ),
        roi_percentage=round(
            roi_percentage,
            2,
        ),
        payback_months=round(
            payback_months,
            2,
        ),
    )


# ============================================================
# Human-Readable Summary
# ============================================================

def generate_roi_summary(
    result: ROIResult,
) -> str:
    """
    Generate a concise business-case summary suitable for
    documentation or a Streamlit section.
    """

    return (
        f"Assuming {result.monthly_alerts:,} alerts per month, "
        f"average investigation effort decreases from "
        f"{result.current_minutes_per_alert:.0f} minutes to "
        f"{result.ai_assisted_minutes_per_alert:.0f} minutes "
        f"per alert. This represents approximately "
        f"{result.monthly_hours_saved:,.1f} analyst hours saved "
        f"per month and estimated annual labor savings of "
        f"₹{result.annual_labor_savings:,.0f}. "
        f"Against an illustrative implementation cost of "
        f"₹{result.implementation_cost:,.0f}, the calculated "
        f"first-year net benefit is "
        f"₹{result.net_annual_benefit:,.0f}, with an estimated "
        f"payback period of "
        f"{result.payback_months:.1f} months."
    )


# ============================================================
# Default Scenario
# ============================================================

def get_default_roi() -> ROIResult:
    """
    Calculate the default illustrative business case.
    """

    return calculate_roi()


# ============================================================
# Self-Test
# ============================================================

def run_self_test() -> None:
    """
    Basic assertion-based validation of the ROI model.
    """

    result = calculate_roi()

    # Default assumptions:
    # 200 alerts × 90 min = 300 hours/month
    assert result.current_monthly_hours == 300.0

    # 200 alerts × 30 min = 100 hours/month
    assert result.ai_assisted_monthly_hours == 100.0

    # 200 hours saved/month
    assert result.monthly_hours_saved == 200.0

    # 200 × ₹800 = ₹160,000/month
    assert result.monthly_labor_savings == 160000.0

    # ₹160,000 × 12 = ₹1,920,000/year
    assert result.annual_labor_savings == 1920000.0

    # ₹1,920,000 - ₹250,000
    assert result.net_annual_benefit == 1670000.0

    # 1,670,000 / 250,000 × 100
    assert result.roi_percentage == 668.0

    # 250,000 / 160,000
    assert result.payback_months == 1.56

    # Validation checks
    try:
        calculate_roi(
            monthly_alerts=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected validation error for zero monthly alerts."
        )

    try:
        calculate_roi(
            current_minutes_per_alert=30,
            ai_assisted_minutes_per_alert=60,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected validation error when AI-assisted time "
            "exceeds current investigation time."
        )

    print("FinGuard ROI Model Test")
    print("=" * 70)
    print("Monthly alerts:", result.monthly_alerts)
    print(
        "Current effort:",
        f"{result.current_monthly_hours:.2f}",
        "hours/month",
    )
    print(
        "AI-assisted effort:",
        f"{result.ai_assisted_monthly_hours:.2f}",
        "hours/month",
    )
    print(
        "Monthly hours saved:",
        f"{result.monthly_hours_saved:.2f}",
    )
    print(
        "Monthly labor savings:",
        f"₹{result.monthly_labor_savings:,.2f}",
    )
    print(
        "Annual labor savings:",
        f"₹{result.annual_labor_savings:,.2f}",
    )
    print(
        "Net annual benefit:",
        f"₹{result.net_annual_benefit:,.2f}",
    )
    print(
        "ROI:",
        f"{result.roi_percentage:.2f}%",
    )
    print(
        "Payback:",
        f"{result.payback_months:.2f} months",
    )
    print()
    print("ROI MODEL TEST PASSED")


if __name__ == "__main__":
    run_self_test()