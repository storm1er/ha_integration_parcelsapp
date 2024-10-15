from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ParcelsAppCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for tracking_id, package_data in coordinator.tracked_packages.items():
        sensor = ParcelsAppTrackingSensor(coordinator, tracking_id, package_data.get("name"))
        entities.append(sensor)
    async_add_entities(entities, True)

    # Store a reference to the added entities
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id + "_entities"] = entities

    # Listen for new packages to add
    async def handle_new_package(tracking_id: str):
        package_data = coordinator.tracked_packages.get(tracking_id)
        if package_data:
            new_sensor = ParcelsAppTrackingSensor(coordinator, tracking_id, package_data.get("name"))
            async_add_entities([new_sensor], True)
            # Add to entities list
            hass.data[DOMAIN][entry.entry_id + "_entities"].append(new_sensor)

    # Listen for packages to remove
    async def handle_remove_package(tracking_id: str):
        entities = hass.data[DOMAIN][entry.entry_id + "_entities"]
        entity_to_remove = None
        for entity in entities:
            if entity.tracking_id == tracking_id:
                entity_to_remove = entity
                break
        if entity_to_remove:
            await entity_to_remove.async_remove()
            entities.remove(entity_to_remove)

            # Remove entity from entity registry
            entity_registry = er.async_get(hass)
            entity_id = entity_to_remove.entity_id
            if entity_registry.async_is_registered(entity_id):
                entity_registry.async_remove(entity_id)

    unsub_new_package = async_dispatcher_connect(
        hass, f"{DOMAIN}_new_package", handle_new_package
    )
    unsub_remove_package = async_dispatcher_connect(
        hass, f"{DOMAIN}_remove_package", handle_remove_package
    )

    # Store unsub functions to clean up later
    hass.data[DOMAIN][entry.entry_id + "_unsub_dispatcher"] = [unsub_new_package, unsub_remove_package]


class ParcelsAppTrackingSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Parcels App tracking sensor."""

    def __init__(self, coordinator: ParcelsAppCoordinator, tracking_id: str, name: str = None) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.tracking_id = tracking_id
        self._attr_unique_id = f"tracking_{tracking_id}"
        stored_name = self.coordinator.tracked_packages.get(tracking_id, {}).get("name")
        self.name = name or stored_name or f"Parcel {tracking_id}"

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        if self.tracking_id in self.coordinator.tracked_packages:
            return self.coordinator.tracked_packages[self.tracking_id].get("status")
        return None

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        status = self.state
        if status == "delivered":
            return "mdi:package-variant"
        elif status == "pickup":
            return "mdi:package-variant-closed-check"
        else:
            return "mdi:package-variant-closed"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        if self.tracking_id in self.coordinator.tracked_packages:
            attributes = self.coordinator.tracked_packages[self.tracking_id].copy()
            # Convert last_updated to a more readable format
            if 'last_updated' in attributes:
                attributes['last_updated'] = attributes['last_updated'].replace('T', ' ')
            attributes['tracking_id'] = self.tracking_id
            return attributes
        return {}

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.tracking_id in self.coordinator.tracked_packages
        )
