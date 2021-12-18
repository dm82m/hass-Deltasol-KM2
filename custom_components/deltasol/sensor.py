"""
Gets sensor data from Deltasol KM2 using api.
Author: dm82m
https://github.com/dm82m/hass-Deltasol-KM2

Configuration for this platform:
sensor:
  - platform: deltasol
    #scan_interval: 300
    host: 192.168.178.15
    username: username
    password: password
"""

from datetime import timedelta

import async_timeout
import homeassistant.helpers.config_validation as config_validation
import voluptuous as vol
from homeassistant.components.sensor import SensorEntity, PLATFORM_SCHEMA, STATE_CLASS_MEASUREMENT
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER_FACTOR
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_NAME, _LOGGER, DEFAULT_TIMEOUT
from .deltasolapi import DeltasolApi

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): config_validation.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=timedelta(minutes=5)): config_validation.time_period,
        vol.Required(CONF_HOST): config_validation.string,
        vol.Required(CONF_USERNAME): config_validation.string,
        vol.Required(CONF_PASSWORD): config_validation.string,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the Deltasol KM2 sensors."""

    api = DeltasolApi(config.get(CONF_USERNAME), config.get(CONF_PASSWORD), config.get(CONF_HOST))

    async def async_update_data():
        """ fetch data from the Wem Portal website"""
        async with async_timeout.timeout(DEFAULT_TIMEOUT):
            data = await hass.async_add_executor_job(api.fetch_data)
            return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="deltasol_km2_sensor",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=max(config.get(CONF_SCAN_INTERVAL), timedelta(minutes=1)),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    entities = []
    sensor_prefix = config.get(CONF_NAME)

    async_add_entities(
        DeltasolSensor(coordinator, _name, values[1], values[2]) for _name, values in coordinator.data.items()
    )


class DeltasolSensor(SensorEntity):
    """Representation of a Deltasol Sensor."""

    def __init__(self, coordinator, _name, _icon, _unit):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._last_updated = None
        self._name = _name
        self._icon = _icon
        self._unit = _unit
        self._state = self.state

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        self.coordinator.async_remove_listener(self.async_write_ha_state)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the binary sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        try:
            state = self.coordinator.data[self._name][0]
            if state:
                return state
            return 0
        except KeyError:
            _LOGGER.error("can't find %s", self._name)
            _LOGGER.debug("sensor data %s", self.coordinator.data)
            return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class of this entity, if any."""
        if self._unit == '°C':
            return DEVICE_CLASS_TEMPERATURE
        elif self._unit == '%':
            return DEVICE_CLASS_POWER_FACTOR
        else:
            return None

    @property
    def state_class(self):
        """Return the state class of this entity, if any."""
        if self._unit == '°C':
            return STATE_CLASS_MEASUREMENT
        else:
            return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes of this device."""
        attr = {}
        if self._last_updated is not None:
            attr["Last Updated"] = self._last_updated
        return attr

    async def async_update(self):
        """Update Entity
        Only used by the generic entity update service."""
        await self.coordinator.async_request_refresh()
