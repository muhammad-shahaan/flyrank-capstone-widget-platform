from database import get_connection


def create_widget(
    tenant_id: int,
    widget_type: str,
    title: str,
    description: str,
    button_text: str
):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO widgets
        (
            tenant_id,
            type,
            title,
            description,
            button_text
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            tenant_id,
            widget_type,
            title,
            description,
            button_text
        )
    )

    connection.commit()
    widget_id = cursor.lastrowid
    connection.close()

    return widget_id


def get_widgets(tenant_id: int):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM widgets
        WHERE tenant_id = ?
        ORDER BY created_at DESC
        """,
        (tenant_id,)
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_widget(widget_id: int, tenant_id: int):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM widgets
        WHERE id = ?
        AND tenant_id = ?
        """,
        (
            widget_id,
            tenant_id
        )
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def update_widget(
    widget_id: int,
    tenant_id: int,
    widget_type: str,
    title: str,
    description: str,
    button_text: str
):
    connection = get_connection()

    cursor = connection.execute(
        """
        UPDATE widgets
        SET
            type = ?,
            title = ?,
            description = ?,
            button_text = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        AND tenant_id = ?
        """,
        (
            widget_type,
            title,
            description,
            button_text,
            widget_id,
            tenant_id
        )
    )

    connection.commit()
    updated = cursor.rowcount > 0
    connection.close()

    return updated


def delete_widget(widget_id: int, tenant_id: int):
    connection = get_connection()

    cursor = connection.execute(
        """
        DELETE FROM widgets
        WHERE id = ?
        AND tenant_id = ?
        """,
        (
            widget_id,
            tenant_id
        )
    )

    connection.commit()
    deleted = cursor.rowcount > 0
    connection.close()

    return deleted


def get_public_widget(widget_id: int):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            type,
            title,
            description,
            button_text
        FROM widgets
        WHERE id = ?
        """,
        (widget_id,)
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)