"""Binary sensor platform for Kimai."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KimaiCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: KimaiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KimaiIsDayOffSensor(coordinator, entry)])


class KimaiIsDayOffSensor(CoordinatorEntity[KimaiCoordinator], BinarySensorEntity):
    """Binary sensor that indicates if today is a day off (weekend or vacation)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:palm-tree"

    def __init__(
        self,
        coordinator: KimaiCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_is_day_off"
        self._attr_name = "Is Day Off"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Kimai",
            "entry_type": "service",
        }

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        return self.coordinator.data.get("is_day_off", False)
