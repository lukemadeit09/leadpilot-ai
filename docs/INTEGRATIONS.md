# Business Integrations

LeadPilot AI can accept leads from websites, widgets, and external systems through organization-scoped API keys.

## Security Model

- API keys are generated with a secure random token.
- The raw key is returned only once during creation.
- Only the SHA-256 hash is stored in the database.
- Public requests must include `X-LeadPilot-Key`.
- Leads created through public endpoints are scoped to the organization that owns the API key.
- Revoked API keys are rejected immediately.
- Public endpoints are rate limited.

## API Keys

Create an API key from the integrations page or with:

```bash
curl -X POST http://localhost:8000/integrations/api-keys \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"name":"Website form"}'
```

Save the returned `api_key` securely. It is not shown again.

## Public Lead Intake

```bash
curl -X POST http://localhost:8000/integrations/public/leads \
  -H "Content-Type: application/json" \
  -H "X-LeadPilot-Key: lp_live_YOUR_API_KEY" \
  -d '{
    "name": "Alex Buyer",
    "email": "alex@example.com",
    "company": "Acme",
    "message": "We need pricing and a demo next week."
  }'
```

## Webhook Intake

Use the webhook endpoint for contact forms and external systems that send named events.

```bash
curl -X POST http://localhost:8000/integrations/public/webhook \
  -H "Content-Type: application/json" \
  -H "X-LeadPilot-Key: lp_live_YOUR_API_KEY" \
  -d '{
    "event": "contact_form.submitted",
    "lead": {
      "name": "Alex Buyer",
      "email": "alex@example.com",
      "company": "Acme",
      "message": "We need pricing and a demo next week."
    },
    "metadata": {
      "source": "website"
    }
  }'
```

## Embeddable Widget

Add this script to a marketing site, CMS page, or static site:

```html
<script
  src="http://localhost:8000/integrations/widget.js"
  data-leadpilot-key="lp_live_YOUR_API_KEY"
  data-api-base="http://localhost:8000"
  async>
</script>
```

The widget is framework-agnostic and posts leads to `/integrations/public/leads`.

## Widget Configuration

Owners/admins can configure:

- enabled/disabled state
- widget title
- accent color

The public widget reads configuration using the API key, but it never receives internal organization data.

## Usage Tracking

Integration calls are tracked in `integration_usage_events` with:

- organization
- API key id
- endpoint
- event type
- status code
- timestamp

The frontend integrations page shows recent usage for operational debugging.
