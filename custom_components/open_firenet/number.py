from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BAKE_TEMP_MAX,
    BAKE_TEMP_MIN,
    BAKE_TEMP_STEP,
    DOMAIN,
    FROST_TEMP_MAX,
    FROST_TEMP_MIN,
    FROST_TEMP_STEP,
    HEATING_POWER_MAX,
    HEATING_POWER_MIN,
    HEATING_POWER_STEP,
    MULTIAIR_TRIM_MAX,
    MULTIAIR_TRIM_MIN,
    MULTIAIR_TRIM_STEP,
    ROOM_OFFSET_MAX,
    ROOM_OFFSET_MIN,
    ROOM_OFFSET_STEP,
    SETBACK_TEMP_MAX,
    SETBACK_TEMP_MIN,
    SETBACK_TEMP_STEP,
    get_model_name,
    is_bake_supported,
    is_multiair_supported,
    CONF_MULTIAIR,
)
from .coordinator import OpenFirenetCoordinator


@dataclass(frozen=True, kw_only=True)
class OpenFirenetNumberDescription(NumberEntityDescription):
    value_fn: Callable[[dict[str, Any]], float | None]
    set_fn: Callable[[OpenFirenetCoordinator, float], Any]


NUMBER_TYPES: tuple[OpenFirenetNumberDescription, ...] = (
    # The power setting, used by the stove in manual and automatic modes (issue #43). The thermostat entity also
    # offers it, as its "fan mode", which nobody looks for.
    OpenFirenetNumberDescription(
        key="heating_power",
        name="Heating Power",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=HEATING_POWER_MIN,
        native_max_value=HEATING_POWER_MAX,
        native_step=HEATING_POWER_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:fire",
        value_fn=lambda data: data.get("controls", {}).get("power_percent"),
        set_fn=lambda coord, val: coord.async_set_controls(power_percent=int(val)),
    ),
    OpenFirenetNumberDescription(
        key="setback_temperature",
        name="Setback Temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=SETBACK_TEMP_MIN,
        native_max_value=SETBACK_TEMP_MAX,
        native_step=SETBACK_TEMP_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:thermometer-chevron-down",
        value_fn=lambda data: data.get("controls", {}).get(
            "setback_temperature",
            (
                data.get("controls", {}).get("setBackTemp", 160) / 10.0
                if "setBackTemp" in data.get("controls", {})
                else 16.0
            ),
        ),
        set_fn=lambda coord, val: coord.async_set_controls(
            setback_temperature=float(val)
        ),
    ),
    OpenFirenetNumberDescription(
        key="frost_protection_temperature",
        name="Frost Protection Temperature",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=FROST_TEMP_MIN,
        native_max_value=FROST_TEMP_MAX,
        native_step=FROST_TEMP_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:snowflake-thermometer",
        value_fn=lambda data: data.get("controls", {}).get(
            "frost_protection_temperature",
            (
                data.get("controls", {}).get("frostProtectionTemp", 50) / 10.0
                if "frostProtectionTemp" in data.get("controls", {})
                else (
                    data.get("controls_pos", [])[30] / 10.0
                    if len(data.get("controls_pos", [])) > 30 and data.get("controls_pos", [])[30] > 0
                    else 5.0
                )
            ),
        ),
        set_fn=lambda coord, val: coord.async_set_controls(
            frostProtectionTemp=float(val)
        ),
    ),
    OpenFirenetNumberDescription(
        key="room_temperature_offset",
        name="Room Temperature Offset",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=ROOM_OFFSET_MIN,
        native_max_value=ROOM_OFFSET_MAX,
        native_step=ROOM_OFFSET_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:thermometer-lines",
        value_fn=lambda data: data.get("controls", {}).get(
            "room_temperature_offset",
            (
                data.get("controls", {}).get("roomTempOffset", 0) / 10.0
                if "roomTempOffset" in data.get("controls", {})
                else (
                    data.get("controls_pos", [])[31] / 10.0
                    if len(data.get("controls_pos", [])) > 31
                    else 0.0
                )
            ),
        ),
        set_fn=lambda coord, val: coord.async_set_controls(
            room_temperature_offset=float(val)
        ),
    ),
)

MULTIAIR_NUMBER_TYPES: tuple[OpenFirenetNumberDescription, ...] = (
    OpenFirenetNumberDescription(
        key="multiair_1_area",
        name="MultiAir 1 Convection Trim",
        native_unit_of_measurement="%",
        native_min_value=MULTIAIR_TRIM_MIN,
        native_max_value=MULTIAIR_TRIM_MAX,
        native_step=MULTIAIR_TRIM_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:fan-chevron-up",
        value_fn=lambda data: data.get("controls", {}).get(
            "convection_fan1_area",
            data.get("controls", {}).get("convectionFan1Area", 0),
        ),
        set_fn=lambda coord, val: coord.async_set_controls(
            convectionFan1Area=int(val)
        ),
    ),
    OpenFirenetNumberDescription(
        key="multiair_2_area",
        name="MultiAir 2 Convection Trim",
        native_unit_of_measurement="%",
        native_min_value=MULTIAIR_TRIM_MIN,
        native_max_value=MULTIAIR_TRIM_MAX,
        native_step=MULTIAIR_TRIM_STEP,
        mode=NumberMode.SLIDER,
        icon="mdi:fan-chevron-up",
        value_fn=lambda data: data.get("controls", {}).get(
            "convection_fan2_area",
            data.get("controls", {}).get("convectionFan2Area", 0),
        ),
        set_fn=lambda coord, val: coord.async_set_controls(
            convectionFan2Area=int(val)
        ),
    ),
)

BAKE_NUMBER_TYPE = OpenFirenetNumberDescription(
    key="bake_target_temperature",
    name="Bake Target Temperature",
    device_class=NumberDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    native_min_value=BAKE_TEMP_MIN,
    native_max_value=BAKE_TEMP_MAX,
    native_step=BAKE_TEMP_STEP,
    mode=NumberMode.SLIDER,
    icon="mdi:toaster-oven",
    value_fn=lambda data: data.get("controls", {}).get(
        "bake_target_temperature",
        (
            data.get("controls", {}).get("bakeTarget", 180)
            if "bakeTarget" in data.get("controls", {})
            else (
                data.get("controls_pos", [])[5]
                if len(data.get("controls_pos", [])) > 5 and data.get("controls_pos", [])[5] > 0
                else 180
            )
        ),
    ),
    set_fn=lambda coord, val: coord.async_set_controls(
        bakeTarget=int(val)
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: OpenFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [OpenFirenetNumber(coordinator, entry, desc) for desc in NUMBER_TYPES]

    if is_multiair_supported(coordinator.data, entry.options.get(CONF_MULTIAIR, False)):
        entities.extend(
            [
                OpenFirenetNumber(coordinator, entry, desc)
                for desc in MULTIAIR_NUMBER_TYPES
            ]
        )

    if is_bake_supported(coordinator.data):
        entities.append(OpenFirenetNumber(coordinator, entry, BAKE_NUMBER_TYPE))

    async_add_entities(entities)


class OpenFirenetNumber(CoordinatorEntity[OpenFirenetCoordinator], NumberEntity):
    """Number entity for Open Firenet controllable ranges."""

    entity_description: OpenFirenetNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OpenFirenetCoordinator,
        entry: ConfigEntry,
        description: OpenFirenetNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_translation_key = description.key
        self._attr_unique_id = f"{entry.entry_id}_number_{description.key}"

    @property
    def device_info(self) -> dict:
        device = self.coordinator.data.get("device", {})
        stove = self.coordinator.data.get("stove", {})
        model_name = stove.get("model_name") or get_model_name(stove.get("model"))
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": device.get("name", "Open Firenet"),
            "manufacturer": "Open Firenet",
            "model": f"RIKA {model_name}",
            "sw_version": f"Firmware v{device.get('version', '2.0.0')} (MB {stove.get('mainboard_version') or '?'})",
            "configuration_url": f"http://{self.coordinator.host}",
        }

    @property
    def native_value(self) -> float | None:
        val = self.entity_description.value_fn(self.coordinator.data)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        return None

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.set_fn(self.coordinator, value)
