# Demo Guide

Use this guide to run a portfolio demo or an early customer walkthrough.

## Demo Script

1. Open the landing page and describe the product:
   LeadPilot AI turns inbound customer messages into CRM records, AI analysis, professional replies, follow-up tasks, and activity logs.

2. Create a workspace:
   Register a new account. The app creates a workspace and owner membership automatically.

3. Run the sample AI workflow:
   Open `/analyzer` and use this sample message:

```text
Hi, we are a 45-person operations team and are interested in your software. Can you send pricing and schedule a demo next week?
```

Expected result:

- lead score around 85
- positive sentiment
- qualified CRM status
- professional reply draft
- follow-up task for a demo
- recent activity log entry

4. Review the dashboard:
   Show total leads, qualified leads, AI credits remaining, pending tasks, pipeline chart, AI usage guardrail, and recent activity.

5. Review tasks:
   Show the follow-up task created by the AI workflow.

6. Upload knowledge:
   Upload a small pricing, FAQ, or product text/PDF document in `/knowledge`.

7. Ask a grounded question:
   Example: "What should I tell a customer asking about pricing?"

## Sample Knowledge Document

```text
LeadPilot AI helps sales teams qualify inbound leads, draft professional replies, create follow-up tasks, and answer questions using uploaded company knowledge.

Starter is for demos and solo validation. Pro is for small sales teams. Agency is for high-volume teams and client service workflows.

Customers asking for pricing should be offered a short discovery call so the team can confirm team size, workflow needs, and expected lead volume.
```

## Screenshots To Capture

- Landing page hero
- Pricing page
- Onboarding guide
- Dashboard with populated metrics
- AI analyzer result
- Lead detail page
- Knowledge base Q&A with citations
- Settings usage panel

## Demo Notes

- The app works without a live OpenAI key by using deterministic fallback behavior.
- For a stronger demo, set `OPENAI_API_KEY` and upload a small product/pricing document.
- Do not use real customer data in portfolio screenshots.
