from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OpenFirenetCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: OpenFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        OpenFirenetConnected(coordinator, entry),
        OpenFirenetWifi(coordinator, entry),
        OpenFirenetProvisioning(coordinator, entry),
    ])


class OpenFirenetConnected(CoordinatorEntity[OpenFirenetCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: OpenFirenetCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connected"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("status", {}).get("mainLoop", False)


class OpenFirenetWifi(CoordinatorEntity[OpenFirenetCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "wifi"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: OpenFirenetCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_wifi"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("status", {}).get("wifi", False)


class OpenFirenetProvisioning(CoordinatorEntity[OpenFirenetCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "provisioning"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: OpenFirenetCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_provisioning"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("status", {}).get("provisioning", False)
