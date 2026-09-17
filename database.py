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

    # -----------------------------------------------------
    # Tenants Table
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Widgets Table
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Submissions Table
    # -----------------------------------------------------

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # =====================================================
    # SIMPLE MIGRATION
    # Add tenant_id to an existing submissions table
    # =====================================================

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


    # -----------------------------------------------------
    # Backfill Old Submissions
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Submission Indexes
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Demo Tenant A
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # Demo Tenant B
    # -----------------------------------------------------

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
    connection.close()


# =========================================================
# GET WIDGET FOR PUBLIC SUBMISSION
# =========================================================

def get_submission_widget(widget_id: int):

    connection = get_connection()

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

    connection.close()

    if row is None:
        return None

    return dict(row)


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
):

    connection = get_connection()

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
            city
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            widget_id,
            tenant_id,
            name,
            email,
            message,
            ip_address,
            country,
            city
        )
    )

    connection.commit()

    submission_id = cursor.lastrowid

    connection.close()

    return submission_id