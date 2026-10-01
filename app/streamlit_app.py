import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------
# Project path
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------
# FinGuard imports
# ---------------------------------------------------------------------

from app.analytics import (
    get_total_cases,
    get_override_rate,
    get_escalation_rate,
    get_decision_distribution,
    get_risk_distribution,
    get_ai_human_outcomes,
    get_provider_distribution,
    get_cases_by_date,
)

from app.audit_db import (
    get_all_audit_records,
    save_hitl_decision,
)

from app.hitl_decision import (
    create_hitl_decision,
)

from app.investigation_engine import (
    investigate_alert,
)

from app.ai_investigation import (
    generate_ai_investigation,
)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="FinGuard AML Investigation Workspace",
    page_icon="🛡️",
    layout="wide",
)


# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------

DATA_DIR = PROJECT_ROOT / "data"

CUSTOMERS_PATH = DATA_DIR / "customers.csv"
TRANSACTIONS_PATH = DATA_DIR / "transactions.csv"
ALERTS_PATH = DATA_DIR / "alerts.csv"
CASE_HISTORY_PATH = DATA_DIR / "case_history.csv"


@st.cache_data
def load_data():

    customers = pd.read_csv(CUSTOMERS_PATH)
    transactions = pd.read_csv(TRANSACTIONS_PATH)
    alerts = pd.read_csv(ALERTS_PATH)
    case_history = pd.read_csv(CASE_HISTORY_PATH)

    return (
        customers,
        transactions,
        alerts,
        case_history,
    )


customers, transactions, alerts, case_history = load_data()


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title("🛡️ FinGuard")
st.subheader(
    "AI-Assisted AML Transaction Monitoring & "
    "Human-in-the-Loop Investigation System"
)

st.caption(
    "Prototype for analyst-assisted transaction monitoring. "
    "AI provides evidence-based recommendations; the human analyst "
    "retains final decision authority."
)

st.divider()


# ---------------------------------------------------------------------
# KPI layer
# ---------------------------------------------------------------------

st.header("📊 Operations Dashboard")

col1, col2, col3, col4 = st.columns(4)

total_cases = get_total_cases()
override_rate = get_override_rate()
escalation_rate = get_escalation_rate()

decision_distribution = get_decision_distribution()

col1.metric(
    "Audited Cases",
    total_cases,
)

col2.metric(
    "Override Rate",
    f"{override_rate:.1f}%",
)

col3.metric(
    "Escalation Rate",
    f"{escalation_rate:.1f}%",
)

open_alerts = int(
    (alerts["status"] == "OPEN").sum()
)

col4.metric(
    "Open Alerts",
    open_alerts,
)


# ---------------------------------------------------------------------
# KPI charts
# ---------------------------------------------------------------------

kpi_col1, kpi_col2 = st.columns(2)


with kpi_col1:

    st.subheader("Human Decisions")

    decision_df = pd.DataFrame(
        decision_distribution
    )

    if not decision_df.empty:
        decision_df = decision_df.set_index(
            "analyst_decision"
        )

        st.bar_chart(
            decision_df["case_count"]
        )


with kpi_col2:

    st.subheader("AI Risk Distribution")

    risk_distribution = get_risk_distribution()

    risk_df = pd.DataFrame(
        risk_distribution
    )

    if not risk_df.empty:
        risk_df = risk_df.set_index(
            "ai_risk_assessment"
        )

        st.bar_chart(
            risk_df["case_count"]
        )


st.divider()


# ---------------------------------------------------------------------
# Alert queue
# ---------------------------------------------------------------------

st.header("🚨 Investigation Queue")

display_columns = [
    "alert_id",
    "customer_id",
    "alert_type",
    "priority",
    "trigger_rule",
    "status",
]

available_columns = [
    column
    for column in display_columns
    if column in alerts.columns
]

queue_df = alerts[
    available_columns
].copy()

st.dataframe(
    queue_df,
    width='stretch',
    hide_index=True,
)


# ---------------------------------------------------------------------
# Alert selection
# ---------------------------------------------------------------------

st.subheader("🔎 Select Alert")

alert_ids = alerts[
    "alert_id"
].tolist()

selected_alert_id = st.selectbox(
    "Alert ID",
    alert_ids,
)


selected_alert = alerts[
    alerts["alert_id"] == selected_alert_id
].iloc[0]


customer_id = selected_alert[
    "customer_id"
]


# ---------------------------------------------------------------------
# Alert summary
# ---------------------------------------------------------------------

st.divider()

st.header("📌 Alert Overview")

alert_col1, alert_col2, alert_col3, alert_col4 = st.columns(4)

alert_col1.metric(
    "Alert",
    selected_alert_id,
)

alert_col2.metric(
    "Customer",
    customer_id,
)

alert_col3.metric(
    "Priority",
    selected_alert.get(
        "priority",
        "N/A",
    ),
)

alert_col4.metric(
    "Alert Type",
    selected_alert.get(
        "alert_type",
        "N/A",
    ),
)

st.write(
    "**Trigger Rule:**",
    selected_alert.get(
        "trigger_rule",
        "N/A",
    ),
)


# ---------------------------------------------------------------------
# Customer profile
# ---------------------------------------------------------------------

st.header("👤 Customer Profile")

customer_rows = customers[
    customers["customer_id"] == customer_id
]

if not customer_rows.empty:

    customer = customer_rows.iloc[0]

    profile_col1, profile_col2, profile_col3 = st.columns(3)

    profile_col1.write(
        f"**Customer ID:** {customer.get('customer_id', 'N/A')}"
    )

    profile_col2.write(
        f"**Risk Tier:** {customer.get('risk_tier', 'N/A')}"
    )

    profile_col3.write(
        f"**Monthly Avg Volume:** "
        f"{customer.get('monthly_avg_volume', 'N/A')}"
    )

else:

    st.warning(
        "Customer profile not found."
    )


# ---------------------------------------------------------------------
# Investigation
# ---------------------------------------------------------------------

st.header("🧪 Investigation")

run_investigation = st.button(
    "Run Investigation",
    type="primary",
)


if run_investigation:

    with st.spinner(
        "Building investigation evidence package..."
    ):

        try:

            # ---------------------------------------------------------
            # Convert the selected alert into the dictionary structure
            # expected by the existing Investigation Engine.
            # ---------------------------------------------------------

            alert_data = selected_alert.to_dict()

            # ---------------------------------------------------------
            # Get the selected customer's profile.
            # ---------------------------------------------------------

            customer_rows = customers[
                customers["customer_id"] == customer_id
            ]

            if customer_rows.empty:
                raise ValueError(
                    f"Customer {customer_id} was not found."
                )

            customer_data = (
                customer_rows.iloc[0].to_dict()
            )

            # ---------------------------------------------------------
            # Get all transactions belonging to this customer.
            #
            # The Investigation Engine applies the investigation
            # window and contextual rule logic itself.
            # ---------------------------------------------------------

            customer_transactions = transactions[
                transactions["customer_id"] == customer_id
            ]

            transaction_data = (
                customer_transactions
                .to_dict(orient="records")
            )

            # ---------------------------------------------------------
            # Get historical cases belonging to this customer.
            # ---------------------------------------------------------

            customer_case_history = case_history[
                case_history["customer_id"] == customer_id
            ]

            case_history_data = (
                customer_case_history
                .to_dict(orient="records")
            )

            # ---------------------------------------------------------
            # Call the existing Investigation Engine.
            # ---------------------------------------------------------

            evidence_package = investigate_alert(
                alert_data,
                transaction_data,
                customer_data,
                case_history_data,
            )

            # ---------------------------------------------------------
            # Store the result for the rest of the UI.
            # ---------------------------------------------------------

            st.session_state[
                "evidence_package"
            ] = evidence_package

            st.session_state[
                "selected_alert_id"
            ] = selected_alert_id

            st.success(
                "Investigation evidence package generated."
            )

        except Exception as error:

            st.error(
                f"Investigation failed: {error}"
            )


# ---------------------------------------------------------------------
# Display investigation
# ---------------------------------------------------------------------

if (
    "evidence_package" in st.session_state
    and st.session_state.get(
        "selected_alert_id"
    ) == selected_alert_id
):

    evidence_package = st.session_state[
        "evidence_package"
    ]

    st.subheader("Evidence Package")

    # -------------------------------------------------------------
    # Alert evidence
    # -------------------------------------------------------------

    alert_evidence = evidence_package.get(
        "alert_trigger",
        {},
    )

    with st.expander(
        "Alert Trigger",
        expanded=True,
    ):

        st.json(
            alert_evidence
        )

    # -------------------------------------------------------------
    # Investigation context
    # -------------------------------------------------------------

    investigation_context = evidence_package.get(
        "investigation_context",
        {},
    )

    with st.expander(
        "Investigation Context",
        expanded=True,
    ):

        # -------------------------------------------------------------
        # The Investigation Engine returns the transaction count and
        # transaction IDs in the Evidence Package.
        #
        # Retrieve the corresponding transaction records from the
        # already-loaded transactions dataset for UI display.
        # -------------------------------------------------------------

        context_transaction_ids = (
            investigation_context.get(
                "transaction_ids",
                [],
            )
        )

        context_transaction_count = (
            investigation_context.get(
                "transaction_count",
                len(context_transaction_ids),
            )
        )

        st.write(
            f"**Transactions in context:** "
            f"{context_transaction_count}"
        )

        st.write(
            f"**Investigation Window:** "
            f"{investigation_context.get('window_start', 'N/A')} "
            f"→ "
            f"{investigation_context.get('window_end', 'N/A')}"
        )

        if context_transaction_ids:

            context_df = transactions[
                transactions["transaction_id"].isin(
                    context_transaction_ids
                )
            ].copy()

            # Keep the same chronological ordering used by the
            # investigation context where possible.
            if "timestamp" in context_df.columns:

                context_df = context_df.sort_values(
                    "timestamp"
                )

            st.dataframe(
                context_df,
                width='stretch',
                hide_index=True,
            )

        else:

            st.info(
                "No transactions were included in the "
                "investigation context."
            )


    # -------------------------------------------------------------
    # Contextual indicators
    # -------------------------------------------------------------

    contextual_indicators = evidence_package.get(
        "contextual_indicators",
        [],
    )

    with st.expander(
        "Risk Indicators",
        expanded=True,
    ):

        if contextual_indicators:

            for indicator in contextual_indicators:

                triggered = indicator.get(
                    "triggered",
                    False,
                )

                status = (
                    "🔴 TRIGGERED"
                    if triggered
                    else "🟢 NOT TRIGGERED"
                )

                st.markdown(
                    f"### {status} — "
                    f"{indicator.get('rule_id', 'N/A')}"
                )

                st.write(
                    indicator.get(
                        "rule_name",
                        "",
                    )
                )

                st.write(
                    indicator.get(
                        "reason",
                        "",
                    )
                )

        else:

            st.info(
                "No contextual indicators returned."
            )

    # -------------------------------------------------------------
    # Historical context
    # -------------------------------------------------------------

    historical_context = evidence_package.get(
        "historical_signals",
        {},
    )

    with st.expander(
        "Historical Customer Context",
        expanded=True,
    ):

        st.json(
            historical_context
        )


    # -----------------------------------------------------------------
    # AI Investigation
    # -----------------------------------------------------------------

    st.subheader("🤖 AI Investigation")

    run_ai = st.button(
        "Generate AI Investigation",
        type="primary",
    )

    if run_ai:

        # Clear any previous AI result so stale output
        # cannot be reused if the new AI attempt fails.
        st.session_state.pop(
            "ai_result",
            None,
        )

        st.session_state[
            "ai_unavailable"
        ] = False

        with st.spinner(
            "Generating evidence-based AI investigation..."
        ):

            try:

                ai_result = generate_ai_investigation(
                    evidence_package
                )

                st.session_state[
                    "ai_result"
                ] = ai_result

                st.success(
                    "AI investigation generated successfully."
                )

            except RuntimeError as error:

                st.session_state[
                    "ai_unavailable"
                ] = True

                st.warning(
                    "AI investigation is currently unavailable. "
                    "The deterministic investigation evidence remains "
                    "available for analyst review. No AI recommendation "
                    "has been generated."
                )

                st.caption(
                    f"Technical detail: {error}"
                )

            except Exception as error:

                st.session_state[
                    "ai_unavailable"
                ] = True

                st.error(
                    f"AI investigation failed: {error}"
                )


# ---------------------------------------------------------------------
# AI result
# ---------------------------------------------------------------------

if st.session_state.get("ai_unavailable", False):

    st.info(
        "AI assistance is unavailable for this attempt. "
        "Review the evidence package and deterministic risk "
        "indicators above. A human decision should not be submitted "
        "through the AI-assisted workflow until an AI result is available."
    )

if (
    "ai_result" in st.session_state
    and st.session_state.get(
        "selected_alert_id"
    ) == selected_alert_id
):

    ai_result = st.session_state[
        "ai_result"
    ]

    st.subheader(
        "AI-Assisted Investigation Result"
    )

    ai_col1, ai_col2, ai_col3 = st.columns(3)

    ai_col1.metric(
        "AI Provider",
        ai_result.provider or "N/A",
    )

    ai_col2.metric(
        "Risk Assessment",
        ai_result.risk_assessment,
    )

    ai_col3.metric(
        "Recommendation",
        ai_result.recommended_next_step,
    )

    st.markdown("### Investigation Summary")

    st.write(
        ai_result.investigation_summary
    )

    st.markdown("### Key Findings")

    for finding in ai_result.key_findings:

        st.markdown(
            f"**{finding.finding}**"
        )

        st.write(
            finding.significance
        )

        if finding.evidence_references:

            references = [
                (
                    f"{reference.reference_type}: "
                    f"{reference.reference_id}"
                )
                for reference
                in finding.evidence_references
            ]

            st.caption(
                "Evidence: "
                + ", ".join(references)
            )

    st.markdown("### Rationale")

    st.write(
        ai_result.rationale
    )

    if ai_result.evidence_gaps:

        st.markdown(
            "### Evidence Gaps"
        )

        for gap in ai_result.evidence_gaps:

            st.write(
                f"- {gap}"
            )

    st.warning(
        ai_result.analyst_warning
    )


    # -----------------------------------------------------------------
    # Human-in-the-loop decision
    # -----------------------------------------------------------------

    st.divider()

    st.header(
        "👨‍💼 Human Analyst Decision"
    )

    st.info(
        "The AI recommendation is advisory only. "
        "The final case disposition must be made by the analyst."
    )

    analyst_decision = st.radio(
        "Select final decision",
        [
            "CLOSE",
            "OVERRIDE",
            "ESCALATE",
        ],
        horizontal=True,
    )

    analyst_reason = st.text_area(
        "Analyst reasoning",
        placeholder=(
            "Document why the final decision was selected..."
        ),
    )

    submit_decision = st.button(
        "Submit Analyst Decision",
        type="primary",
    )

    if submit_decision:

        if not analyst_reason.strip():

            st.error(
                "Analyst reasoning is required."
            )

        else:

            try:

                decision = create_hitl_decision(
                    alert_id=selected_alert_id,
                    customer_id=customer_id,
                    ai_provider=ai_result.provider,
                    ai_recommendation=(
                        ai_result.recommended_next_step
                    ),
                    ai_risk_assessment=(
                        ai_result.risk_assessment
                    ),
                    analyst_decision=analyst_decision,
                    analyst_reason=analyst_reason,
                )

                case_id = save_hitl_decision(
                    decision
                )

                # Store the case ID so it can be shown after
                # the automatic Streamlit rerun.
                st.session_state[
                    "last_case_id"
                ] = case_id

                # Re-run the complete application so the KPI
                # dashboard and audit trail immediately reflect
                # the newly persisted decision.
                st.rerun()

            except Exception as error:

                st.error(
                    f"Could not save analyst decision: {error}"
                )


# ---------------------------------------------------------------------
# Audit history
# ---------------------------------------------------------------------

st.divider()

st.header("📜 Audit Trail")

audit_records = get_all_audit_records()

# Show the save confirmation after the automatic rerun.
if "last_case_id" in st.session_state:

    st.success(
        f"Decision saved successfully. "
        f"Case ID: {st.session_state['last_case_id']}"
    )

    # Prevent the success message from appearing again on
    # unrelated future Streamlit reruns.
    del st.session_state["last_case_id"]

if audit_records:

    audit_df = pd.DataFrame(
        audit_records
    )

    st.dataframe(
        audit_df,
        width='stretch',
        hide_index=True,
    )

else:

    st.info(
        "No audit records available."
    )


# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------

st.divider()

st.caption(
    "FinGuard is a synthetic-data prototype. "
    "It is designed to demonstrate AI-assisted AML investigation "
    "workflow, human oversight, evidence traceability, and "
    "operational analytics. It is not a production AML compliance system."
)