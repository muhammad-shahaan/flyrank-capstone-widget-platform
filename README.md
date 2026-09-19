
# FlyRank Capstone Widget Platform

A multi-tenant embeddable widget and lead-capture platform built using Python and FastAPI.

The platform allows tenants to create customizable widgets, embed them into websites, collect customer submissions, and manage leads through authenticated API endpoints.

It includes spam protection, rate limiting, geo enrichment, idempotent submissions, and background notification jobs.

## 1. Project Overview

The FlyRank Capstone Widget Platform provides a backend system for managing embeddable lead-capture widgets.

Each tenant can create and manage their own widgets while maintaining separation between their data and other tenants.

Visitors can submit information through embedded forms, and the platform stores submissions and creates background notification jobs.

## 2. Technology Stack

- Python
- FastAPI
- SQLite
- Pydantic
- JavaScript
- HTML and CSS
- SlowAPI
- Git and GitHub

## 3. Features

### Multi-Tenant Architecture

- Tenant authentication using API keys.
- Tenant-specific widget management.
- Tenant-specific dashboard and submissions.
- Data isolation between tenants.

### Widget Management

- Create widgets.
- Retrieve widgets.
- Update widget configuration.
- Delete widgets.
- Generate embeddable JavaScript snippets.
- Retrieve public widget configuration.

### Lead Capture

- Public submission endpoint.
- Input validation.
- Honeypot spam protection.
- Rate limiting.
- Visitor IP address collection.
- Geo enrichment.

### Idempotency

The submission API supports an optional Idempotency-Key header.

When a new request is submitted, the platform creates a submission and notification job within a single database transaction.

If the same request is repeated with the same key, the existing submission and job are returned.

If the same key is reused with different submission content, the API returns HTTP 409 Conflict.

### Background Jobs

- Notification job creation.
- Job status tracking.
- Pending and completed job states.
- Failed job handling.
- Retry mechanism.
- Maximum retry attempts.
- Manual job processing endpoint.

The current notification processing uses a simulated notification action.

## 4. Project Structure

```text
flyrank-capstone-widget-platform/
│
├── main.py
├── database.py
├── widgets.py
├── dashboard.py
├── jobs.py
├── geo.py
├── widget.js
├── capstone.db
├── requirements.txt
├── README.md
└── .gitignore
```

## 5. Installation

Clone the repository:

```bash
git clone https://github.com/muhammad-shahaan/flyrank-capstone-widget-platform.git

cd flyrank-capstone-widget-platform
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The application runs locally at:

http://127.0.0.1:8000

Swagger API documentation:

http://127.0.0.1:8000/docs

## 6. API Endpoints

### General

| Method | Endpoint | Description |
|---|---|---|
| GET | / | API information |
| GET | /health | Health check |

### Widget Management

| Method | Endpoint | Description |
|---|---|---|
| POST | /widgets | Create a widget |
| GET | /widgets | List tenant widgets |
| GET | /widgets/{widget_id} | Get widget details |
| PUT | /widgets/{widget_id} | Update a widget |
| DELETE | /widgets/{widget_id} | Delete a widget |
| GET | /widgets/{widget_id}/snippet | Generate embed snippet |
| GET | /widgets/{widget_id}/config | Get public configuration |
| GET | /widget.js | Retrieve widget JavaScript |

### Lead Capture

| Method | Endpoint | Description |
|---|---|---|
| POST | /submissions | Create a submission |

### Dashboard

| Method | Endpoint | Description |
|---|---|---|
| GET | /dashboard/stats | Get tenant statistics |
| GET | /dashboard/submissions | List tenant submissions |
| GET | /dashboard/widgets/{widget_id}/submissions | List widget submissions |

### Background Jobs

| Method | Endpoint | Description |
|---|---|---|
| POST | /jobs/process | Process due jobs |
| GET | /jobs/{job_id} | Retrieve job status |

## 7. API Authentication

Protected endpoints require the following HTTP header:

```text
x-api-key: YOUR_API_KEY
```

For local development, the database initializes two demo tenants:

```text
Demo Tenant A: tenant-a-key
Demo Tenant B: tenant-b-key
```

These credentials are intended for local testing only and must be replaced before production deployment.

Public widget configuration and submission endpoints do not require tenant API keys.

## 8. Example Submission

Endpoint:

```text
POST /submissions
```

Optional header:

```text
Idempotency-Key: example-request-001
```

Request body:

```json
{
  "widget_id": 1,
  "name": "Shahan",
  "email": "shahan@example.com",
  "message": "Testing the lead capture platform",
  "website": ""
}
```

A successful new submission returns HTTP 201 Created with the submission ID and notification job ID.

Repeating the same request with the same idempotency key returns HTTP 200 OK and the existing submission details.

Reusing the same key with different submission content returns HTTP 409 Conflict.

## 9. Background Job Processing

Each new submission creates a notification job.

Jobs can have the following statuses:

- pending
- processing
- completed
- retry
- failed

The system supports a maximum of three processing attempts.

Failed attempts can be retried after a configured delay.

The current implementation uses a simulated notification action rather than a real email or messaging provider.

## 10. Database

The application currently uses SQLite.

The database file is:

```text
capstone.db
```

The main database tables include:

- tenants
- widgets
- submissions
- jobs

The database is initialized when the FastAPI application starts.

The database file should not be committed to a public GitHub repository.

## 11. Testing

The API can be tested using FastAPI Swagger UI.

The following scenarios have been manually tested during development:

- Widget creation and retrieval.
- Public lead submission.
- Tenant-specific dashboard access.
- Unauthorized API access.
- Background job processing.
- Job status retrieval.
- Duplicate submission handling.
- Idempotency conflict detection.

Idempotency test results:

| Scenario | Expected HTTP Status |
|---|---|
| New submission | 201 Created |
| Repeated request with the same key | 200 OK |
| Same key with different content | 409 Conflict |

## 12. Current Limitations

- SQLite is used for local persistence.
- Notification delivery is simulated.
- Background jobs require an explicit processing trigger.
- Demo API keys are intended for local development.
- Production deployment requires additional configuration and security review.

## 13. Future Improvements

- PostgreSQL database integration.
- Docker-based deployment.
- Automated background job worker.
- Real email notification integration.
- Automated integration tests.
- Production-ready tenant credential management.

## 14. Author

Muhammad Shahan

BS Software Engineering Student

GitHub:

https://github.com/muhammad-shahaan

## 15. Project Repository

https://github.com/muhammad-shahaan/flyrank-capstone-widget-platform