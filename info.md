[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![buy me a coffee](https://img.shields.io/badge/If%20you%20like%20it-Buy%20me%20a%20coffee-yellow.svg?style=for-the-badge)](https://www.buymeacoffee.com/dirkmaucher)
[![License](https://img.shields.io/github/license/toreamun/amshan-homeassistant?style=for-the-badge)](LICENSE)

# hass-Deltasol-KM2

Custom component for retrieving sensor information from Deltasol KM2.  
Component uses webservice to get all the sensor data from the Deltasol KM2 and makes it available
in [Home Assistant](https://home-assistant.io/).

I want to give special credits to @erikkastelec - my plugin is mainly based on the plugin he created! Thank you for your work man!

## Installation

### HACS (preferred method)

- In [HACS](https://github.com/hacs/default) Store search for dm82m/hass-Deltasol-KM2 and install it
- Activate the component by adding configuration into your `configuration.yaml` file.

### Manual install

Create a directory called `deltasol` in the `<config directory>/custom_components/` directory on your Home Assistant
instance. Install this component by copying all files in `/custom_components/deltasol/` folder from this repo into the
new `<config directory>/custom_components/deltasol/` directory you just created.

This is how your custom_components directory should look like:

```bash
custom_components
├── deltasol
│   ├── __init__.py
│   ├── const.py
│   ├── manifest.json
│   └── sensor.py
│   └── deltasolapi.py  
```

## Configuration

Configuration variables:
- `username`: Email address used for logging into WEM Portal
- `password`: Password used for logging into WEM Portal
- `host`: Hostname or IP address of your Deltasol KM2
- `scan_interval (Optional)`: Defines update frequency. Optional and in seconds (defaults to 5 min, minimum value is 1
  min)

Add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: deltasol
  	host: your_deltasol_hostname_or_ip_address
    username: your_username
    password: your_password
```

## Troubleshooting
Please set your logging for the custom_component to debug:
```yaml
logger:
  default: warn
  logs:
    custom_components.deltasol: debug
```