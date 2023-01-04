[![version](https://img.shields.io/github/v/release/dm82m/hass-Deltasol-KM2?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2)
[![maintained](https://img.shields.io/maintenance/yes/2023?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2)
[![license](https://img.shields.io/github/license/toreamun/amshan-homeassistant?style=for-the-badge)](LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)<br/>
[![downloads_latest](https://img.shields.io/github/downloads/dm82m/hass-Deltasol-KM2/latest/total?style=for-the-badge)](https://github.com/dm82m/hass-Deltasol-KM2/releases)
[![buy_me_a_coffee](https://img.shields.io/badge/If%20you%20like%20it-Buy%20me%20a%20coffee-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/dirkmaucher)

# hass-Deltasol-KM2

Custom component for retrieving sensor information from Resol Deltasol KM2 or DL2/DL3 or VBus/LAN or VBus/USB. This component automatically determines if you are using KM2 or DL2/DL3 device and can also be set up to work with VBus/LAN or VBus/USB.
Component uses webservice to get all the sensor data and makes it available in [Home Assistant](https://home-assistant.io/).

## Installation

### HACS (preferred method)

- In [HACS](https://github.com/hacs/default) Store search for dm82m/hass-Deltasol-KM2 and install it.
- Activate the component by adding configuration into your `configuration.yaml` file.

### Manual install

Create a directory called `deltasol` in the `<config directory>/custom_components/` directory on your Home Assistant instance. Install this component by copying all files in `/custom_components/deltasol/` folder from this repo into the new `<config directory>/custom_components/deltasol/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── deltasol
│   ├── __init__.py
│   ├── const.py
│   ├── manifest.json
│   ├── sensor.py
│   └── deltasolapi.py  
```

## Configuration

### KM2 and DL2/DL3

It works out-of-the-box, the only thing that is needed is the configuration described next.

#### Configuration variables

- `username`: Username used for logging in to Resol Deltasol KM2 or DL2/DL3.
- `password`: Password used for logging in to Resol Deltasol KM2 or DL2/DL3.
- `host`: Hostname or IP address of your Resol Deltasol KM2 or DL2/DL3.
- `scan_interval` (Optional): Defines update frequency. Optional and in seconds. Defaults to 300 (5 min), minimum value is 60 (1 min).
- `api_key` (Optional):  Only applicable if you are using DL2/DL3 device. Applies the filter defined on the DL2/DL3. Use the id of the DL2/DL3 defined filter here.

#### Example `configuration.yaml`

```yaml
sensor:
  - platform: deltasol
    host: your_deltasol_hostname_or_ip_address
    username: your_username
    password: your_password
```

### VBus/LAN and VBus/USB

There is one prerequisite before it works. You need to run the resol-vbus [json-live-data-server](https://github.com/danielwippermann/resol-vbus/tree/master/examples/json-live-data-server). To do so you have at least two possibilities:
1. Run the server as an HAOS add-on, continue [here](https://github.com/dm82m/hassio-addons/tree/main/resol-vbus).
2. Run the server on your own, continue [here](https://github.com/danielwippermann/resol-vbus/tree/master/examples/json-live-data-server) and ensure to be at least on git commit `7c9e88af5af3e14443c01a4ec5d7c042be2163f9`.

If your json-live-data-server is successfully running, lets continue here.

#### Configuration variables

- `host`: If you went with point 1 it is `127.0.0.1:3333` and if you went with point 2 it is `hostname_or_ip_of_your_json-live-data-server:3333`.
- `scan_interval` (Optional): Defines update frequency. Optional and in seconds. Defaults to 300 (5 min), minimum value is 60 (1 min).

#### Example `configuration.yaml`

```yaml
sensor:
  - platform: deltasol
    host: 127.0.0.1:3333
```

## Troubleshooting
Please set your logging for the this custom component to debug during initial setup phase. If everything works well, you are safe to remove the debug logging:
```yaml
logger:
  default: warn
  logs:
    custom_components.deltasol: debug
```

## Credits

A huge thank you to the following people for your contribution and/or inspiration: [ostat](https://github.com/ostat) / [chiefdeputy](https://github.com/chiefdeputy) / [erikkastelec](https://github.com/erikkastelec) / [danielwippermann](https://github.com/danielwippermann).
