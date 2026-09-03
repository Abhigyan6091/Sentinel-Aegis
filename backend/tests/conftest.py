import pytest

from app.events.bus import get_event_bus
from app.observability.telemetry import get_telemetry
from app.redteam.runner import campaign_store
from app.security.guardrails import get_conversation_memory


@pytest.fixture(autouse=True)
def reset_process_state():
    """Clear process-global runtime state so tests cannot leak into each other."""
    campaign_store.clear()
    get_conversation_memory().clear()
    get_telemetry().clear()
    get_event_bus().clear()
    yield
