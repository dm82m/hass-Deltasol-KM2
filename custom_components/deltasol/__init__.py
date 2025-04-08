"""The Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB component.

Gets sensor data from Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB using api
Author: dm82m
https://github.com/dm82m/hass-Deltasol-KM2"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA_BASE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, IntegrationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    MIN_SCAN_INTERVAL,
)
from .deltasolapi import DeltasolApi, DeltasolEndpoint

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

PLATFORM_SCHEMA = PLATFORM_SCHEMA_BASE.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
        ),
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_API_KEY): cv.string,
    }
)

type DeltasolConfigEntry = ConfigEntry[RuntimeData]


@dataclass
class RuntimeData:
    """Class to hold your data."""

    coordinator: DataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config):
    """Set up yaml entry."""

    # This function can be removed in a future version when migration to config flow completed.
    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: DeltasolConfigEntry
) -> bool:
    """Set up Example Integration from a config entry."""

    # Initialise the coordinator that manages data updates from your api.
    # This is defined in below
    coordinator = DeltasolCoordinator(hass, config_entry)

    # Perform an initial data load from api.
    # async_config_entry_first_refresh() is special in that it does not log errors if it fails
    await coordinator.async_config_entry_first_refresh()

    # Test to see if api initialised correctly, else raise ConfigNotReady to make HA retry setup
    if not coordinator.api.product_details:
        raise ConfigEntryNotReady

    # Add the coordinator and update listener to config runtime data to make
    # accessible throughout your integration
    config_entry.runtime_data = RuntimeData(coordinator)

    # Setup platforms (based on the list of entity types in PLATFORMS defined above)
    # This calls the async_setup method in each of your entity type files.
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Return true to denote a successful setup.
    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: DeltasolConfigEntry
) -> bool:
    """Unload a config entry."""
    # This is called when you remove your integration or shutdown HA.
    # If you have created any custom services, they need to be removed here too.

    # Unload platforms and return result
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


class DeltasolCoordinator(DataUpdateCoordinator):
    """Coordinator class."""

    data: dict[str, DeltasolEndpoint]

    def __init__(self, hass: HomeAssistant, config: DeltasolConfigEntry) -> None:
        """Initialize coordinator."""
        self.hass = hass
        self.api = DeltasolApi(
            host=config.data.get(CONF_HOST),
            port=config.data.get(CONF_PORT),
            username=config.data.get(CONF_USERNAME),
            password=config.data.get(CONF_PASSWORD),
            api_key=config.data.get(CONF_API_KEY),
        )
        super().__init__(
            hass,
            _LOGGER,
            name="deltasol_sensor",
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(
                seconds=max(
                    config.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    MIN_SCAN_INTERVAL,
                )
            ),
        )

    async def async_update_data(self):
        """Fetch data from the Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB."""
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            try:
                data = await self.hass.async_add_executor_job(self.api.fetch_data)
            except IntegrationError as error:
                _LOGGER.error(
                    "Stopping Resol integration due to previous error: %s", error
                )
                raise
            else:
                return data
