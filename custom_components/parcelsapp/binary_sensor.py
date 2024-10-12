"""Binary sensor platform for parcelsapp."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ParcelsAppCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ParcelsAppBinarySensor(coordinator)], True)


class ParcelsAppBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Parcels App binary sensor."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: ParcelsAppCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_status"
        self._attr_name = "Parcels App Status"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data and "parcels_app_status" in self.coordinator.data:
            return self.coordinator.data["parcels_app_status"]["status"]
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        if self.coordinator.data and "parcels_app_status" in self.coordinator.data:
            status_data = self.coordinator.data["parcels_app_status"]
            return {
                "response_time": status_data["response_time"],
                "response_code": status_data["response_code"],
            }
        return {}
