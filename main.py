from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import init_db, save_submission
from geo import get_geo_data


# -------------------------
# Rate Limiter
# -------------------------

limiter = Limiter(key_func=get_remote_address)


# -------------------------
# FastAPI App
# -------------------------

app = FastAPI(
    title="Embeddable Widget & Lead-Capture Platform",
    version="1.0.0"
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


# -------------------------
# CORS
# -------------------------

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


# -------------------------
# Database Startup
# -------------------------

@app.on_event("startup")
def startup_event():
    init_db()


# -------------------------
# Request Model
# -------------------------

class SubmissionCreate(BaseModel):

    widget_id: int

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

    # Honeypot field
    website: str = ""


# -------------------------
# Health Routes
# -------------------------

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


# -------------------------
# Public Submission Route
# -------------------------

@app.post("/submissions", status_code=201)
@limiter.limit("5/minute")
def create_submission(
    request: Request,
    submission: SubmissionCreate
):

    # -------------------------
    # Honeypot Spam Protection
    # -------------------------

    if submission.website:

        raise HTTPException(
            status_code=400,
            detail="Spam submission rejected"
        )


    # -------------------------
    # Get Visitor IP
    # -------------------------

    ip_address = (
        request.client.host
        if request.client
        else None
    )


    # -------------------------
    # Geo Enrichment
    # -------------------------

    geo_data = {
        "country": None,
        "city": None,
        "provider": None
    }

    if ip_address:

        geo_data = get_geo_data(
            ip_address
        )


    # -------------------------
    # Save Submission
    # -------------------------

    submission_id = save_submission(

        widget_id=submission.widget_id,

        name=submission.name,

        email=submission.email,

        message=submission.message,

        ip_address=ip_address,

        country=geo_data.get("country"),

        city=geo_data.get("city")
    )


    # -------------------------
    # Response
    # -------------------------

    return {

        "message":
            "Submission stored successfully",

        "submission_id":
            submission_id,

        "geo": {
            "country":
                geo_data.get("country"),

            "city":
                geo_data.get("city"),

            "provider":
                geo_data.get("provider")
        }
    }