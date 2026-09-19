
from database import get_connection


# ==========================================
# GET TENANT DASHBOARD STATISTICS
# ==========================================

def get_dashboard_stats(tenant_id: int):

    connection = get_connection()

    try:
        # Total widgets belonging to this tenant
        widget_count = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM widgets
            WHERE tenant_id = ?
            """,
            (tenant_id,)
        ).fetchone()["total"]

        # Total submissions belonging to this tenant
        submission_count = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM submissions
            WHERE tenant_id = ?
            """,
            (tenant_id,)
        ).fetchone()["total"]

        # Submissions grouped by widget
        rows = connection.execute(
            """
            SELECT
                w.id AS widget_id,
                w.title AS widget_title,
                COUNT(s.id) AS total_submissions

            FROM widgets AS w

            LEFT JOIN submissions AS s
                ON s.widget_id = w.id
                AND s.tenant_id = w.tenant_id

            WHERE w.tenant_id = ?

            GROUP BY w.id, w.title

            ORDER BY w.id
            """,
            (tenant_id,)
        ).fetchall()

        return {
            "tenant_id": tenant_id,
            "total_widgets": widget_count,
            "total_submissions": submission_count,
            "widgets": [
                dict(row) for row in rows
            ]
        }

    finally:
        connection.close()


# ==========================================
# GET TENANT SUBMISSIONS
# ==========================================

def get_tenant_submissions(
    tenant_id: int,
    limit: int = 50,
    offset: int = 0
):

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                s.id,
                s.widget_id,
                w.title AS widget_title,
                s.name,
                s.email,
                s.message,
                s.ip_address,
                s.country,
                s.city,
                s.created_at

            FROM submissions AS s

            INNER JOIN widgets AS w
                ON w.id = s.widget_id
                AND w.tenant_id = s.tenant_id

            WHERE s.tenant_id = ?

            ORDER BY s.created_at DESC, s.id DESC

            LIMIT ? OFFSET ?
            """,
            (
                tenant_id,
                limit,
                offset
            )
        ).fetchall()

        return [
            dict(row) for row in rows
        ]

    finally:
        connection.close()


# ==========================================
# GET SUBMISSIONS FOR ONE WIDGET
# ==========================================

def get_widget_submissions(
    widget_id: int,
    tenant_id: int
):

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                s.id,
                s.widget_id,
                s.name,
                s.email,
                s.message,
                s.ip_address,
                s.country,
                s.city,
                s.created_at

            FROM submissions AS s

            INNER JOIN widgets AS w
                ON w.id = s.widget_id
                AND w.tenant_id = s.tenant_id

            WHERE s.widget_id = ?
                AND s.tenant_id = ?

            ORDER BY s.created_at DESC, s.id DESC
            """,
            (
                widget_id,
                tenant_id
            )
        ).fetchall()

        return [
            dict(row) for row in rows
        ]

    finally:
        connection.close()