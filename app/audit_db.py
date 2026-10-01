import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.hitl_decision import HITLDecision


# ---------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "finguard_audit.db"
)


# ---------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------

def get_connection():
    """
    Create a connection to the FinGuard SQLite audit database.
    """

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------

def initialize_database():
    """
    Create the audit table if it does not already exist.
    """

    connection = get_connection()

    try:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_records (

                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,

                case_id TEXT NOT NULL UNIQUE,

                alert_id TEXT NOT NULL,

                customer_id TEXT NOT NULL,

                ai_provider TEXT NOT NULL,

                ai_risk_assessment TEXT NOT NULL,

                ai_recommendation TEXT NOT NULL,

                analyst_decision TEXT NOT NULL,

                analyst_reason TEXT NOT NULL,

                decided_at TEXT NOT NULL,

                recorded_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:

        connection.close()


# ---------------------------------------------------------------------
# Generate case ID
# ---------------------------------------------------------------------

def generate_case_id(
    connection,
):
    """
    Generate the next sequential FinGuard case ID.
    """

    row = connection.execute(
        """
        SELECT MAX(audit_id)
        FROM audit_records
        """
    ).fetchone()

    last_audit_id = row[0]

    next_id = (
        1
        if last_audit_id is None
        else last_audit_id + 1
    )

    return f"CASE-{next_id:06d}"


# ---------------------------------------------------------------------
# Save HITL decision
# ---------------------------------------------------------------------

def save_hitl_decision(
    decision: HITLDecision,
):
    """
    Persist a validated HITL decision into the audit database.

    Returns:
        str: Generated FinGuard case ID.
    """

    initialize_database()

    connection = get_connection()

    try:

        case_id = generate_case_id(
            connection
        )

        recorded_at = datetime.now(
            timezone.utc
        ).isoformat(
            timespec="seconds"
        )

        connection.execute(
            """
            INSERT INTO audit_records (
                case_id,
                alert_id,
                customer_id,
                ai_provider,
                ai_risk_assessment,
                ai_recommendation,
                analyst_decision,
                analyst_reason,
                decided_at,
                recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                decision.alert_id,
                decision.customer_id,
                decision.ai_provider,
                decision.ai_risk_assessment,
                decision.ai_recommendation,
                decision.analyst_decision,
                decision.analyst_reason,
                decision.decided_at,
                recorded_at,
            ),
        )

        connection.commit()

        return case_id

    finally:

        connection.close()


# ---------------------------------------------------------------------
# Retrieve one audit record
# ---------------------------------------------------------------------

def get_audit_record(
    case_id: str,
):
    """
    Retrieve one audit record by FinGuard case ID.

    Returns:
        dict | None
    """

    initialize_database()

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                audit_id,
                case_id,
                alert_id,
                customer_id,
                ai_provider,
                ai_risk_assessment,
                ai_recommendation,
                analyst_decision,
                analyst_reason,
                decided_at,
                recorded_at
            FROM audit_records
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:

        connection.close()


# ---------------------------------------------------------------------
# Retrieve all audit records
# ---------------------------------------------------------------------

def get_all_audit_records():
    """
    Retrieve all persisted audit records.

    Returns:
        list[dict]
    """

    initialize_database()

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                audit_id,
                case_id,
                alert_id,
                customer_id,
                ai_provider,
                ai_risk_assessment,
                ai_recommendation,
                analyst_decision,
                analyst_reason,
                decided_at,
                recorded_at
            FROM audit_records
            ORDER BY audit_id
            """
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        connection.close()