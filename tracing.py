"""Sentry agent tracing. If SENTRY_DSN is empty, every helper is a harmless no-op."""
import sentry_sdk

from config import SENTRY_DSN

ENABLED = False


class _Noop:
    def set_data(self, key, value):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def init() -> bool:
    global ENABLED
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0,
            send_default_pii=False,
            environment="local",
        )
        ENABLED = True
    return ENABLED


def agent_run(name: str):
    """Top-level transaction for one agent run (e.g. making today's nudge)."""
    if ENABLED:
        return sentry_sdk.start_transaction(op="gen_ai.invoke_agent", name=name)
    return _Noop()


def span(op: str, name: str):
    """Child span: op examples 'gen_ai.chat', 'db', 'tts'."""
    if ENABLED:
        return sentry_sdk.start_span(op=op, name=name)
    return _Noop()


def capture(exc: Exception):
    if ENABLED:
        sentry_sdk.capture_exception(exc)


def flush():
    if ENABLED:
        sentry_sdk.flush(timeout=5)
