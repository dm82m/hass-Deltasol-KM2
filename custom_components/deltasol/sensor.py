"""Sensor entities."""

from collections import defaultdict
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from . import DeltasolConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: DeltasolConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Platform setup for Resol KM1/KM2, DL2/DL3, VBus/LAN, VBus/USB sensors."""

    if (
        not hass.config_entries.async_entries(DOMAIN)
        and config.get("platform") == DOMAIN
    ):
        # No config entry exists and configuration.yaml config exists, trigger the import flow.
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=config,
            )
        )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config: DeltasolConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    coordinator = config.runtime_data.coordinator
    async_add_entities(
        DeltasolSensor(coordinator, unique_id, endpoint)
        for unique_id, endpoint in coordinator.data.items()
    )


class DeltasolSensor(SensorEntity):
    """Representation of a Resol sensor."""

    icon_mapper = defaultdict(
        lambda: "mdi:alert-circle",
        {
            "°C": "mdi:thermometer",
            "%": "mdi:flash",
            "l/h": "mdi:hydro-power",
            "bar": "mdi:car-brake-low-pressure",
            "%RH": "mdi:water-percent",
            "s": "mdi:timer",
            "Wh": "mdi:solar-power-variant-outline",
        },
    )

    def __init__(self, coordinator, unique_id, endpoint) -> None:
        """Initialize the sensor."""
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

        self._product_details = endpoint.product_details

        # Set entity category to diagnostic for sensors with no unit
        if not endpoint.unit:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        # If diagnostics entity then disable sensor by default
        if not endpoint.unit:
            self._attr_entity_registry_enabled_default = False

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
        return self._unique_id

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the sensor."""
        try:
            state = self.coordinator.data[self._unique_id].value
            if state:
                return state
        except KeyError:
            _LOGGER.error("Can't find %s", self._name)
            _LOGGER.debug("Sensor data %s", self.coordinator.data)
            return None
        else:
            return 0

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_class(self):
        """Return the device class of this entity, if any."""
        if self._unit == "°C":
            return SensorDeviceClass.TEMPERATURE
        if self._unit == "%":
            return SensorDeviceClass.POWER_FACTOR
        if self._unit == "Wh":
            return SensorDeviceClass.ENERGY
        return None

    @property
    def state_class(self):
        """Return the state class of this entity, if any."""
        if self._unit == "°C":
            return SensorStateClass.MEASUREMENT
        if self._unit == "Wh":
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def device_info(self):
        """Return device specific attributes."""
        # Device unique identifier is the serial
        return {
            "identifiers": {(DOMAIN, self._product_details["serial"] + "_" + self._src_name)},
            "name": self._src_name,
            "manufacturer": self._product_details["vendor"],
            "model": self._product_details["name"],
            "sw_version": self._product_details["version"],
            "serial_number": self._product_details["serial"],
            "hw_version": self._product_details["build"],
            "model_id": self._product_details["features"],
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes of this device."""
        attr = {}
        if self._last_updated is not None:
            attr["Last Updated"] = self._last_updated
        return attr

    async def async_update(self):
        """Update Entity. Only used by the generic entity update service."""
        await self.coordinator.async_request_refresh()
