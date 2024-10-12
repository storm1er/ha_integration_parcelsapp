from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .coordinator import ParcelsAppCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Add existing tracked packages
    entities = []
    for tracking_id, package_data in coordinator.tracked_packages.items():
        entities.append(ParcelsAppTrackingSensor(coordinator, tracking_id, package_data.get("name")))
    async_add_entities(entities, True)

    # Listen for new packages to add
    async def handle_new_package(tracking_id: str):
        package_data = coordinator.tracked_packages.get(tracking_id)
        if package_data:
            new_sensor = ParcelsAppTrackingSensor(coordinator, tracking_id, package_data.get("name"))
            async_add_entities([new_sensor], True)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id + "_unsub_dispatcher"] = async_dispatcher_connect(
        hass, f"{DOMAIN}_new_package", handle_new_package
    )

class ParcelsAppTrackingSensor(SensorEntity):
    """Representation of a Parcels App tracking sensor."""

    def __init__(self, coordinator: ParcelsAppCoordinator, tracking_id: str, name: str = None) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.tracking_id = tracking_id
        self._attr_unique_id = f"{DOMAIN}_tracking_{tracking_id}"
        stored_name = self.coordinator.tracked_packages.get(tracking_id, {}).get("name")
        self._attr_name = name or stored_name or f"Parcel {tracking_id}"

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
            return attributes
        return {}

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.tracking_id in self.coordinator.tracked_packages
        )

    async def async_update(self) -> None:
        """Update the entity."""
        await self.coordinator.async_request_refresh()
