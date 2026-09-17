from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import (
    init_db,
    save_submission,
    get_connection,
    get_submission_widget
)

from geo import get_geo_data

from widgets import (
    create_widget,
    get_widgets,
    get_widget,
    update_widget,
    delete_widget,
    get_public_widget
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# RATE LIMITER
# =========================================================

limiter = Limiter(key_func=get_remote_address)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Embeddable Widget & Lead-Capture Platform",
    version="1.0.0"
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():
    init_db()


# =========================================================
# PYDANTIC MODELS
# =========================================================

class SubmissionCreate(BaseModel):
    widget_id: int = Field(gt=0)

    name: str = Field(
        min_length=1,
        max_length=100
    )

    email: str = Field(
        min_length=3,
        max_length=254
    )

    message: str = Field(
        min_length=1,
        max_length=1000
    )

    # Honeypot spam field
    website: str = ""


class WidgetCreate(BaseModel):
    type: str = Field(
        min_length=1,
        max_length=50
    )

    title: str = Field(
        min_length=1,
        max_length=100
    )

    description: str = Field(
        min_length=1,
        max_length=500
    )

    button_text: str = Field(
        min_length=1,
        max_length=50
    )


class WidgetUpdate(BaseModel):
    type: str = Field(
        min_length=1,
        max_length=50
    )

    title: str = Field(
        min_length=1,
        max_length=100
    )

    description: str = Field(
        min_length=1,
        max_length=500
    )

    button_text: str = Field(
        min_length=1,
        max_length=50
    )


# =========================================================
# TENANT AUTHENTICATION
# =========================================================

def get_tenant_id(api_key: str):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT id
        FROM tenants
        WHERE api_key = ?
        """,
        (api_key,)
    ).fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return row["id"]


# =========================================================
# BASIC ROUTES
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Widget Platform API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# AUTHENTICATED WIDGET OWNER API
# =========================================================

@app.post("/widgets", status_code=201)
def create_widget_endpoint(
    widget: WidgetCreate,
    request: Request,
    x_api_key: str = Header(...)
):
    tenant_id = get_tenant_id(x_api_key)

    widget_id = create_widget(
        tenant_id=tenant_id,
        widget_type=widget.type,
        title=widget.title,
        description=widget.description,
        button_text=widget.button_text
    )

    api_base = str(request.base_url).rstrip("/")

    embed_snippet = (
        f'<script src="{api_base}/widget.js?v=1" '
        f'data-widget-id="{widget_id}"></script>'
    )

    return {
        "message": "Widget created successfully",
        "widget_id": widget_id,
        "embed_snippet": embed_snippet
    }


@app.get("/widgets")
def list_widgets_endpoint(
    x_api_key: str = Header(...)
):
    tenant_id = get_tenant_id(x_api_key)

    widgets = get_widgets(
        tenant_id=tenant_id
    )

    return {
        "widgets": widgets
    }


@app.get("/widgets/{widget_id}")
def get_widget_endpoint(
    widget_id: int,
    x_api_key: str = Header(...)
):
    tenant_id = get_tenant_id(x_api_key)

    widget = get_widget(
        widget_id=widget_id,
        tenant_id=tenant_id
    )

    if widget is None:
        raise HTTPException(
            status_code=404,
            detail="Widget not found"
        )

    return widget


@app.put("/widgets/{widget_id}")
def update_widget_endpoint(
    widget_id: int,
    widget: WidgetUpdate,
    x_api_key: str = Header(...)
):
    tenant_id = get_tenant_id(x_api_key)

    updated = update_widget(
        widget_id=widget_id,
        tenant_id=tenant_id,
        widget_type=widget.type,
        title=widget.title,
        description=widget.description,
        button_text=widget.button_text
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Widget not found"
        )

    return {
        "message": "Widget updated successfully"
    }


@app.delete("/widgets/{widget_id}")
def delete_widget_endpoint(
    widget_id: int,
    x_api_key: str = Header(...)
):
    tenant_id = get_tenant_id(x_api_key)

    deleted = delete_widget(
        widget_id=widget_id,
        tenant_id=tenant_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Widget not found"
        )

    return {
        "message": "Widget deleted successfully"
    }


# =========================================================
# AUTHENTICATED EMBED SNIPPET
# =========================================================

@app.get("/widgets/{widget_id}/snippet")
def get_widget_snippet(
    widget_id: int,
    request: Request,
    x_api_key: str = Header(...)
):
    tenant_id = get_tenant_id(x_api_key)

    widget = get_widget(
        widget_id=widget_id,
        tenant_id=tenant_id
    )

    if widget is None:
        raise HTTPException(
            status_code=404,
            detail="Widget not found"
        )

    api_base = str(request.base_url).rstrip("/")

    snippet = (
        f'<script src="{api_base}/widget.js?v=1" '
        f'data-widget-id="{widget_id}"></script>'
    )

    return {
        "widget_id": widget_id,
        "snippet": snippet
    }


# =========================================================
# EMBEDDABLE WIDGET SCRIPT
# =========================================================

@app.get("/widget.js", include_in_schema=False)
def widget_script():
    widget_file = (
        Path(__file__).parent / "widget.js"
    )

    if not widget_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Widget script not found"
        )

    return FileResponse(
        path=widget_file,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600"
        }
    )


# =========================================================
# PUBLIC WIDGET CONFIG
# =========================================================

@app.get("/widgets/{widget_id}/config")
def public_widget_config(
    widget_id: int,
    response: Response
):
    widget = get_public_widget(widget_id)

    if widget is None:
        raise HTTPException(
            status_code=404,
            detail="Widget not found"
        )

    response.headers[
        "Cache-Control"
    ] = "public, max-age=60"

    return {
        "widget": widget
    }


# =========================================================
# PUBLIC SUBMISSION API
# =========================================================

@app.post("/submissions", status_code=201)
@limiter.limit("5/minute")
def create_submission(
    request: Request,
    submission: SubmissionCreate
):

    # -----------------------------------------------------
    # Honeypot Spam Protection
    # -----------------------------------------------------

    if submission.website:
        raise HTTPException(
            status_code=400,
            detail="Spam submission rejected"
        )


    # -----------------------------------------------------
    # Verify Widget Exists
    # -----------------------------------------------------

    submission_widget = get_submission_widget(
        submission.widget_id
    )

    if submission_widget is None:
        raise HTTPException(
            status_code=404,
            detail="Widget not found"
        )


    # -----------------------------------------------------
    # Tenant Comes From Widget
    # Never trust tenant information from public visitor
    # -----------------------------------------------------

    tenant_id = submission_widget["tenant_id"]


    # -----------------------------------------------------
    # Visitor IP
    # -----------------------------------------------------

    ip_address = (
        request.client.host
        if request.client
        else None
    )


    # -----------------------------------------------------
    # Default Geo Data
    # -----------------------------------------------------

    geo_data = {
        "country": None,
        "city": None,
        "provider": None
    }


    # -----------------------------------------------------
    # Geo Enrichment
    # -----------------------------------------------------

    if ip_address:
        geo_data = get_geo_data(
            ip_address
        )


    # -----------------------------------------------------
    # Save Valid Submission
    # -----------------------------------------------------

    submission_id = save_submission(
        widget_id=submission.widget_id,
        tenant_id=tenant_id,
        name=submission.name,
        email=submission.email,
        message=submission.message,
        ip_address=ip_address,
        country=geo_data.get("country"),
        city=geo_data.get("city")
    )


    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return {
        "message": "Submission stored successfully",
        "submission_id": submission_id,
        "geo": {
            "country": geo_data.get("country"),
            "city": geo_data.get("city"),
            "provider": geo_data.get("provider")
        }
    }