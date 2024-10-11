"""DataUpdateCoordinator for parcelsapp."""

from __future__ import annotations

from datetime import timedelta
import logging
import time
import json

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ParcelsAppCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize my coordinator."""
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

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
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

    async def track_package(self, tracking_id: str) -> None:
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
                "language": "en",
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
                    self.tracked_packages[tracking_id] = {
                        "status": "pending",
                        "uuid": data["uuid"],
                        "message": "Tracking initiated",
                    }
                elif "shipments" in data and data["shipments"]:
                    # Already tracked parcel
                    shipment = data["shipments"][0]
                    self.tracked_packages[tracking_id] = {
                        "status": shipment.get("status", "unknown"),
                        "uuid": None,
                        "message": shipment.get("lastState", {}).get(
                            "status", "No status available"
                        ),
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
                    }
                else:
                    _LOGGER.error(
                        f"Unexpected API response for tracking ID {tracking_id}. Response: {response_text}"
                    )
                    return

                await self.async_request_refresh()
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error tracking package {tracking_id}: {err}")
        except json.JSONDecodeError:
            _LOGGER.error(
                f"Failed to parse API response for tracking ID {tracking_id}. Response: {response_text}"
            )

    async def update_package(self, tracking_id: str, uuid: str | None) -> None:
        """Update a single package."""
        if uuid is None:
            # For packages without UUID, we need to use the track_package method again
            await self.track_package(tracking_id)
            return

        url = f"https://parcelsapp.com/api/v3/shipments/tracking?uuid={uuid}&apiKey={self.api_key}"

        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("done") and data.get("shipments"):
                    shipment = data["shipments"][0]
                    self.tracked_packages[tracking_id] = {
                        "status": shipment.get("status", "unknown"),
                        "uuid": uuid,
                        "message": shipment.get("lastState", {}).get(
                            "status", "No status available"
                        ),
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
                    }
                else:
                    _LOGGER.debug(f"Tracking data not yet available for {tracking_id}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Error updating package {tracking_id}: {err}")

    async def update_tracked_packages(self) -> None:
        """Update all tracked packages."""
        for tracking_id, package_data in self.tracked_packages.items():
            if package_data.get("status") not in ["delivered", "archived"]:
                await self.update_package(tracking_id, package_data["uuid"])
        await self.async_request_refresh()

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
