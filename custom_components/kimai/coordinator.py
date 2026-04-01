"""Data update coordinator for Kimai."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import KimaiApi, KimaiApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

# Saturday=5, Sunday=6
WEEKEND_DAYS = {5, 6}


class KimaiCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from Kimai API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: KimaiApi,
        vacation_activity_ids: list[int],
        required_minutes_per_day: int = 480,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api
        self.vacation_activity_ids = vacation_activity_ids
        self.required_minutes_per_day = required_minutes_per_day

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            now = dt_util.now()
            today = now.date()

            # Today's timesheets only (with end filter to exclude future entries)
            today_begin = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_begin = today_begin + timedelta(days=1)
            today_timesheets = await self.api.get_timesheets(
                begin=today_begin.strftime("%Y-%m-%dT%H:%M:%S"),
                end=tomorrow_begin.strftime("%Y-%m-%dT%H:%M:%S"),
                size=100,
            )

            # Today's tracked duration in minutes
            today_duration_seconds = self._sum_duration(today_timesheets)
            today_duration_minutes = today_duration_seconds // 60

            # Check if today is a day off (weekend or vacation/holiday activity)
            is_weekend = today.weekday() in WEEKEND_DAYS
            today_vacation_entries = self._filter_vacation_entries(today_timesheets)
            is_day_off = is_weekend or len(today_vacation_entries) > 0

            # Work time fulfilled and missing minutes (always fulfilled on days off)
            if is_day_off:
                missing_minutes = 0
                work_time_fulfilled = True
                overtime_minutes = today_duration_minutes
            else:
                missing_minutes = max(0, self.required_minutes_per_day - today_duration_minutes)
                work_time_fulfilled = missing_minutes == 0
                overtime_minutes = max(0, today_duration_minutes - self.required_minutes_per_day)

            # Fetch future vacation dates for next_day_off and next_workday
            future_vacation_dates = await self._get_future_vacation_dates(today)

            # Next day off (excluding today)
            next_day_off = self._find_next_day_off(today, future_vacation_dates)

            # Next workday (excluding today): weekday without vacation
            next_workday = self._find_next_workday(today, future_vacation_dates)

            return {
                "is_day_off": is_day_off,
                "next_day_off": next_day_off,
                "next_workday": next_workday,
                "today_duration_minutes": today_duration_minutes,
                "missing_minutes": missing_minutes,
                "overtime_minutes": overtime_minutes,
                "work_time_fulfilled": work_time_fulfilled,
            }
        except KimaiApiError as err:
            raise UpdateFailed(f"Error fetching Kimai data: {err}") from err

    async def _get_future_vacation_dates(self, today: date) -> set[date]:
        """Fetch all future vacation dates after today."""
        if not self.vacation_activity_ids:
            return set()
        try:
            entries = await self.api.get_future_timesheets(
                self.vacation_activity_ids
            )
            dates = set()
            for entry in entries:
                begin = entry.get("begin")
                if not begin:
                    continue
                try:
                    entry_date = datetime.fromisoformat(begin).date()
                except (ValueError, TypeError):
                    continue
                if entry_date > today:
                    dates.add(entry_date)
            return dates
        except KimaiApiError:
            _LOGGER.warning("Could not fetch future vacation timesheets")
            return set()

    @staticmethod
    def _find_next_day_off(today: date, vacation_dates: set[date]) -> date:
        """Find the next day off after today (weekend or vacation)."""
        day = today + timedelta(days=1)
        # Search up to 365 days ahead
        for _ in range(365):
            if day.weekday() in WEEKEND_DAYS or day in vacation_dates:
                return day
            day += timedelta(days=1)
        return today + timedelta(days=1)

    @staticmethod
    def _find_next_workday(today: date, vacation_dates: set[date]) -> date:
        """Find the next workday after today (weekday without vacation)."""
        day = today + timedelta(days=1)
        # Search up to 365 days ahead
        for _ in range(365):
            if day.weekday() not in WEEKEND_DAYS and day not in vacation_dates:
                return day
            day += timedelta(days=1)
        return today + timedelta(days=1)

    @staticmethod
    def _sum_duration(timesheets: list[dict]) -> int:
        """Sum duration of timesheets in seconds."""
        return sum(t.get("duration", 0) or 0 for t in timesheets)

    def _filter_vacation_entries(self, timesheets: list[dict]) -> list[dict]:
        """Filter timesheets to only vacation/holiday activity entries."""
        if not self.vacation_activity_ids:
            return []
        return [
            t for t in timesheets
            if t.get("activity") in self.vacation_activity_ids
        ]
