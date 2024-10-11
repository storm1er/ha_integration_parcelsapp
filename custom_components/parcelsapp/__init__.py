from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SERVICE_TRACK_PACKAGE
from .coordinator import ParcelsAppCoordinator
from .sensor import ParcelsAppTrackingSensor

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = ParcelsAppCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_track_package(call: ServiceCall) -> None:
        tracking_id = call.data["tracking_id"]
        await coordinator.track_package(tracking_id)

        # Create and add new sensor
        async_add_entities = hass.data[DOMAIN][entry.entry_id + "_add_entities"]
        new_sensor = ParcelsAppTrackingSensor(coordinator, tracking_id)
        async_add_entities([new_sensor], True)

    hass.services.async_register(DOMAIN, SERVICE_TRACK_PACKAGE, handle_track_package)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
