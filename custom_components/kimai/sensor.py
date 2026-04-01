"""Sensor platform for Kimai."""

from __future__ import annotations

from datetime import date

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
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
    async_add_entities([
        KimaiNextDayOffSensor(coordinator, entry),
        KimaiNextWorkdaySensor(coordinator, entry),
    ])


class KimaiBaseSensor(CoordinatorEntity[KimaiCoordinator], SensorEntity):
    """Base class for Kimai sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KimaiCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Kimai",
            "entry_type": "service",
        }


class KimaiNextDayOffSensor(KimaiBaseSensor):
    """Sensor showing the next day off (weekend or vacation, excluding today)."""

    _attr_icon = "mdi:calendar-check"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: KimaiCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "next_day_off", "Next Day Off")

    @property
    def native_value(self) -> date | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("next_day_off")



class KimaiNextWorkdaySensor(KimaiBaseSensor):
    """Sensor showing the next workday (weekday without vacation, excluding today)."""

    _attr_icon = "mdi:briefcase-outline"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: KimaiCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "next_workday", "Next Workday")

    @property
    def native_value(self) -> date | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("next_workday")
