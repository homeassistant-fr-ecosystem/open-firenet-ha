from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OpenFirenetCoordinator

_D = EntityCategory.DIAGNOSTIC

# Sensors from /api/sensors: key → (unit, device_class, divide_by_10, entity_category, state_class_override)
# divide_by_10=True for stove values encoded as integer×10 (e.g. 233 = 23.3°C)
# state_class_override=None falls back to the generic float→MEASUREMENT heuristic
# Names are resolved via translation_key → strings.json entity.sensor.<key>.name
KNOWN_SENSORS: dict[str, tuple[str | None, str | None, bool, EntityCategory | None, SensorStateClass | None]] = {
    # Stove POST_SENSORS fields (f0 = sRoomTemp_ACT, f1..fN = other stove fields)
    "f0":              (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, True,  None, None),
    # Stove POST_CONTROLS fields exposed by the firmware
    "stoveOnOff":      (None,       None,                              False, None, None),
    "stoveOpMode":     (None,       None,                              False, None, None),
    "stovePower":      (PERCENTAGE, None,                              False, None, None),
    "stoveTempTarget": (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, True,  None, None),
    # ESP32 system sensors — diagnostic
    "uptime":          (UnitOfTime.SECONDS, SensorDeviceClass.DURATION,         False, _D, SensorStateClass.TOTAL_INCREASING),
    "internalTemp":    (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, False, _D, None),
    "rssi":            (SIGNAL_STRENGTH_DECIBELS_MILLIWATT, SensorDeviceClass.SIGNAL_STRENGTH, False, _D, None),
    "firmware":        (None,       None,                              False, _D, None),
    "mac":             (None,       None,                              False, _D, None),
    "ip":              (None,       None,                              False, _D, None),
    "ssid":            (None,       None,                              False, _D, None),
}

# Keys exposed by /api/controls and handled by the climate entity
_SKIP_KEYS = {"onOff", "operatingMode", "heatingPower", "tempRoomTarget"}


def _is_primitive(value) -> bool:
    return isinstance(value, (str, int, float, bool)) or value is None


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: OpenFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors_data: dict = coordinator.data.get("sensors", {})
    entities = [
        OpenFirenetSensor(coordinator, entry, key)
        for key, value in sensors_data.items()
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
        info = KNOWN_SENSORS.get(key, (None, None, False, None, None))
        unit, device_class, self._divide_by_10, entity_category, self._state_class_override = info
        if key in KNOWN_SENSORS:
            self._attr_translation_key = key
        else:
            self._attr_name = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_entity_category = entity_category
        self._attr_unique_id = f"{entry.entry_id}_sensor_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self):
        raw = self.coordinator.data.get("sensors", {}).get(self._key)
        if not _is_primitive(raw):
            return None
        if self._divide_by_10:
            try:
                return float(raw) / 10
            except (TypeError, ValueError):
                return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return raw

    @property
    def state_class(self) -> SensorStateClass | None:
        if self._state_class_override is not None:
            return self._state_class_override
        if isinstance(self.native_value, float):
            return SensorStateClass.MEASUREMENT
        return None
