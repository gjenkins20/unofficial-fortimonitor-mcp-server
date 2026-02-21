"""Crawl state persistence — save/load/resume crawl progress to JSON.

Allows crawls to be interrupted and resumed by persisting the current
queue, visited URLs, and error list.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..models import CrawlProgress, CrawlStatus

logger = logging.getLogger(__name__)


class CrawlState:
    """Manages crawl progress persistence."""

    def __init__(self, state_dir: str = "data/webgui/crawl_state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _state_path(self, crawl_id: str) -> Path:
        return self.state_dir / f"{crawl_id}.json"

    def save(
        self,
        crawl_id: str,
        status: CrawlStatus,
        visited: Set[str],
        queue: List[str],
        errors: List[str],
        current_page: Optional[str] = None,
        started_at: Optional[datetime] = None,
    ) -> None:
        """Save current crawl state to disk."""
        data = {
            "crawl_id": crawl_id,
            "status": status.value,
            "visited": list(visited),
            "queue": queue,
            "errors": errors,
            "current_page": current_page,
            "started_at": started_at.isoformat() if started_at else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._state_path(crawl_id).write_text(json.dumps(data, indent=2))

    def load(self, crawl_id: str) -> Optional[Dict]:
        """Load crawl state from disk. Returns None if not found."""
        path = self._state_path(crawl_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except Exception as e:
            logger.error(f"Error loading crawl state {crawl_id}: {e}")
            return None

    def get_progress(self, crawl_id: str) -> Optional[CrawlProgress]:
        """Get crawl progress as a CrawlProgress model."""
        data = self.load(crawl_id)
        if not data:
            return None
        visited = data.get("visited", [])
        queue = data.get("queue", [])
        return CrawlProgress(
            crawl_id=crawl_id,
            status=CrawlStatus(data.get("status", "pending")),
            pages_discovered=len(visited) + len(queue),
            pages_crawled=len(visited),
            pages_remaining=len(queue),
            current_page=data.get("current_page"),
            errors=data.get("errors", []),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None,
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None,
        )

    def delete(self, crawl_id: str) -> bool:
        """Delete crawl state."""
        path = self._state_path(crawl_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_crawls(self) -> List[Dict]:
        """List all saved crawl states."""
        results = []
        for path in sorted(self.state_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(path.read_text())
                results.append({
                    "crawl_id": data.get("crawl_id", path.stem),
                    "status": data.get("status", "unknown"),
                    "pages_crawled": len(data.get("visited", [])),
                    "pages_remaining": len(data.get("queue", [])),
                    "updated_at": data.get("updated_at"),
                })
            except Exception:
                continue
        return results
