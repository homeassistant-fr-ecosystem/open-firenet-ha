from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import aiohttp

from .const import API_CONTROLS, API_SENSORS, API_STATUS


@dataclass
class FirenetControls:
    on_off: int
    operating_mode: int
    heating_power: int
    temp_room_target: int

    @classmethod
    def from_dict(cls, data: dict) -> FirenetControls:
        return cls(
            on_off=int(data.get("onOff", 0)),
            operating_mode=int(data.get("operatingMode", 2)),
            heating_power=int(data.get("heatingPower", 30)),
            temp_room_target=int(data.get("tempRoomTarget", 200)),
        )

    def as_post_body(self) -> str:
        return (
            f"onOff={self.on_off}; "
            f"operatingMode={self.operating_mode}; "
            f"heatingPower={self.heating_power}; "
            f"tempRoomTarget={self.temp_room_target};"
        )

    def replace(self, **kwargs) -> FirenetControls:
        return FirenetControls(
            on_off=kwargs.get("onOff", self.on_off),
            operating_mode=kwargs.get("operatingMode", self.operating_mode),
            heating_power=kwargs.get("heatingPower", self.heating_power),
            temp_room_target=kwargs.get("tempRoomTarget", self.temp_room_target),
        )


@dataclass
class FirenetData:
    sensors: dict[str, Any]
    controls: FirenetControls


class OpenFirenetClient:
    def __init__(self, host: str) -> None:
        self._base = f"http://{host}"
        self._session: aiohttp.ClientSession | None = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def async_validate(self) -> bool:
        data = await self._get(API_STATUS)
        return "mainLoop" in data

    async def fetch_all(self) -> FirenetData:
        sensors_raw, controls_raw = await asyncio.gather(
            self._get(API_SENSORS),
            self._get(API_CONTROLS),
        )
        return FirenetData(
            sensors=sensors_raw,
            controls=FirenetControls.from_dict(controls_raw),
        )

    async def set_controls(self, controls: FirenetControls) -> None:
        async with self._get_session().post(
            f"{self._base}{API_CONTROLS}",
            data=controls.as_post_body(),
            headers={"Content-Type": "text/plain"},
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            resp.raise_for_status()

    async def _get(self, path: str) -> dict:
        async with self._get_session().get(f"{self._base}{path}") as resp:
            resp.raise_for_status()
            return await resp.json()
