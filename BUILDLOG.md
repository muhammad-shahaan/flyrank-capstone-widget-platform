
# BUILDLOG — FlyRank Capstone Widget Platform

**Developer:** Muhammad Shahan  
**Project:** Embeddable Widget & Lead-Capture Platform  
**Backend:** Python, FastAPI, SQLite  
**Frontend:** JavaScript, HTML, CSS  
**Repository:** https://github.com/muhammad-shahaan/flyrank-capstone-widget-platform

---

## 1. Project Overview

The goal of this capstone project is to develop a multi-tenant platform that allows businesses to create embeddable widgets, collect customer leads, and manage submissions through authenticated API endpoints.

The platform includes widget management, tenant isolation, spam protection, geo enrichment, background jobs, retry handling, and idempotent submissions.

## 2. Development Progress

### Phase 1 — Backend Foundation

**Objective:** Establish the backend application and database structure.

Implemented:
- FastAPI application.
- SQLite database connection.
- Database initialization.
- Health-check endpoint.
- API documentation using Swagger UI.

**Outcome:** Established the backend foundation for the widget platform.

### Phase 2 — Multi-Tenant Widget Management

**Objective:** Allow multiple tenants to manage their own widgets.

Implemented:
- Tenant records and API-key authentication.
- Widget creation, retrieval, updating, and deletion.
- Tenant-specific widget ownership.
- Public widget configuration endpoint.

**Outcome:** Created a multi-tenant widget management system with tenant-specific access controls.

### Phase 3 — Embeddable JavaScript Widget

**Objective:** Allow widgets to be embedded into external websites.

Implemented:
- JavaScript widget loader.
- Dynamic widget configuration retrieval.
- Lead-capture form rendering.
- Name, email, and message fields.
- Form submission through the public API.
- Basic form styling and validation.

**Outcome:** Created a reusable embeddable lead-capture widget.

### Phase 4 — Lead Capture and Protection

**Objective:** Store customer submissions and protect the public submission endpoint.

Implemented:
- Public submission API.
- Input validation.
- Honeypot spam protection.
- Request rate limiting.
- Visitor IP address collection.
- Geo enrichment.
- Tenant-aware submission validation.

**Outcome:** Established the lead-capture workflow with basic abuse protection and tenant association.

### Phase 5 — Tenant Dashboard

**Objective:** Allow tenants to access their own submission data.

Implemented:
- Tenant dashboard statistics.
- Tenant-specific submission retrieval.
- Widget-specific submission retrieval.
- API-key authentication for protected endpoints.

**Outcome:** Added authenticated access to tenant lead data.

### Phase 6 — Background Notification Jobs

**Objective:** Create and process notification jobs for new submissions.

Implemented:
- Jobs database table.
- Notification job creation.
- Job status tracking.
- Pending and completed job states.
- Manual job processing endpoint.
- Retry handling.
- Maximum processing attempts.
- Forced-failure testing support.

**Outcome:** Created a database-backed notification job workflow.

**Current limitation:** Notification delivery is simulated, and jobs require an explicit processing trigger.

### Phase 7 — Idempotent Submissions

**Objective:** Prevent duplicate submissions and notification jobs when the same request is repeated.

Implemented:
- Optional Idempotency-Key request header.
- Request payload hashing.
- Tenant-scoped idempotency keys.
- Unique database constraints.
- Atomic submission and notification job creation.
- Duplicate request detection.
- Conflict detection when a key is reused with different content.

**Outcome:** Implemented idempotent submission handling using a database transaction.

## 3. Testing Evidence

The following API responses were observed during development.

| Test | HTTP Status | Result |
|---|---|---|
| New lead submission | 201 | Passed |
| Duplicate request with the same key | 200 | Passed |
| Same key with different content | 409 | Passed |
| Background job creation | 201 | Passed |
| Job status retrieval | 200 | Passed |
| Successful job processing | 200 | Passed |
| Missing resource | 404 | Observed |
| Invalid API key | 401 | Observed |

### Idempotency Test

A new submission was created using an idempotency key.

The same request was submitted again using the same key and payload.

The API returned the existing submission with:

- HTTP 200 OK.
- duplicate: true.
- Existing submission ID.
- Existing notification job ID.

When the same key was reused with a different message, the API returned HTTP 409 Conflict.

### Background Job Test

A notification job was created after a successful lead submission.

The job was processed using the job-processing endpoint.

The job-status endpoint confirmed that a job had reached the completed state.

Forced-failure and retry behavior require separate final verification.

## 4. Challenges and Solutions

### Challenge 1 — GitHub Connectivity

A GitHub push initially failed because the system could not resolve github.com.

After connectivity was restored, the project changes were pushed successfully.

### Challenge 2 — Tenant Data Isolation

Public submissions needed to be associated with the correct tenant.

The backend was updated to determine tenant ownership through the widget record rather than trusting tenant information supplied by visitors.

### Challenge 3 — Duplicate Requests

Repeated form submissions could create duplicate database records and notification jobs.

Tenant-scoped idempotency keys, request hashing, unique indexes, and atomic database transactions were added.

### Challenge 4 — Background Job Testing

A job-processing test initially used force_failure=false instead of true.

The job completed successfully, but this did not verify retry behavior.

Forced-failure and retry testing remains a separate verification task.

## 5. Current Project Status

Implemented:
- FastAPI backend.
- SQLite persistence.
- Multi-tenant widget management.
- Embeddable JavaScript widget.
- Lead-capture API.
- Spam protection and rate limiting.
- Geo enrichment.
- Tenant dashboard.
- Background notification jobs.
- Idempotent submission handling.

Remaining work:
- Final retry and failure-handling verification.
- Automated integration tests.
- Security and configuration review.
- Final evidence collection.
- Final GitHub submission.

## 6. Future Improvements

- PostgreSQL integration.
- Docker-based deployment.
- Automated background worker.
- Real email or messaging notifications.
- Production-ready tenant credential management.
- Automated CI testing.

## 7. Developer Reflection

This project provided practical experience in backend API development, database design, multi-tenant architecture, authentication, request validation, background job processing, and idempotency.

I also gained experience debugging API responses, working with Git and GitHub, and integrating a JavaScript widget with a FastAPI backend.

The project helped me understand how different backend components work together to support a complete lead-capture workflow.

---

**Developer:** Muhammad Shahan  
**Project:** FlyRank Capstone Widget Platform