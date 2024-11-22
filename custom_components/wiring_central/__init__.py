"""WiringCentral Load Platform integration."""
import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
_LOGGER = logging.getLogger(__name__)


from .const import DOMAIN

PLATFORMS = ["sensor", "climate", "switch"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the BOM component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """WiringCentral controller/hub platform load."""

    _LOGGER.info("async_setup_entry: WiringCentral controller/hub platform load")
    print("platform config: ", entry.data)
    print("platform entry_id: ", entry.entry_id)
    hass_data = hass.data.setdefault(DOMAIN, {})
    hass_data[entry.entry_id] = {}

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
        _LOGGER.debug(f"async_setup_entry: loading: {component}")

    # hass.async_create_task(async_load_platform(hass=hass, component=CLIMATE_DOMAIN, platform=DOMAIN, discovered={}, hass_config=config))
    # hass.async_create_task(async_load_platform(hass=hass, component=SENSOR_DOMAIN, platform=DOMAIN, discovered={}, hass_config=config))
    # hass.async_create_task(async_load_platform(hass=hass, component=SWITCH_DOMAIN, platform=DOMAIN, discovered={}, hass_config=config))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info("async_unload_entry: unloading...")
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info("async_unload_entry: unloaded...")

    return unload_ok