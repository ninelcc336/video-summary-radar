from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class TimeWindow:
    label: str
    start_at: datetime
    end_at: datetime


def parse_range(range_value: str, now: datetime | None = None) -> TimeWindow:
    end_at = now or datetime.now(timezone.utc)
    if end_at.tzinfo is None:
        end_at = end_at.replace(tzinfo=timezone.utc)

    days_by_range = {
        "1d": 1,
        "7d": 7,
        "30d": 30,
    }
    if range_value not in days_by_range:
        raise ValueError("range must be one of: 1d, 7d, 30d")

    return TimeWindow(
        label=range_value,
        start_at=end_at - timedelta(days=days_by_range[range_value]),
        end_at=end_at,
    )


def is_inside_window(published_at: datetime, window: TimeWindow) -> bool:
    value = published_at
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return window.start_at <= value <= window.end_at
