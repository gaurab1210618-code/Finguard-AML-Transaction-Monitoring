import sqlite3

from app.audit_db import get_connection


def get_total_cases() -> int:
    """
    Return the total number of persisted audit cases.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total_cases
            FROM audit_records
            """
        ).fetchone()

        return int(row["total_cases"])

    finally:
        connection.close()


def get_decision_distribution() -> list[dict]:
    """
    Return case counts grouped by analyst decision.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                analyst_decision,
                COUNT(*) AS case_count
            FROM audit_records
            GROUP BY analyst_decision
            ORDER BY case_count DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_risk_distribution() -> list[dict]:
    """
    Return case counts grouped by AI risk assessment.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                ai_risk_assessment,
                COUNT(*) AS case_count
            FROM audit_records
            GROUP BY ai_risk_assessment
            ORDER BY case_count DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_ai_human_outcomes() -> list[dict]:
    """
    Compare AI recommendation with final analyst decision.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                ai_recommendation,
                analyst_decision,
                COUNT(*) AS case_count
            FROM audit_records
            GROUP BY
                ai_recommendation,
                analyst_decision
            ORDER BY case_count DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_override_rate() -> float:
    """
    Return the percentage of cases where the analyst
    explicitly selected OVERRIDE.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                CASE
                    WHEN COUNT(*) = 0 THEN 0.0
                    ELSE
                        100.0 *
                        SUM(
                            CASE
                                WHEN analyst_decision = 'OVERRIDE'
                                THEN 1
                                ELSE 0
                            END
                        ) / COUNT(*)
                END AS override_rate
            FROM audit_records
            """
        ).fetchone()

        return float(row["override_rate"])

    finally:
        connection.close()


def get_escalation_rate() -> float:
    """
    Return the percentage of cases escalated by analysts.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                CASE
                    WHEN COUNT(*) = 0 THEN 0.0
                    ELSE
                        100.0 *
                        SUM(
                            CASE
                                WHEN analyst_decision = 'ESCALATE'
                                THEN 1
                                ELSE 0
                            END
                        ) / COUNT(*)
                END AS escalation_rate
            FROM audit_records
            """
        ).fetchone()

        return float(row["escalation_rate"])

    finally:
        connection.close()


def get_provider_distribution() -> list[dict]:
    """
    Return case counts grouped by AI provider.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                ai_provider,
                COUNT(*) AS case_count
            FROM audit_records
            GROUP BY ai_provider
            ORDER BY case_count DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def get_cases_by_date() -> list[dict]:
    """
    Return case counts grouped by recorded date.

    recorded_at is stored as UTC ISO-8601 text.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                DATE(recorded_at) AS case_date,
                COUNT(*) AS case_count
            FROM audit_records
            GROUP BY DATE(recorded_at)
            ORDER BY case_date
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()