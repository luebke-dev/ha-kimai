"""Kimai API client."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class KimaiApiError(Exception):
    """Kimai API error."""


class KimaiAuthError(KimaiApiError):
    """Kimai authentication error."""


class KimaiApi:
    """Client for the Kimai REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        api_user: str,
        api_token: str,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "X-AUTH-USER": api_user,
            "X-AUTH-TOKEN": api_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self._base_url}/api/{path.lstrip('/')}"
        try:
            async with self._session.request(
                method, url, headers=self._headers, **kwargs
            ) as resp:
                if resp.status == 403:
                    raise KimaiAuthError("Authentication failed")
                if resp.status >= 400:
                    text = await resp.text()
                    raise KimaiApiError(
                        f"API request failed ({resp.status}): {text}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise KimaiApiError(f"Connection error: {err}") from err

    async def ping(self) -> dict:
        return await self._request("GET", "ping")

    async def get_me(self) -> dict:
        return await self._request("GET", "users/me")

    async def get_activities(self, **params: Any) -> list[dict]:
        return await self._request("GET", "activities", params=params)

    async def get_timesheets(self, **params: Any) -> list[dict]:
        return await self._request("GET", "timesheets", params=params)

    async def get_active_timesheets(self) -> list[dict]:
        return await self._request("GET", "timesheets/active")

    async def get_recent_timesheets(self, size: int = 10) -> list[dict]:
        return await self._request(
            "GET", "timesheets/recent", params={"size": size}
        )

    async def get_timesheet(self, timesheet_id: int) -> dict:
        return await self._request("GET", f"timesheets/{timesheet_id}")

    async def start_timesheet(self, data: dict) -> dict:
        return await self._request("POST", "timesheets", json=data)

    async def stop_timesheet(self, timesheet_id: int) -> dict:
        return await self._request("PATCH", f"timesheets/{timesheet_id}/stop")

    async def get_projects(self, **params: Any) -> list[dict]:
        return await self._request("GET", "projects", params=params)

    async def get_customers(self, **params: Any) -> list[dict]:
        return await self._request("GET", "customers", params=params)

    async def get_future_timesheets(
        self, activity_ids: list[int] | None = None
    ) -> list[dict]:
        """Fetch future timesheet entries, optionally filtered by activity IDs."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        params: dict[str, Any] = {
            "begin": now,
            "order": "ASC",
            "orderBy": "begin",
            "size": 50,
            "user": "all",
        }
        results = await self._request("GET", "timesheets", params=params)
        if activity_ids:
            results = [
                r for r in results if r.get("activity") in activity_ids
            ]
        return results
