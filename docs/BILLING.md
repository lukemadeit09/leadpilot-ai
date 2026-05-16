# Billing and Usage Quotas

LeadPilot AI includes a minimal SaaS monetization foundation without Stripe payments.

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

## APIs

- `GET /billing/plans`: returns available plans and monthly limits.
- `GET /billing/usage`: returns current organization and user usage for the month.
- `PATCH /billing/plan`: changes the organization plan. Restricted to owner/admin members.

## Frontend

The dashboard and settings page show current plan, usage, and remaining AI credits. This is intentionally not a payment UI yet.

## Not Included Yet

- Stripe checkout
- invoices
- paid subscription webhooks
- customer portal
- tax handling
