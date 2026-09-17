import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).parent / "capstone.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    # Enable SQLite foreign keys
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_db():
    connection = get_connection()

    # -------------------------
    # Tenants Table
    # -------------------------

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

    # -------------------------
    # Widgets Table
    # -------------------------

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

    # Useful tenant lookup index
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_widgets_tenant_id
        ON widgets(tenant_id)
        """
    )

    # -------------------------
    # Submissions Table
    # -------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            widget_id INTEGER NOT NULL,
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

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_submissions_widget_id
        ON submissions(widget_id)
        """
    )

    # -------------------------
    # Demo Tenants
    # -------------------------

    connection.execute(
        """
        INSERT OR IGNORE INTO tenants
        (id, name, api_key)
        VALUES
        (1, 'Demo Tenant A', 'tenant-a-key')
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO tenants
        (id, name, api_key)
        VALUES
        (2, 'Demo Tenant B', 'tenant-b-key')
        """
    )

    connection.commit()
    connection.close()


def save_submission(
    widget_id: int,
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
            name,
            email,
            message,
            ip_address,
            country,
            city
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            widget_id,
            name,
            email,
            message,
            ip_address,
            country,
            city,
        ),
    )

    connection.commit()

    submission_id = cursor.lastrowid
    connection.close()

    return submission_id