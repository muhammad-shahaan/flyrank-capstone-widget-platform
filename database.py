
import sqlite3
from pathlib import Path


# =========================================================
# DATABASE PATH
# =========================================================

DATABASE_PATH = Path(__file__).parent / "capstone.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # Enable SQLite foreign key enforcement
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():
    connection = get_connection()

    try:
        # -------------------------------------------------
        # Tenants Table
        # -------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                api_key TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # -------------------------------------------------
        # Widgets Table
        # -------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS widgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                button_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (tenant_id)
                    REFERENCES tenants(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_widgets_tenant_id
            ON widgets(tenant_id)
            """
        )

        # -------------------------------------------------
        # Submissions Table
        # -------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                widget_id INTEGER NOT NULL,
                tenant_id INTEGER,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                ip_address TEXT,
                country TEXT,
                city TEXT,
                idempotency_key TEXT,
                request_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # -------------------------------------------------
        # Existing Database Migration
        # -------------------------------------------------

        columns = connection.execute(
            """
            PRAGMA table_info(submissions)
            """
        ).fetchall()

        column_names = [
            column["name"]
            for column in columns
        ]

        if "tenant_id" not in column_names:
            connection.execute(
                """
                ALTER TABLE submissions
                ADD COLUMN tenant_id INTEGER
                """
            )

        if "idempotency_key" not in column_names:
            connection.execute(
                """
                ALTER TABLE submissions
                ADD COLUMN idempotency_key TEXT
                """
            )

        if "request_hash" not in column_names:
            connection.execute(
                """
                ALTER TABLE submissions
                ADD COLUMN request_hash TEXT
                """
            )

        # -------------------------------------------------
        # Backfill Old Submissions
        # -------------------------------------------------

        connection.execute(
            """
            UPDATE submissions
            SET tenant_id = (
                SELECT widgets.tenant_id
                FROM widgets
                WHERE widgets.id = submissions.widget_id
            )
            WHERE tenant_id IS NULL
            """
        )

        # -------------------------------------------------
        # Submission Indexes
        # -------------------------------------------------

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_submissions_widget_id
            ON submissions(widget_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_submissions_tenant_id
            ON submissions(tenant_id)
            """
        )

        # Unique idempotency key per tenant.
        # Existing NULL keys remain allowed.

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_submissions_tenant_idempotency
            ON submissions(
                tenant_id,
                idempotency_key
            )
            WHERE idempotency_key IS NOT NULL
            """
        )

        # -------------------------------------------------
        # Demo Tenant A
        # -------------------------------------------------

        connection.execute(
            """
            INSERT OR IGNORE INTO tenants
            (
                id,
                name,
                api_key
            )
            VALUES
            (
                1,
                'Demo Tenant A',
                'tenant-a-key'
            )
            """
        )

        # -------------------------------------------------
        # Demo Tenant B
        # -------------------------------------------------

        connection.execute(
            """
            INSERT OR IGNORE INTO tenants
            (
                id,
                name,
                api_key
            )
            VALUES
            (
                2,
                'Demo Tenant B',
                'tenant-b-key'
            )
            """
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# GET WIDGET FOR PUBLIC SUBMISSION
# =========================================================

def get_submission_widget(widget_id: int):

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                tenant_id
            FROM widgets
            WHERE id = ?
            """,
            (widget_id,)
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


# =========================================================
# GET EXISTING IDEMPOTENT SUBMISSION
# =========================================================

def get_idempotent_submission(
    tenant_id: int,
    idempotency_key: str
):

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                widget_id,
                tenant_id,
                idempotency_key,
                request_hash
            FROM submissions
            WHERE tenant_id = ?
              AND idempotency_key = ?
            """,
            (
                tenant_id,
                idempotency_key
            )
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


# =========================================================
# SAVE SUBMISSION
# =========================================================

def save_submission(
    widget_id: int,
    tenant_id: int,
    name: str,
    email: str,
    message: str,
    ip_address: str | None = None,
    country: str | None = None,
    city: str | None = None,
    idempotency_key: str | None = None,
    request_hash: str | None = None,
):

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO submissions
            (
                widget_id,
                tenant_id,
                name,
                email,
                message,
                ip_address,
                country,
                city,
                idempotency_key,
                request_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                widget_id,
                tenant_id,
                name,
                email,
                message,
                ip_address,
                country,
                city,
                idempotency_key,
                request_hash
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
        
# =========================================================
# ATOMIC IDEMPOTENT SUBMISSION + JOB CREATION
# =========================================================

import hashlib
import json
from datetime import datetime, timezone


def create_idempotent_submission(
    widget_id: int,
    tenant_id: int,
    name: str,
    email: str,
    message: str,
    idempotency_key: str | None = None,
    ip_address: str | None = None,
    country: str | None = None,
    city: str | None = None,
):
    # Hash the request payload to detect key reuse
    # with different submission content.
    payload = {
        "widget_id": widget_id,
        "name": name,
        "email": email,
        "message": message,
    }

    request_hash = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()

    connection = get_connection()

    try:
        # Lock before checking the key so concurrent
        # requests cannot both create a submission.
        connection.execute("BEGIN IMMEDIATE")

        if idempotency_key is not None:

            existing = connection.execute(
                """
                SELECT id, request_hash
                FROM submissions
                WHERE tenant_id = ?
                  AND idempotency_key = ?
                """,
                (
                    tenant_id,
                    idempotency_key
                )
            ).fetchone()

            if existing is not None:

                if existing["request_hash"] != request_hash:
                    connection.rollback()

                    return {
                        "conflict": True,
                        "message": (
                            "Idempotency key was already "
                            "used with different content"
                        )
                    }

                job = connection.execute(
                    """
                    SELECT id, status
                    FROM jobs
                    WHERE submission_id = ?
                      AND job_type = 'lead_notification'
                    """,
                    (existing["id"],)
                ).fetchone()

                connection.commit()

                return {
                    "conflict": False,
                    "duplicate": True,
                    "submission_id": existing["id"],
                    "job_id": job["id"] if job else None,
                    "job_status": (
                        job["status"] if job else None
                    )
                }

        # Verify the widget belongs to the tenant.
        widget = connection.execute(
            """
            SELECT id
            FROM widgets
            WHERE id = ?
              AND tenant_id = ?
            """,
            (
                widget_id,
                tenant_id
            )
        ).fetchone()

        if widget is None:
            connection.rollback()

            return {
                "conflict": True,
                "message": "Widget not found for tenant"
            }

        # Save submission.
        cursor = connection.execute(
            """
            INSERT INTO submissions (
                widget_id,
                tenant_id,
                name,
                email,
                message,
                ip_address,
                country,
                city,
                idempotency_key,
                request_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                widget_id,
                tenant_id,
                name,
                email,
                message,
                ip_address,
                country,
                city,
                idempotency_key,
                request_hash
            )
        )

        submission_id = cursor.lastrowid

        # Create notification job in the SAME transaction.
        now = datetime.now(timezone.utc).isoformat()

        job_cursor = connection.execute(
            """
            INSERT INTO jobs (
                submission_id,
                tenant_id,
                job_type,
                status,
                attempts,
                max_attempts,
                next_run_at,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission_id,
                tenant_id,
                "lead_notification",
                "pending",
                0,
                3,
                now,
                now
            )
        )

        job_id = job_cursor.lastrowid

        # Commit submission and job together.
        connection.commit()

        return {
            "conflict": False,
            "duplicate": False,
            "submission_id": submission_id,
            "job_id": job_id,
            "job_status": "pending"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()