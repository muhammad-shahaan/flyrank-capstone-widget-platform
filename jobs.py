
from datetime import datetime, timedelta, timezone

from database import get_connection


# =========================================================
# JOB SETTINGS
# =========================================================

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 30


# =========================================================
# CREATE JOBS TABLE
# =========================================================

def init_jobs():

    connection = get_connection()

    try:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                tenant_id INTEGER NOT NULL,
                job_type TEXT NOT NULL DEFAULT 'lead_notification',
                status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL DEFAULT 3,
                next_run_at TEXT NOT NULL,
                last_error TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,

                FOREIGN KEY (submission_id)
                    REFERENCES submissions(id),

                FOREIGN KEY (tenant_id)
                    REFERENCES tenants(id)
            )
            """
        )

        # -------------------------------------------------
        # Job Processing Index
        # -------------------------------------------------

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_jobs_status_next_run
            ON jobs(status, next_run_at)
            """
        )

        # -------------------------------------------------
        # Idempotency Protection
        # -------------------------------------------------
        # Prevent multiple notification jobs from being
        # created for the same submission.
        #
        # Existing duplicate jobs must be resolved before
        # creating this unique index.
        # -------------------------------------------------

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_jobs_unique_submission_notification
            ON jobs(submission_id, job_type)
            """
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# UTC TIME
# =========================================================

def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# CREATE BACKGROUND JOB
# =========================================================

def create_job(
    submission_id: int,
    tenant_id: int
):

    connection = get_connection()

    try:

        now = utc_now()

        cursor = connection.execute(
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
                MAX_ATTEMPTS,
                now,
                now
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
# PROCESS ONE JOB
# =========================================================

def process_job(
    job_id: int,
    force_failure: bool = False
):

    connection = get_connection()

    try:

        now = utc_now()

        # Claim only a due, pending or retryable job.

        cursor = connection.execute(
            """
            UPDATE jobs
            SET
                status = 'processing',
                attempts = attempts + 1
            WHERE id = ?
              AND status IN ('pending', 'retry')
              AND next_run_at <= ?
              AND attempts < max_attempts
            """,
            (job_id, now)
        )

        if cursor.rowcount == 0:

            connection.rollback()

            return {
                "job_id": job_id,
                "message": "Job not found or not ready"
            }

        job = connection.execute(
            """
            SELECT *
            FROM jobs
            WHERE id = ?
            """,
            (job_id,)
        ).fetchone()

        connection.commit()

        try:

            # Simulated notification side effect.
            # Replace with a real notification provider later.

            if force_failure:

                raise RuntimeError(
                    "Forced notification failure"
                )

            print(
                f"Notification processed for submission "
                f"{job['submission_id']}"
            )

            connection.execute(
                """
                UPDATE jobs
                SET
                    status = 'completed',
                    completed_at = ?,
                    last_error = NULL
                WHERE id = ?
                  AND status = 'processing'
                """,
                (utc_now(), job_id)
            )

            connection.commit()

            return {
                "job_id": job_id,
                "status": "completed",
                "attempts": job["attempts"]
            }

        except Exception as error:

            attempts = job["attempts"]
            max_attempts = job["max_attempts"]

            if attempts >= max_attempts:

                status = "failed"

            else:

                status = "retry"

            next_run_at = (
                datetime.now(timezone.utc)
                + timedelta(seconds=RETRY_DELAY_SECONDS)
            ).isoformat()

            connection.execute(
                """
                UPDATE jobs
                SET
                    status = ?,
                    next_run_at = ?,
                    last_error = ?
                WHERE id = ?
                  AND status = 'processing'
                """,
                (
                    status,
                    next_run_at,
                    str(error),
                    job_id
                )
            )

            connection.commit()

            return {
                "job_id": job_id,
                "status": status,
                "attempts": attempts,
                "error": str(error)
            }

    finally:

        connection.close()


# =========================================================
# PROCESS DUE JOBS
# =========================================================

def process_due_jobs(
    limit: int = 10,
    force_failure: bool = False
):

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT id
            FROM jobs
            WHERE status IN ('pending', 'retry')
              AND next_run_at <= ?
              AND attempts < max_attempts
            ORDER BY next_run_at, id
            LIMIT ?
            """,
            (
                utc_now(),
                limit
            )
        ).fetchall()

        job_ids = [
            row["id"]
            for row in rows
        ]

    finally:

        connection.close()

    results = []

    for job_id in job_ids:

        result = process_job(
            job_id=job_id,
            force_failure=force_failure
        )

        results.append(result)

    return results


# =========================================================
# GET JOB STATUS
# =========================================================

def get_job_status(
    job_id: int,
    tenant_id: int
):

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                submission_id,
                tenant_id,
                job_type,
                status,
                attempts,
                max_attempts,
                next_run_at,
                last_error,
                created_at,
                completed_at
            FROM jobs
            WHERE id = ?
              AND tenant_id = ?
            """,
            (
                job_id,
                tenant_id
            )
        ).fetchone()

        if row is None:

            return None

        return dict(row)

    finally:

        connection.close()