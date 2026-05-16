import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.config import Settings

logger = logging.getLogger("leadpilot.sentry")


def init_sentry(settings: Settings) -> None:
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[FastApiIntegration()],
        send_default_pii=False,
    )
    logger.info("Sentry backend monitoring enabled")
