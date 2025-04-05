[![version](https://img.shields.io/github/v/release/dm82m/hass-deltasol-km2?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2)
[![downloads_total](https://img.shields.io/github/downloads/dm82m/hass-deltasol-km2/total?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2/releases)
[![downloads_latest](https://img.shields.io/github/downloads/dm82m/hass-deltasol-km2/latest/total?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2/releases)
[![maintained](https://img.shields.io/maintenance/yes/2025?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2)
[![license](https://img.shields.io/github/license/dm82m/hass-deltasol-km2.svg?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2/blob/master/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![buy_me_a_coffee](https://img.shields.io/badge/If%20you%20like%20it-Buy%20me%20a%20coffee-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/dirkmaucher)
[![paypal](https://img.shields.io/badge/If%20you%20like%20it-PayPal%20Me-blue.svg?style=for-the-badge)](https://paypal.me/dirkmaucher)
[![forum](https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge)](https://community.home-assistant.io/t/hass-deltasol-km2-resol-km1-km2-dl2-dl3-vbus-lan-vbus-usb/871497)

[![GitHub Repo stars](https://img.shields.io/github/stars/dm82m/hass-deltasol-km2?style=flat)](https://github.com/dm82m/hass-Deltasol-KM2/stargazers) _Thanks to everyone having starred my repo! To star it click [here](https://github.com/dm82m/hass-Deltasol-KM2), then click on the star on the top right. Thanks!_

# hass-Deltasol-KM2

Custom component for retrieving sensor information from Resol KM1/KM2 or DL2/DL2Plus/DL3 or VBus/LAN or VBus/USB. This component automatically determines if you are using KM2 or DL2/DL2Plus/DL3 device and can also be set up to work with KM1, VBus/LAN or VBus/USB.
Component uses webservice to get all the sensor data and makes it available in [Home Assistant](https://home-assistant.io/).

## Features

### Currently Available Features

- :computer: This integration supports all Resol devices: KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN and VBus/USB. Welcome the *DL2Plus* as the newest family member.
- :tv: This integration is fully configurable within the UI, no `yaml` configuration needed. *It now even guides you through the whole setup process and only asks you for the options that are really needed for your specific device. And we even have the possibility to re-configure your device and change all options you made before.*
- :star: The exclusive filter that is only available on DL2/DL3 devices can be used with this integration!
- :link: If the connection to your Resol device gets lost (network issue, Add-on not yet started, ...) the integration makes retries until the connection is established.
- :large_blue_diamond: All the data of your Resol device is shown in Home Assistant. I.e. Product Name, Serial Number, Product Features, Software Version, Hardware Version, ...
- :small_blue_diamond: All bus devices that are connected to your Resol device are shown as device in Home Assistant with the specific bus device name. Additionally all the sensors are grouped by these bus devices to make it easier to find your desired sensors.
- :small_orange_diamond: By default all sensors without a unit are handled as diagnostic sensors and disabled by default. You can manually enable them if needed.
- :earth_africa: Multiple language support, currently we have :uk:, :de:, :it: and :netherlands:. If you speak another language, just directly open a PR or create an [Translation Request](https://github.com/dm82m/hass-Deltasol-KM2/issues/new?template=translation_request.yml) for your language and provide the translation there.

### Next To Come Features (Wishlist)

- :arrows_counterclockwise: Move the configuration of SCAN_INTERVAL into options flow instead of having it in the configuration flow.
- ... more ideas? Feel free to open an [Feature Request](https://github.com/dm82m/hass-Deltasol-KM2/issues/new?template=feature_request.yml).

### Bugs

:bug: No software is perfect and therefore neither is this one. If you encounter a problem, please open an [Bug Report](https://github.com/dm82m/hass-Deltasol-KM2/issues/new?template=bug_report.yml).

## Release 1.x.x

> [!IMPORTANT]
>
>With version 1.x.x we have moved on to UI based configuration. The `yaml` configuration will be automtically migrated. The process is as following:
> - Update the integration to version 1.x.x.
> - Restart Home Assistant Core.
> - Remove the old sensor definition from your `configuration.yaml`.

## Installation

### HACS (preferred method)

- [![add_resol](https://img.shields.io/badge/Add%20Integration-Home%20Assistant-blue?style=flat)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dm82m&repository=hass-Deltasol-KM2&category=integration) or go to your HACS store and search for `dm82m/hass-Deltasol-KM2`.
- Click `Download` in the lower right side and install it.
- Restart Home Assistant Core.
- [![configure_resol](https://img.shields.io/badge/Configure%20Integration-Home%20Assistant-blue?style=flat)](https://my.home-assistant.io/redirect/config_flow_start/?domain=deltasol) or configure the integration by adding it via UI `Settings` -> `Devices & Services` -> `Add Integration` -> `Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB`. Then follow the configuration steps below.

### Manual install

Create a directory called `deltasol` in the `<config directory>/custom_components/` directory on your Home Assistant instance. Install this component by copying all files in `/custom_components/deltasol/` folder from this repo into the new `<config directory>/custom_components/deltasol/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── deltasol
│   ├── __init__.py
│   ├── config_flow.py
│   ├── const.py
│   ├── deltasolapi.py
│   ├── manifest.json
│   ├── sensor.py
│   ├── strings.json
│   └── languages
│       ├── de.json
│       ├── en.json
│       ├── it.json
│       └── nl.json
```

Restart Home Assistant Core and afterwards [![configure_resol](https://img.shields.io/badge/Configure%20Integration-Home%20Assistant-blue?style=flat)](https://my.home-assistant.io/redirect/config_flow_start/?domain=deltasol) or configure the integration by adding it via UI `Settings` -> `Devices & Services` -> `Add Integration` -> `Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB`. Then follow the configuration steps below.

## Configuration

In any case, try to ensure to have the latest firmware running on your Resol device.

### KM2 and DL2/DL2Plus/DL3

It works out-of-the-box, the only thing that is needed is the configuration described next.

#### Configuration

- `Host`: Hostname or IP address of your Resol KM2 or DL2/DL2Plus/DL3.
- `Port`: Port of your Resol KM2 or DL2/DL2Plus/DL3. Defaults to 80. Do not change that, unless you know what you do.
- `Username`: Username used for logging in to Resol KM2 or DL2/DL2Plus/DL3.
- `Password`: Password used for logging in to Resol KM2 or DL2/DL2Plus/DL3.
- `Scan interval` (Optional): Defines update frequency. Optional and in seconds. Defaults to 300 (5 min), minimum value is 60 (1 min).
- `API key` (Optional):  Only applicable if you are using DL2/DL3 device. Applies the filter defined on the DL2/DL3. Use the id of the DL2/DL3 defined filter here.

### KM1, VBus/LAN and VBus/USB

There is one prerequisite before it works. You need to run the resol-vbus [json-live-data-server](https://github.com/danielwippermann/resol-vbus/tree/master/examples/json-live-data-server). To do so you have at least two possibilities:
1. Run the server as an HAOS add-on, continue [here](https://github.com/dm82m/hassio-addons/tree/main/resol-vbus).
2. Run the server on your own, continue [here](https://github.com/danielwippermann/resol-vbus/tree/master/examples/json-live-data-server) and ensure to be at least on git commit `7c9e88af5af3e14443c01a4ec5d7c042be2163f9`.

If your json-live-data-server is successfully running, lets continue here.

#### Configuration

- `Host`: If you went with point 1 it is `127.0.0.1` and if you went with point 2 it is `hostname_or_ip_of_your_json-live-data-server`.
- `Port`: Within default `json-live-data-server` it is port `3333`. If you have changed that, you need to use this port here aswell. Otherweise set it to `3333`.
- `Scan interval` (Optional): Defines update frequency. Optional and in seconds. Defaults to 300 (5 min), minimum value is 60 (1 min).
- Do not set `Username`, `Password` or `API key` here, they are not needed.

## Troubleshooting
Please set your logging for this custom component to debug during initial setup phase. If everything works well, you are safe to remove the debug logging:
```yaml
logger:
  default: warn
  logs:
    custom_components.deltasol: debug
```

## Credits

A huge thank you to all the contributors and also thank you to everyone who contributed ideas.

[![contributors](https://contrib.rocks/image?repo=dm82m/hass-Deltasol-KM2)](https://github.com/dm82m/hass-Deltasol-KM2/graphs/contributors)
