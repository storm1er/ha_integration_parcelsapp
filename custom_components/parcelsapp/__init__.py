from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SERVICE_TRACK_PACKAGE, SERVICE_REMOVE_PACKAGE, SERVICE_PRUNE_PACKAGES
from .coordinator import ParcelsAppCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = ParcelsAppCoordinator(hass, entry)
    await coordinator.async_init()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_track_package(call: ServiceCall) -> None:
        tracking_id = call.data["tracking_id"]
        name = call.data.get("name")
        zipcode = call.data.get("zipcode")
        await coordinator.track_package(tracking_id, name, zipcode)

        # Notify sensor platform to add the new entity
        async_dispatcher_send(hass, f"{DOMAIN}_new_package", tracking_id)

    hass.services.async_register(DOMAIN, SERVICE_TRACK_PACKAGE, handle_track_package)

    async def handle_remove_package(call: ServiceCall) -> None:
        tracking_id = call.data["tracking_id"]
        await coordinator.remove_package(tracking_id)

        # Notify sensor platform to remove the entity
        async_dispatcher_send(hass, f"{DOMAIN}_remove_package", tracking_id)

    hass.services.async_register(DOMAIN, SERVICE_REMOVE_PACKAGE, handle_remove_package)

    async def handle_prune_packages(call: ServiceCall) -> None:
        pruned_packages = await coordinator.prune_packages()
        
        # Notify sensor platform to remove entities for each pruned package
        for tracking_id in pruned_packages:
            async_dispatcher_send(hass, f"{DOMAIN}_remove_package", tracking_id)

    hass.services.async_register(DOMAIN, SERVICE_PRUNE_PACKAGES, handle_prune_packages)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Disconnect dispatcher listeners
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        unsub_dispatchers = hass.data[DOMAIN].pop(entry.entry_id + "_unsub_dispatcher", [])
        for unsub in unsub_dispatchers:
            unsub()
    return unload_ok
