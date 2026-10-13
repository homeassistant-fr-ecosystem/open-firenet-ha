"""The "Stove State" sensor gives a state key that Home Assistant translates (issue openfirenet/open-firenet#105)."""
import json
from pathlib import Path

from homeassistant.helpers import entity_registry as er

from custom_components.open_firenet.sensor import STOVE_STATES

COMPONENT = Path(__file__).parent.parent / "custom_components" / "open_firenet"


def _state(hass, entry):
    registry = er.async_get(hass)
    entity = next(e for e in er.async_entries_for_config_entry(registry, entry.entry_id) if e.unique_id == f"{entry.entry_id}_sensor_stove_state")
    return hass.states.get(entity.entity_id)


async def test_the_sensor_gives_the_key_and_lists_the_states(hass, bridge, setup_integration):
    state = _state(hass, setup_integration)
    assert state.state == bridge.state["stove"]["state"]
    assert state.attributes["options"] == STOVE_STATES


async def test_a_state_of_a_newer_firmware_is_unknown_not_an_error(hass, bridge, setup_integration):
    bridge.state["stove"]["state"] = "a_state_added_later"
    await hass.config_entries.async_reload(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert _state(hass, setup_integration).state == "unknown"


def test_every_state_is_named_in_every_language():
    for name in ("strings.json", "translations/en.json", "translations/fr.json", "translations/de.json", "translations/it.json"):
        names = json.loads((COMPONENT / name).read_text())["entity"]["sensor"]["stove_state"]["state"]
        assert sorted(names) == sorted(STOVE_STATES), name
        assert all(names.values()), name
