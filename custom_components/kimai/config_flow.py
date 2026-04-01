"""Config flow for Kimai integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KimaiApi, KimaiApiError, KimaiAuthError
from .const import (
    CONF_API_TOKEN,
    CONF_API_USER,
    CONF_BASE_URL,
    CONF_REQUIRED_MINUTES_PER_DAY,
    CONF_VACATION_ACTIVITY_IDS,
    DEFAULT_REQUIRED_MINUTES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL): str,
        vol.Required(CONF_API_USER): str,
        vol.Required(CONF_API_TOKEN): str,
        vol.Optional(CONF_VACATION_ACTIVITY_IDS, default=""): str,
        vol.Optional(
            CONF_REQUIRED_MINUTES_PER_DAY, default=DEFAULT_REQUIRED_MINUTES
        ): int,
    }
)


class KimaiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kimai."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = KimaiApi(
                session,
                user_input[CONF_BASE_URL],
                user_input[CONF_API_USER],
                user_input[CONF_API_TOKEN],
            )

            try:
                me = await api.get_me()
            except KimaiAuthError:
                errors["base"] = "invalid_auth"
            except KimaiApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                username = me.get("alias") or me.get("username", "Kimai")
                await self.async_set_unique_id(
                    f"{user_input[CONF_BASE_URL]}_{user_input[CONF_API_USER]}"
                )
                self._abort_if_unique_id_configured()

                # Parse vacation activity IDs
                raw_ids = user_input.get(CONF_VACATION_ACTIVITY_IDS, "")
                vacation_ids = []
                if raw_ids.strip():
                    vacation_ids = [
                        int(x.strip())
                        for x in raw_ids.split(",")
                        if x.strip().isdigit()
                    ]

                return self.async_create_entry(
                    title=f"Kimai ({username})",
                    data={
                        CONF_BASE_URL: user_input[CONF_BASE_URL],
                        CONF_API_USER: user_input[CONF_API_USER],
                        CONF_API_TOKEN: user_input[CONF_API_TOKEN],
                        CONF_VACATION_ACTIVITY_IDS: vacation_ids,
                        CONF_REQUIRED_MINUTES_PER_DAY: user_input.get(
                            CONF_REQUIRED_MINUTES_PER_DAY, DEFAULT_REQUIRED_MINUTES
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
