from datetime import datetime, timedelta
import logging
import time
import json
import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import Store

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class ParcelsAppCoordinator(DataUpdateCoordinator):
    """Custom coordinator for Parcels App."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api_key = entry.data["api_key"]
        self.destination_country = entry.data["destination_country"]
        self.session = aiohttp.ClientSession()
        self.tracked_packages = {}
        self.store = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}_tracked_packages")
        # Get the first two letters of the language code
        language_code = (hass.config.language or 'en')[:2].lower()
        self.language = language_code

    async def async_init(self):
        """Initialize the coordinator."""
        await self._load_tracked_packages()

    async def _load_tracked_packages(self):
        """Load tracked packages from persistent storage."""
        stored_data = await self.store.async_load()
        if stored_data:
            # Convert uuid_timestamp back to datetime if it's stored as string
            for package in stored_data.values():
                if 'uuid_timestamp' in package and isinstance(package['uuid_timestamp'], str):
                    package['uuid_timestamp'] = datetime.fromisoformat(package['uuid_timestamp'])
            self.tracked_packages = stored_data
        else:
            self.tracked_packages = {}

    async def _save_tracked_packages(self):
        """Save tracked packages to persistent storage."""
        # Convert uuid_timestamp to ISO format string before saving
        for package in self.tracked_packages.values():
            if 'uuid_timestamp' in package and isinstance(package['uuid_timestamp'], datetime):
                package['uuid_timestamp'] = package['uuid_timestamp'].isoformat()
        await self.store.async_save(self.tracked_packages)
        await self.async_request_refresh()

    async def track_package(self, tracking_id: str, name: str = None) -> None:
        """Track a new package or update an existing one."""
        url = "https://parcelsapp.com/api/v3/shipments/tracking"
        payload = json.dumps(
            {
                "shipments": [
                    {
                        "trackingId": tracking_id,
                        "destinationCountry": self.destination_country,
                    }
                ],
                "language": self.language,
                "apiKey": self.api_key,
            }
        )
        headers = {"Content-Type": "application/json"}

        try:
            async with self.session.post(
                url, headers=headers, data=payload
            ) as response:
                response_text = await response.text()
                response.raise_for_status()
                data = json.loads(response_text)

                if "uuid" in data:
                    # New tracking request
                    package_data = {
                        "status": "pending",
                        "uuid": data["uuid"],
                        "uuid_timestamp": datetime.now(),
                        "message": "Tracking initiated",
                        "last_updated": datetime.now().isoformat(),
                        "name": name or self.tracked_packages.get(tracking_id, {}).get("name"),
                    }
                    self.tracked_packages[tracking_id] = package_data
                elif "shipments" in data and data["shipments"]:
                    # Already tracked parcel
                    shipment = data["shipments"][0]
                    package_data = {
                        "status": shipment.get("status", "unknown"),
                        "uuid": None,
                        "uuid_timestamp": None,
                        "message": shipment.get("lastState", {}).get(
                            "status", "No status available"
                        ),
                        "location": shipment.get("lastState", {}).get("location", "undefined"),
                        "origin": shipment.get("origin"),
                        "carrier": shipment.get("detectedCarrier", {}).get("name"),
                        "days_in_transit": next(
                            (
                                attr["val"]
                                for attr in shipment.get("attributes", [])
                                if attr["l"] == "days_transit"
                            ),
                            None,
                        ),
                        "last_updated": datetime.now().isoformat(),
                        "name": name or self.tracked_packages.get(tracking_id, {}).get("name"),
                    }
                    self.tracked_packages[tracking_id] = package_data
                else:
                    _LOGGER.error(
                        f"Unexpected API response for tracking ID {tracking_id}. Response: {response_text}"
                    )
                    return
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error tracking package {tracking_id}: {err}")
        except json.JSONDecodeError:
            _LOGGER.error(
                f"Failed to parse API response for tracking ID {tracking_id}. Response: {response_text}"
            )
        await self._save_tracked_packages()

    async def remove_package(self, tracking_id: str) -> None:
        """Remove a package from tracking."""
        if tracking_id in self.tracked_packages:
            del self.tracked_packages[tracking_id]
            await self._save_tracked_packages()
        else:
            _LOGGER.warning(f"Tracking ID {tracking_id} not found in tracked packages.")

    async def update_package(self, tracking_id: str, uuid: str | None, uuid_timestamp: datetime | None) -> None:
        """Update a single package."""
        # Check if UUID is expired
        uuid_expired = False
        if uuid_timestamp:
            time_since_uuid = datetime.now() - uuid_timestamp
            if time_since_uuid > timedelta(minutes=30):
                uuid_expired = True
                _LOGGER.debug(f"UUID for {tracking_id} is expired.")
        else:
            uuid_expired = True  # No UUID timestamp means we need a new UUID

        if uuid_expired or not uuid:
            # Re-initiate tracking to get a new UUID
            await self.track_package(tracking_id)
            return

        url = f"https://parcelsapp.com/api/v3/shipments/tracking?uuid={uuid}&apiKey={self.api_key}&language={self.language}"

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("done") and data.get("shipments"):
                    shipment = data["shipments"][0]
                    existing_name = self.tracked_packages.get(tracking_id, {}).get("name")
                    package_data = {
                        "status": shipment.get("status", "unknown"),
                        "uuid": None,  # UUID is no longer needed after data is retrieved
                        "uuid_timestamp": None,
                        "message": shipment.get("lastState", {}).get(
                            "status", "No status available"
                        ),
                        "location": shipment.get("lastState", {}).get("location", "undefined"),
                        "origin": shipment.get("origin"),
                        "destination": shipment.get("destination"),
                        "carrier": shipment.get("detectedCarrier", {}).get("name"),
                        "days_in_transit": next(
                            (
                                attr["val"]
                                for attr in shipment.get("attributes", [])
                                if attr["l"] == "days_transit"
                            ),
                            None,
                        ),
                        "last_updated": datetime.now().isoformat(),
                        "name": existing_name,
                    }
                    self.tracked_packages[tracking_id] = package_data
                else:
                    _LOGGER.debug(f"Tracking data not yet available for {tracking_id}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error updating package {tracking_id}: {err}")
        await self._save_tracked_packages()

    async def update_tracked_packages(self) -> None:
        """Update all tracked packages."""
        for tracking_id, package_data in self.tracked_packages.items():
            if package_data.get("status") not in ["delivered", "archived"]:
                await self.update_package(
                    tracking_id,
                    package_data.get("uuid"),
                    package_data.get("uuid_timestamp"),
                )

    async def _async_update_data(self):
        """Fetch data from API endpoint and update tracked packages."""
        # First, update the Parcels App status
        status_data = await self._fetch_parcels_app_status()

        # Then, update all tracked packages
        await self.update_tracked_packages()

        # Combine the status data with tracked packages data
        return {
            "parcels_app_status": status_data,
            "tracked_packages": self.tracked_packages,
        }

    async def _fetch_parcels_app_status(self):
        """Fetch Parcels App status."""
        try:
            start_time = time.time()
            async with async_timeout.timeout(10):
                async with self.session.get("https://parcelsapp.com/") as response:
                    await response.text()  # Ensure the response is fully received
                    response.raise_for_status()
                    end_time = time.time()
                    response_time = end_time - start_time
                    return {
                        "status": response.status == 200,
                        "response_time": response_time,
                        "response_code": response.status,
                    }
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
