"""
FortiMonitor MCP Webhook Receiver - Embedded HTTP Listener

Copyright (c) 2026 Gregori Jenkins
https://github.com/gjenkins20/unofficial-fortimonitor-mcp-server

Lightweight HTTP server embedded in the MCP server process that receives
FortiMonitor outbound webhooks and stores events for query via MCP tools/resources.
"""

import json
import logging
import threading
import time
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_PORT = 8765
DEFAULT_MAX_EVENTS = 500


class WebhookEvent:
    """A single webhook event received from FortiMonitor."""

    def __init__(self, payload: dict, source_ip: str = ""):
        self.timestamp = time.time()
        self.payload = payload
        self.source_ip = source_ip
        self.event_type = self._detect_type(payload)

    def _detect_type(self, payload: dict) -> str:
        """Detect FortiMonitor event type from payload."""
        # FortiMonitor webhook payloads vary; common fields to detect type
        if "outage" in payload or "outage_id" in payload:
            status = payload.get("status", payload.get("outage_status", ""))
            if status in ("active", "new"):
                return "outage_started"
            elif status in ("cleared", "resolved"):
                return "outage_cleared"
            return "outage_update"
        if "maintenance" in payload:
            return "maintenance"
        if "escalation" in payload or "escalated" in payload:
            return "escalation"
        return "unknown"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp)),
            "event_type": self.event_type,
            "source_ip": self.source_ip,
            "payload": self.payload,
        }


class EventStore:
    """Thread-safe ring buffer for webhook events."""

    def __init__(self, max_events: int = DEFAULT_MAX_EVENTS):
        self._events = deque(maxlen=max_events)
        self._lock = threading.Lock()

    def add(self, event: WebhookEvent):
        with self._lock:
            self._events.append(event)

    def get_recent(self, limit: int = 25, event_type: Optional[str] = None) -> list:
        with self._lock:
            events = list(self._events)
        # Most recent first
        events.reverse()
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events[:limit]]

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self):
        with self._lock:
            self._events.clear()


# Global event store shared with MCP tools
event_store = EventStore()


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for FortiMonitor webhooks."""

    def do_POST(self):
        """Handle incoming webhook POST."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 1_000_000:  # 1MB limit
            self.send_response(413)
            self.end_headers()
            return

        body = self.rfile.read(content_length)
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        # Validate webhook secret if configured
        expected_secret = getattr(self.server, "webhook_secret", None)
        if expected_secret:
            provided = self.headers.get("X-Webhook-Secret", "")
            if provided != expected_secret:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"error": "Invalid webhook secret"}')
                return

        source_ip = self.client_address[0] if self.client_address else ""
        event = WebhookEvent(payload=payload, source_ip=source_ip)
        event_store.add(event)

        logger.info(f"Webhook received: {event.event_type} from {source_ip}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received", "event_type": event.event_type}).encode())

    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "event_count": event_store.count(),
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Route HTTP logs through our logger instead of stderr."""
        logger.debug(f"Webhook HTTP: {format % args}")


class WebhookReceiver:
    """Manages the embedded webhook HTTP server in a background thread."""

    def __init__(self, port: int = DEFAULT_PORT, secret: Optional[str] = None):
        self.port = port
        self.secret = secret
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the webhook receiver in a background thread."""
        try:
            self._server = HTTPServer(("0.0.0.0", self.port), WebhookHandler)
            if self.secret:
                self._server.webhook_secret = self.secret
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                name="webhook-receiver",
                daemon=True,
            )
            self._thread.start()
            logger.info(f"Webhook receiver started on port {self.port}")
        except OSError as e:
            logger.warning(f"Could not start webhook receiver on port {self.port}: {e}")
            self._server = None

    def stop(self):
        """Stop the webhook receiver."""
        if self._server:
            self._server.shutdown()
            logger.info("Webhook receiver stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
