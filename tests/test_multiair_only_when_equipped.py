"""The MultiAir entities exist only for an equipped stove (issue #33)."""
from homeassistant.helpers import entity_registry as er

from custom_components.open_firenet.const import CONF_MULTIAIR


def _multiair(hass, entry):
    registry = er.async_get(hass)
    return sorted(
        e.unique_id.replace(entry.entry_id + "_", "")
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if "multiair" in e.unique_id
    )


ALL = ["fan_multiair_1", "fan_multiair_2", "number_multiair_1_area", "number_multiair_2_area"]


async def test_a_model_sold_with_multiair_has_them(hass, bridge, setup_integration):
    assert _multiair(hass, setup_integration) == ALL  # the fixture is a DOMO


async def test_another_model_loses_them_and_gets_them_back_with_the_option(hass, bridge, setup_integration):
    entry = setup_integration
    # The same installation, now seen as a REVO II (model 20): the bridge still reports the fan values.
    bridge.state["stove"]["model"] = 20
    bridge.state["stove"]["model_name"] = "REVO II"
    assert "convection_fan1_active" in bridge.state["controls"]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    # The entities an earlier version created are removed, not left behind as unavailable.
    assert _multiair(hass, entry) == []

    # The owner says the stove has MultiAir: they come back.
    hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_MULTIAIR: True})
    await hass.async_block_till_done()
    assert _multiair(hass, entry) == ALL


async def test_the_schedule_entities_survive_a_restart(hass, bridge, setup_integration, caplog):
    entry = setup_integration
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert "Removing orphaned" not in caplog.text
