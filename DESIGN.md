# Embeddable Widget & Lead-Capture Platform — Design

## 1. Problem

Customers need a simple way to create lead-capture widgets and embed them on external websites.

The platform allows a customer to create a widget, receive an embeddable script snippet, and safely collect visitor submissions.

## 2. Widget Model

- id
- tenant_id
- type
- title
- description
- button_text
- form_fields
- display_options
- created_at
- updated_at

Each widget belongs to one tenant. A tenant cannot access or modify another tenant's widgets.

## 3. Submission Model

- id
- widget_id
- tenant_id
- form_data
- ip_address
- country
- city
- created_at

Each submission belongs to a widget and its tenant.

## 4. Embed Flow

Customer creates widget
→ Backend stores widget
→ Backend generates script snippet
→ Customer adds script to external website
→ Script loads widget configuration
→ Widget renders
→ Visitor submits form
→ Validate input
→ Rate limit + spam check
→ Geo enrichment
→ Store submission
→ Safe email/webhook side effect

## 5. API Contracts

### Authenticated Owner API

POST /widgets
GET /widgets
GET /widgets/{id}
PUT /widgets/{id}
DELETE /widgets/{id}

### Public Widget API

GET /widgets/{id}/config
GET /widget.js

### Public Submission API

POST /submissions

### Dashboard API

GET /dashboard/submissions
GET /dashboard/stats

## 6. Non-Goal

This project will not build a complete visual form builder, production CDN, or hosted customer website.

The customer website will be a simple HTML page running from a different local origin.
