from uuid import UUID

from sqlalchemy.orm import Session

from app.models import IntegrationUsageEvent, OrganizationAPIKey


def track_integration_usage(
    db: Session,
    api_key: OrganizationAPIKey,
    endpoint: str,
    event_type: str,
    status_code: int,
    metadata: dict | None = None,
) -> IntegrationUsageEvent:
    event = IntegrationUsageEvent(
        organization_id=api_key.organization_id,
        api_key_id=api_key.id,
        endpoint=endpoint,
        event_type=event_type,
        status_code=status_code,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event


def widget_embed_snippet(api_key: str, api_base_url: str) -> str:
    return (
        '<script src="{api_base}/integrations/widget.js" '
        'data-leadpilot-key="{api_key}" '
        'data-api-base="{api_base}" async></script>'
    ).format(api_key=api_key, api_base=api_base_url.rstrip("/"))


def public_widget_snippet(api_key_id: UUID, api_base_url: str) -> str:
    return (
        '<script src="{api_base}/integrations/widget.js" '
        'data-leadpilot-key="YOUR_RAW_KEY_FOR_{key_id}" '
        'data-api-base="{api_base}" async></script>'
    ).format(api_base=api_base_url.rstrip("/"), key_id=api_key_id)
