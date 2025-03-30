"""Sensor entities."""

import logging
from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import DeltasolConfigEntry, DeltasolCoordinator
from .const import DOMAIN
from .deltasolapi import DeltasolEndpoint

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: DeltasolConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Platform setup for Resol KM1/KM2, DL2/DL3, VBus/LAN, VBus/USB sensors."""
    # This function can be removed in a future version when migration to config flow completed.
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

    if config.get("platform") == DOMAIN:
        _LOGGER.error(
            "The %s integration has been migrated to use a config flow setup.  Please delete the entry in configuration.yaml",
            DOMAIN,
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


class DeltasolSensor(CoordinatorEntity, SensorEntity):
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

    def __init__(
        self,
        coordinator: DeltasolCoordinator,
        unique_id: str,
        endpoint: DeltasolEndpoint,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        # Set correct type for coordinator
        self.coordinator: DeltasolCoordinator = coordinator

        self._attr_unique_id = unique_id
        self._endpoint = endpoint

        self._last_updated = dt_util.now()
        self._attr_unique_id = unique_id
        self._attr_name = endpoint.name
        self._attr_icon = DeltasolSensor.icon_mapper[endpoint.unit]

        self._unit = endpoint.unit
        self._state = None

        # Set entity category to diagnostic and disabled for sensors with no unit
        if not endpoint.unit:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._last_updated = dt_util.now()
        _LOGGER.debug("Updating %s", self.name)
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        try:
            state = self.coordinator.data[self.unique_id].value
            if state:
                return state
        except KeyError:
            _LOGGER.error("Can't find %s", self.name)
            _LOGGER.debug("Sensor data %s", self.coordinator.data)
            return None
        else:
            return 0

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of this entity, if any."""
        return self._endpoint.unit

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of this entity, if any."""
        if self._unit == UnitOfTemperature.CELSIUS:
            return SensorDeviceClass.TEMPERATURE
        if self._unit == PERCENTAGE:
            return SensorDeviceClass.POWER_FACTOR
        if self._unit == UnitOfEnergy.WATT_HOUR:
            return SensorDeviceClass.ENERGY
        if isinstance(self.coordinator.data[self.unique_id].value, date):
            return SensorDeviceClass.DATE
        return None

    @property
    def state_class(self) -> SensorStateClass | str | None:
        """Return the state class of this entity, if any."""
        if self._unit == UnitOfTemperature.CELSIUS:
            return SensorStateClass.MEASUREMENT
        if self._unit == UnitOfEnergy.WATT_HOUR:
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes."""
        # Device unique identifier is the serial + bus_src
        product_details = self._endpoint.product_details
        return DeviceInfo(
            identifiers={
                (DOMAIN, product_details["serial"] + "_" + self._endpoint.bus_src)
            },
            name=self._endpoint.bus_src,
            manufacturer=product_details["vendor"],
            model=product_details["name"],
            sw_version=product_details["version"],
            serial_number=product_details["serial"],
            hw_version=product_details["build"],
            model_id=product_details["features"],
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes of this device."""
        attr = {}
        if self._last_updated is not None:
            attr["Last Updated"] = self._last_updated
        return attr
