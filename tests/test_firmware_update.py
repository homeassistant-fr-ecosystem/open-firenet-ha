"""The firmware update entity only tells that a newer firmware is published; it never installs."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.components.update import UpdateEntityFeature
from homeassistant.helpers import entity_registry as er

from custom_components.open_firenet.const import DOMAIN

FETCH = "custom_components.open_firenet.update.async_fetch_latest_release"


async def _setup(hass, bridge, release):
    from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: bridge.host, CONF_SCAN_INTERVAL: 300})
    entry.add_to_hass(hass)
    with patch(FETCH, return_value=release):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def _entity_id(hass, entry):
    return er.async_get(hass).async_get_entity_id("update", DOMAIN, f"{entry.entry_id}_update_firmware")


async def test_newer_release_is_announced(hass, bridge):
    release = {"version": "4.0.0", "url": "https://example.org/r", "notes": "New things"}
    entry = await _setup(hass, bridge, release)

    state = hass.states.get(_entity_id(hass, entry))
    assert state.state == "on"
    assert state.attributes["installed_version"] == "2.1.0"
    assert state.attributes["latest_version"] == "4.0.0"
    assert state.attributes["release_url"] == "https://example.org/r"
    # Notification only: no install feature.
    assert not state.attributes["supported_features"] & UpdateEntityFeature.INSTALL


async def test_same_release_is_up_to_date(hass, bridge):
    entry = await _setup(hass, bridge, {"version": "2.1.0", "url": "https://example.org/r", "notes": ""})
    assert hass.states.get(_entity_id(hass, entry)).state == "off"


async def test_github_unreachable_claims_nothing(hass, bridge):
    entry = await _setup(hass, bridge, None)
    assert hass.states.get(_entity_id(hass, entry)).state == "off"
