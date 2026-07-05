from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FirenetData, OpenFirenetClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class OpenFirenetCoordinator(DataUpdateCoordinator[FirenetData]):
    def __init__(self, hass: HomeAssistant, host: str, scan_interval: int) -> None:
        self.host = host
        self._client = OpenFirenetClient(host)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> FirenetData:
        try:
            async with asyncio.timeout(10):
                return await self._client.fetch_all()
        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Timeout connecting to {self.host}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with {self.host}: {err}") from err

    async def async_set_controls(self, **kwargs) -> None:
        new_controls = self.data.controls.replace(**kwargs)
        await self._client.set_controls(new_controls)
        # Optimistic update: reflect the change immediately in the UI
        # without waiting for the next poll cycle.
        self.async_set_updated_data(replace(self.data, controls=new_controls))
