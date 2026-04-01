"""Kimai Time Tracking integration for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KimaiApi
from .const import (
    CONF_API_TOKEN,
    CONF_API_USER,
    CONF_BASE_URL,
    CONF_VACATION_ACTIVITY_IDS,
    DOMAIN,
)
from .coordinator import KimaiCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Kimai from a config entry."""
    session = async_get_clientsession(hass)
    api = KimaiApi(
        session,
        entry.data[CONF_BASE_URL],
        entry.data[CONF_API_USER],
        entry.data[CONF_API_TOKEN],
    )

    vacation_ids = entry.data.get(CONF_VACATION_ACTIVITY_IDS, [])
    coordinator = KimaiCoordinator(hass, api, vacation_ids)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
