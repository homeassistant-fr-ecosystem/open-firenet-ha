"""A state that carries a byte which is not valid UTF-8 (issue #38)."""
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.data_entry_flow import FlowResultType

from custom_components.open_firenet.const import DOMAIN


async def test_the_integration_can_be_added(hass, bridge):
    bridge.invalid_utf8 = True

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: bridge.host, CONF_SCAN_INTERVAL: 300}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]
    # The state is read and the entities get their values.
    assert hass.data[DOMAIN][entry.entry_id].data["stove"]["model_name"]
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_the_state_keeps_being_read(hass, bridge, setup_integration):
    entry = setup_integration
    coordinator = hass.data[DOMAIN][entry.entry_id]
    bridge.invalid_utf8 = True

    await coordinator.async_refresh()

    assert coordinator.last_update_success
    assert coordinator.data["status"]["ssid"] == "\ufffd"  # the bad byte, replaced
