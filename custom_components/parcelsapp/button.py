from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ParcelsAppCoordinator

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the button platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ParcelsAppUpdateButton(coordinator)], True)

class ParcelsAppUpdateButton(ButtonEntity):
    """Representation of a Parcels App update button."""

    def __init__(self, coordinator: ParcelsAppCoordinator) -> None:
        """Initialize the button."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_update_tracking"
        self._attr_name = "Update Parcels App Tracking"
        self._attr_icon = "mdi:truck-delivery"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.update_tracked_packages()
