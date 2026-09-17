import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).parent / "capstone.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()

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