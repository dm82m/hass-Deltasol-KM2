"""
Gets sensor data from Resol Deltasol KM2/DL2/DL3, VBus/LAN, VBus/USB using api.
Author: dm82m
https://github.com/dm82m/hass-Deltasol-KM2

Configuration for this platform:
sensor:
  - platform: deltasol
    #scan_interval: 300
    #api_key: 00
    host: 192.168.178.15
    username: username
    password: password
"""

from datetime import timedelta

import async_timeout
import homeassistant.helpers.config_validation as config_validation
import homeassistant.helpers.entity_registry as entity_registry
import voluptuous as vol
from collections import defaultdict
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    PLATFORM_SCHEMA
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_API_KEY
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import IntegrationError

from .const import DEFAULT_NAME, _LOGGER, DEFAULT_TIMEOUT, DOMAIN
from .deltasolapi import DeltasolApi

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): config_validation.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=timedelta(minutes=5)): config_validation.time_period,
        vol.Required(CONF_HOST): config_validation.string,
        vol.Optional(CONF_USERNAME): config_validation.string,
        vol.Optional(CONF_PASSWORD): config_validation.string,
        vol.Optional(CONF_API_KEY): config_validation.matches_regex("\d\d"),
    }
)

async def update_unique_ids(hass, data):
    _LOGGER.debug("Checking for sensors with old ids in registry.")
    ent_reg = entity_registry.async_get(hass)

    for unique_id, endpoint in data.items():
        name_id = ent_reg.async_get_entity_id("sensor", DOMAIN, endpoint.name)
        if name_id is not None:
            _LOGGER.info(f"Found entity with old id ({name_id}). Updating to new unique_id ({unique_id}).")
            # check if there already is a new one
            new_entity_id = ent_reg.async_get_entity_id("sensor", DOMAIN, unique_id)
            if new_entity_id is not None:
                _LOGGER.info("Found entity with old id and an entity with a new unique_id. Preserving old entity...")
                ent_reg.async_remove(new_entity_id)
            ent_reg.async_update_entity(name_id, new_unique_id=unique_id)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """ Setup the Resol Deltasol KM2/DL2/DL3, VBus/LAN, VBus/USB sensors. """

    api = DeltasolApi(config.get(CONF_USERNAME), config.get(CONF_PASSWORD), config.get(CONF_HOST), config.get(CONF_API_KEY))

    async def async_update_data():
        """ Fetch data from the Resol Deltasol KM2/DL2/DL3, VBus/LAN, VBus/USB. """
        async with async_timeout.timeout(DEFAULT_TIMEOUT):
            try:
                data = await hass.async_add_executor_job(api.fetch_data)
                return data
            except IntegrationError as error:
                _LOGGER.error(f"Stopping Deltasol Resol integration due to previous error: {error}")
                raise error

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

    # Find old entity_ids and convert them to the new format
    await update_unique_ids(hass, coordinator.data)

    async_add_entities(
        DeltasolSensor(coordinator, unique_id, endpoint) for unique_id, endpoint in coordinator.data.items()
    )


class DeltasolSensor(SensorEntity):
    """ Representation of a Resol Deltasol sensor. """
    icon_mapper = defaultdict(lambda: "mdi:alert-circle", {
        '°C': 'mdi:thermometer',
        '%': 'mdi:flash',
        'l/h': 'mdi:hydro-power',
        'bar': 'mdi:car-brake-low-pressure',
        '%RH': 'mdi:water-percent',
        's': 'mdi:timer' })

    def __init__(self, coordinator, unique_id, endpoint):
        """ Initialize the sensor. """
        self.coordinator = coordinator
        self._last_updated = None
        self._unique_id = unique_id
        self._name = endpoint.name
        self._icon = DeltasolSensor.icon_mapper[endpoint.unit]
        self._unit = endpoint.unit
        self._state = self.state
        self._desc = endpoint.description
        self._dest_name = endpoint.bus_dest
        self._src_name = endpoint.bus_src

    @property
    def should_poll(self):
        """ No need to poll. Coordinator notifies entity of updates. """
        return False

    @property
    def available(self):
        """ Return if entity is available. """
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """ When entity is added to hass. """
        self.coordinator.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """ When entity will be removed from hass. """
        self.coordinator.async_remove_listener(self.async_write_ha_state)

    @property
    def name(self):
        """ Return the name of the sensor. """
        return self._name

    @property
    def unique_id(self):
        """ Return the unique ID of the binary sensor. """
        return self._unique_id

    @property
    def icon(self):
        """ Icon to use in the frontend, if any. """
        return self._icon

    @property
    def state(self):
        """ Return the state of the sensor. """
        try:
            state = self.coordinator.data[self._unique_id].value
            if state:
                return state
            return 0
        except KeyError:
            _LOGGER.error("can't find %s", self._name)
            _LOGGER.debug("sensor data %s", self.coordinator.data)
            return None

    @property
    def unit_of_measurement(self):
        """ Return the unit of measurement of this entity, if any. """
        return self._unit

    @property
    def device_class(self):
        """ Return the device class of this entity, if any. """
        if self._unit == '°C':
            return SensorDeviceClass.TEMPERATURE
        elif self._unit == '%':
            return SensorDeviceClass.POWER_FACTOR
        else:
            return None

    @property
    def state_class(self):
        """ Return the state class of this entity, if any. """
        if self._unit == '°C':
            return SensorStateClass.MEASUREMENT
        else:
            return None

    @property
    def extra_state_attributes(self):
        """ Return the state attributes of this device. """
        attr = {}
        attr["description"] = self._desc
        attr["destination_name"] = self._dest_name
        attr["source_name"] = self._src_name
        if self._last_updated is not None:
            attr["Last Updated"] = self._last_updated
        return attr

    async def async_update(self):
        """ Update Entity. Only used by the generic entity update service. """
        await self.coordinator.async_request_refresh()
