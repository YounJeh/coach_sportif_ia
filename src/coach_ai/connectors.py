from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict


class BaseConnector:
    name = "base"

    def health_check(self) -> dict[str, str]:
        return {"status": "ok", "connector": self.name}


class StravaConnector(BaseConnector):
    name = "strava"

    async def fetch_activity_range(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "source": self.name,
            "activities": [{"duration_min": 45, "rpe": 6}],
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }


class CalendarConnector(BaseConnector):
    name = "calendar"

    async def fetch_calendar(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "source": self.name,
            "busy_slots": ["2026-07-10T12:00:00Z/2026-07-10T14:00:00Z"],
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }


class Connectors(TypedDict):
    strava: StravaConnector
    calendar: CalendarConnector


def get_connectors() -> Connectors:
    return {
        "strava": StravaConnector(),
        "calendar": CalendarConnector(),
    }
