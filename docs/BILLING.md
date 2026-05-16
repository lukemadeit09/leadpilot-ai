# Billing and Usage Quotas

LeadPilot AI includes a minimal SaaS monetization foundation with Stripe Checkout, subscription webhooks, and AI usage quota enforcement.

## Plans

| Plan | Monthly AI Credit Limit | Intended Customer |
| --- | ---: | --- |
| Starter | $5 | Solo operators and demos |
| Pro | $50 | Small sales teams |
| Agency | $250 | Higher-volume teams and client services |

The limits are enforced against estimated AI cost, not raw request count. Each AI request records:

- organization
- user
- model used
- input tokens
- output tokens
- estimated cost
- endpoint used
- timestamp

## Enforcement

Before an AI endpoint runs, the backend estimates projected cost for the request and compares it to the organization's current monthly usage. If the projected request would exceed the plan limit, the API returns `402 Payment Required`.

Protected endpoints:

- `POST /ai/analyze-lead`
- `POST /ai/generate-reply`
- `POST /knowledge/ask`

## Stripe Integration

Billing is organization-scoped. Owner/admin users can create Stripe Checkout sessions or open the Stripe billing portal. Stripe webhooks update organization subscription status and map the active price back to the Starter, Pro, or Agency plan.

Required backend environment variables:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_STARTER_PRICE_ID`
- `STRIPE_PRO_PRICE_ID`
- `STRIPE_AGENCY_PRICE_ID`
- `FRONTEND_URL`

Secrets are only read by the backend. The frontend never receives Stripe secret keys.

## APIs

- `GET /billing/plans`: returns available plans and monthly limits.
- `GET /billing/usage`: returns current organization and user usage for the month.
- `POST /billing/checkout`: creates a Stripe Checkout session for owner/admin members.
- `POST /billing/portal`: creates a Stripe billing portal session for owner/admin members.
- `POST /billing/webhook`: validates Stripe signatures and applies subscription changes.
- `PATCH /billing/plan`: manual admin plan override for local development and non-Stripe demos. Restricted to owner/admin members.

## Frontend

The settings page shows current plan, subscription status, usage, remaining AI credits, Checkout actions, and billing portal access. The pricing page links authenticated users into Checkout and routes unauthenticated visitors to workspace registration.

## Not Included Yet

- invoices
- tax handling
