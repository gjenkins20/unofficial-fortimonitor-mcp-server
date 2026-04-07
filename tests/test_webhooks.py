"""
Tests for webhook receiver, event store, and webhook tools.
"""

import json
import time
import pytest
from unittest.mock import MagicMock

from src.webhooks.receiver import WebhookEvent, EventStore
from src.webhooks.tools import (
    WEBHOOK_TOOL_DEFINITIONS,
    WEBHOOK_HANDLERS,
    handle_list_webhook_events,
    handle_get_webhook_status,
    handle_clear_webhook_events,
)


class TestWebhookEvent:

    def test_outage_started_detection(self):
        event = WebhookEvent({"outage": True, "status": "active"})
        assert event.event_type == "outage_started"

    def test_outage_cleared_detection(self):
        event = WebhookEvent({"outage": True, "status": "cleared"})
        assert event.event_type == "outage_cleared"

    def test_outage_update_detection(self):
        event = WebhookEvent({"outage_id": 123, "status": "acknowledged"})
        assert event.event_type == "outage_update"

    def test_escalation_detection(self):
        event = WebhookEvent({"escalation": True})
        assert event.event_type == "escalation"

    def test_maintenance_detection(self):
        event = WebhookEvent({"maintenance": True})
        assert event.event_type == "maintenance"

    def test_unknown_type(self):
        event = WebhookEvent({"something": "else"})
        assert event.event_type == "unknown"

    def test_to_dict(self):
        event = WebhookEvent({"test": 1}, source_ip="192.168.1.1")
        d = event.to_dict()
        assert "timestamp" in d
        assert "timestamp_iso" in d
        assert d["source_ip"] == "192.168.1.1"
        assert d["payload"] == {"test": 1}


class TestEventStore:

    def test_add_and_retrieve(self):
        store = EventStore(max_events=10)
        store.add(WebhookEvent({"outage": True, "status": "active"}))
        events = store.get_recent()
        assert len(events) == 1
        assert events[0]["event_type"] == "outage_started"

    def test_max_events_limit(self):
        store = EventStore(max_events=3)
        for i in range(5):
            store.add(WebhookEvent({"id": i}))
        assert store.count() == 3

    def test_most_recent_first(self):
        store = EventStore(max_events=10)
        store.add(WebhookEvent({"id": "first"}))
        time.sleep(0.01)
        store.add(WebhookEvent({"id": "second"}))
        events = store.get_recent()
        assert events[0]["payload"]["id"] == "second"

    def test_filter_by_type(self):
        store = EventStore(max_events=10)
        store.add(WebhookEvent({"outage": True, "status": "active"}))
        store.add(WebhookEvent({"escalation": True}))
        store.add(WebhookEvent({"outage": True, "status": "cleared"}))

        outage_started = store.get_recent(event_type="outage_started")
        assert len(outage_started) == 1

        escalations = store.get_recent(event_type="escalation")
        assert len(escalations) == 1

    def test_clear(self):
        store = EventStore(max_events=10)
        store.add(WebhookEvent({"test": 1}))
        assert store.count() == 1
        store.clear()
        assert store.count() == 0

    def test_limit_parameter(self):
        store = EventStore(max_events=10)
        for i in range(5):
            store.add(WebhookEvent({"id": i}))
        events = store.get_recent(limit=2)
        assert len(events) == 2


class TestWebhookToolDefinitions:

    def test_tool_count(self):
        assert len(WEBHOOK_TOOL_DEFINITIONS) == 3

    def test_handler_count(self):
        assert len(WEBHOOK_HANDLERS) == 3

    def test_all_tools_have_handlers(self):
        for name in WEBHOOK_TOOL_DEFINITIONS:
            assert name in WEBHOOK_HANDLERS

    @pytest.mark.parametrize("name", [
        "list_webhook_events",
        "get_webhook_status",
        "clear_webhook_events",
    ])
    def test_tool_definition_valid(self, name):
        tool = WEBHOOK_TOOL_DEFINITIONS[name]()
        assert tool.name == name
        assert tool.description


class TestWebhookToolHandlers:

    @pytest.fixture(autouse=True)
    def clean_event_store(self):
        """Clear the global event store before each test."""
        from src.webhooks.receiver import event_store
        event_store.clear()
        yield
        event_store.clear()

    @pytest.mark.asyncio
    async def test_list_webhook_events_empty(self):
        result = await handle_list_webhook_events({}, None)
        data = json.loads(result[0].text)
        assert data["webhook_events"]["count"] == 0

    @pytest.mark.asyncio
    async def test_list_webhook_events_with_data(self):
        from src.webhooks.receiver import event_store
        event_store.add(WebhookEvent({"outage": True, "status": "active"}))
        event_store.add(WebhookEvent({"escalation": True}))

        result = await handle_list_webhook_events({}, None)
        data = json.loads(result[0].text)
        assert data["webhook_events"]["count"] == 2

    @pytest.mark.asyncio
    async def test_list_webhook_events_with_type_filter(self):
        from src.webhooks.receiver import event_store
        event_store.add(WebhookEvent({"outage": True, "status": "active"}))
        event_store.add(WebhookEvent({"escalation": True}))

        result = await handle_list_webhook_events({"event_type": "escalation"}, None)
        data = json.loads(result[0].text)
        assert data["webhook_events"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_webhook_status(self):
        result = await handle_get_webhook_status({}, None)
        data = json.loads(result[0].text)
        assert "webhook_status" in data

    @pytest.mark.asyncio
    async def test_clear_webhook_events(self):
        from src.webhooks.receiver import event_store
        event_store.add(WebhookEvent({"test": 1}))
        result = await handle_clear_webhook_events({}, None)
        assert "Cleared 1" in result[0].text
        assert event_store.count() == 0
