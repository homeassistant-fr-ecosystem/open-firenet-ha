from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OpenFirenetCoordinator

# Known sensor keys with human labels and optional unit
KNOWN_SENSORS: dict[str, tuple[str, str | None]] = {
    "stoveOnOff":      ("Stove On/Off",          None),
    "stoveOpMode":     ("Operating Mode",         None),
    "stovePower":      ("Heating Power",          "%"),
    "stoveTempTarget": ("Target Temperature Raw", None),
}

# Keys handled by other entities or not suitable as sensors
_SKIP_KEYS = {"onOff", "operatingMode", "heatingPower", "tempRoomTarget"}


def _is_primitive(value) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: OpenFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        OpenFirenetSensor(coordinator, entry, key)
        for key, value in coordinator.data.sensors.items()
        if key not in _SKIP_KEYS and _is_primitive(value)
    ]
    async_add_entities(entities)


class OpenFirenetSensor(CoordinatorEntity[OpenFirenetCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: OpenFirenetCoordinator, entry: ConfigEntry, key: str
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        label, unit = KNOWN_SENSORS.get(key, (key, None))
        self._attr_name = label
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_sensor_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def native_value(self):
        raw = self.coordinator.data.sensors.get(self._key)
        if not _is_primitive(raw):
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return raw

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.MEASUREMENT if isinstance(self.native_value, float) else None
