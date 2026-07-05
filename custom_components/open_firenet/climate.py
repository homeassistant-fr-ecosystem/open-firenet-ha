from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import FirenetControls
from .const import (
    DOMAIN,
    HEATING_POWER_MAX,
    HEATING_POWER_MIN,
    OPERATING_MODES,
    OPERATING_MODES_REVERSE,
    ROOM_TEMP_KEYS,
    TEMP_MAX,
    TEMP_MIN,
    TEMP_STEP,
)
from .coordinator import OpenFirenetCoordinator

FAN_MODES = [str(p) for p in range(HEATING_POWER_MIN, HEATING_POWER_MAX + 1, 10)]
PRESET_MODES = list(OPERATING_MODES.values())


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: OpenFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OpenFirenetClimate(coordinator, entry)])


class OpenFirenetClimate(CoordinatorEntity[OpenFirenetCoordinator], ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_preset_modes = PRESET_MODES
    _attr_fan_modes = FAN_MODES
    _attr_min_temp = TEMP_MIN
    _attr_max_temp = TEMP_MAX
    _attr_target_temperature_step = TEMP_STEP
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: OpenFirenetCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Open Firenet",
            "manufacturer": "Open Firenet",
            "model": "Rika WiFi Bridge",
            "configuration_url": f"http://{coordinator.host}",
        }

    @property
    def _controls(self) -> FirenetControls:
        return self.coordinator.data.controls

    @property
    def current_temperature(self) -> float | None:
        sensors = self.coordinator.data.sensors
        for key in ROOM_TEMP_KEYS:
            raw = sensors.get(key)
            if raw is not None:
                try:
                    return float(raw) / 10
                except (TypeError, ValueError):
                    pass
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.HEAT if self._controls.on_off == 1 else HVACMode.OFF

    @property
    def preset_mode(self) -> str | None:
        return OPERATING_MODES.get(self._controls.operating_mode)

    @property
    def target_temperature(self) -> float | None:
        return self._controls.temp_room_target / 10

    @property
    def fan_mode(self) -> str | None:
        return str(self._controls.heating_power)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        await self.coordinator.async_set_controls(onOff=1 if hvac_mode == HVACMode.HEAT else 0)

    async def async_turn_on(self) -> None:
        await self.coordinator.async_set_controls(onOff=1)

    async def async_turn_off(self) -> None:
        await self.coordinator.async_set_controls(onOff=0)

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            await self.coordinator.async_set_controls(tempRoomTarget=int(temp * 10))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        mode_int = OPERATING_MODES_REVERSE.get(preset_mode)
        if mode_int is not None:
            await self.coordinator.async_set_controls(operatingMode=mode_int)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self.coordinator.async_set_controls(heatingPower=int(fan_mode))
