[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

# ParcelsApp Integration for Home Assistant

A Home Assistant integration for [ParcelsApp.com](https://parcelsapp.com/), a universal parcel tracking service.

## Features

### Binary Sensor

| Sensor             | Description                                              |
| ------------------ | -------------------------------------------------------- |
| Parcels App Status | Monitors the availability of the ParcelsApp.com website  |

### Button

| Button                       | Description                                                     |
| ---------------------------- | --------------------------------------------------------------- |
| Update Parcels App Tracking  | Updates all parcels not marked as delivered or archived         |

### Service

The integration provides a service called `parcelsapp.track_package`:

| Argument    | Required | Description                                                      |
| ----------- | -------- | ---------------------------------------------------------------- |
| tracking_id | Yes      | The parcel's tracking ID provided by your parcel/delivery company|
| name        | No       | An optional name for your parcel (used as the sensor name)       |

### Tracking Sensor

The `track_package` service creates a sensor for each tracked package with the following attributes:

| Attribute       | Description                                                        |
| --------------- | ------------------------------------------------------------------ |
| status          | Current state (archived, delivered, transit, arrived, pickup)      |
| uuid            | UUID used by the ParcelsApp API                                    |
| message         | Latest update message from the delivery company                    |
| origin          | Country of departure                                               |
| carrier         | Delivery company name                                              |
| days_in_transit | Number of days between transit and delivery                        |
| last_updated    | Timestamp of the latest check by the integration                   |

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=storm1er&repository=ha_integration_parcelsapp&category=Integration)

1. Add this GitHub repository to HACS as a custom repository, or click the badge above.
2. Install the "Parcels App" integration via HACS.
3. Restart Home Assistant.
4. Add the integration via the Home Assistant UI (Configuration > Integrations > Add Integration > Parcels App).

## Configuration

During setup, you'll need to provide:

1. Your ParcelsApp API key (obtainable from [parcelsapp.com/dashboard](https://parcelsapp.com/dashboard))
2. Your destination country (the name of your country in your native language)

## Usage

After configuration, you can use the `parcelsapp.track_package` service to add new packages for tracking. Each tracked package will create a new sensor entity in Home Assistant.

## Contributing

Contributions to this integration are welcome! Please follow these guidelines:

1. Use descriptive commit messages and add context to your changes.
2. Test your changes thoroughly before submitting a pull request.
3. Update documentation (including this README) if your changes affect user-facing features or setup.

If you find this integration valuable and want to support it in other ways, you can [buy me a coffee](https://www.paypal.com/paypalme/quentindecaunes).