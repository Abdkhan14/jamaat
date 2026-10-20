import logging
import os
from contextlib import contextmanager

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

UNSAMPLED_PATHS = {"/health"}


def _traces_sampler(sampling_context):
    path = sampling_context.get("wsgi_environ", {}).get("PATH_INFO")
    return 0.0 if path in UNSAMPLED_PATHS else 1.0


def init_sentry():
    # Root logger defaults to WARNING, which would hide INFO logs from both stdout and Sentry.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT", "development"),
        # Required for OpenAI prompt/response capture; prompts are public mosque page text.
        send_default_pii=True,
        traces_sampler=_traces_sampler,
        integrations=[
            LoggingIntegration(capture_sentry_logs=True, sentry_logs_level=logging.INFO),
        ],
    )


@contextmanager
def mosque_scope(mosque_name, op):
    """Tag every error, log and span inside the block with the mosque it belongs to."""
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("mosque", mosque_name)
        scope.set_attribute("mosque", mosque_name)
        with sentry_sdk.start_span(op=op, name=mosque_name):
            yield
