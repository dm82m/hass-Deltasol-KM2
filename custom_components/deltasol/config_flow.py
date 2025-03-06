"""Config flow for Integration 101 Template integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, IntegrationError
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN
from .deltasolapi import DeltasolApi

_LOGGER = logging.getLogger(__name__)


CONFIG_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=80): int,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=5): int,
        vol.Optional(CONF_API_KEY): cv.string,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    api = DeltasolApi(
        data.get(CONF_USERNAME),
        data.get(CONF_PASSWORD),
        data.get(CONF_HOST),
        data.get(CONF_PORT),
        data.get(CONF_API_KEY),
    )

    try:
        await hass.async_add_executor_job(api.detect_product)
        # If you cannot connect, raise CannotConnect
        # If the authentication is wrong, raise InvalidAuth
    except IntegrationError as err:
        raise CannotConnect from err

    return {"title": DEFAULT_NAME}


class ExampleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Example Integration."""

    VERSION = 1
    _input_data: dict[str, Any]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Called when you initiate adding an integration via the UI
        errors: dict[str, str] = {}

        if user_input is not None:
            # The form has been filled in and submitted, so process the data provided.
            try:
                # Validate that the setup data is valid and if not handle errors.
                # The errors["base"] values match the values in your strings.json and translation files.
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                # Validation was successful, so create a unique id for this instance of your integration
                # and create the config entry.
                await self.async_set_unique_id(info.get("title"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)

        # Show initial form.
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add reconfigure step to allow to reconfigure a config entry."""
        # This methid displays a reconfigure option in the integration and is
        # different to options.
        # It can be used to reconfigure any of the data submitted when first installed.
        # This is optional and can be removed if you do not want to allow reconfiguration.
        errors: dict[str, str] = {}
        config = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if user_input is not None:
            try:
                user_input[CONF_HOST] = config.data[CONF_HOST]
                user_input[CONF_PORT] = config.data[CONF_PORT]
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    config,
                    unique_id=config.unique_id,
                    data={**config.data, **user_input},
                    reason="reconfigure_successful",
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=config.data.get(CONF_SCAN_INTERVAL),
                    ): int,
                    vol.Optional(
                        CONF_USERNAME, default=config.data.get(CONF_USERNAME)
                    ): cv.string,
                    vol.Optional(
                        CONF_PASSWORD, default=config.data.get(CONF_PASSWORD)
                    ): cv.string,
                    vol.Optional(
                        CONF_API_KEY, default=config.data.get(CONF_API_KEY)
                    ): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_data):
        """Import config from configuration.yaml.

        Triggered by async_setup only if a config entry doesn't already exist.
        We will attempt to validate the credentials
        and create an entry if valid. Otherwise, we will delegate to the user
        step so that the user can continue the config flow.
        """
        errors = {}
        user_input = {}
        _LOGGER.warning("IMPORT DATA: %s", import_data)
        try:
            user_input = {
                CONF_HOST: import_data[CONF_HOST].split(':')[0] if ':' in import_data[CONF_HOST] else import_data[CONF_HOST],
                CONF_PORT: import_data[CONF_HOST].split(':')[1] if ':' in import_data[CONF_HOST] else 80,
                CONF_USERNAME: import_data.get(CONF_USERNAME),
                CONF_PASSWORD: import_data.get(CONF_PASSWORD),
                CONF_SCAN_INTERVAL: import_data.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
                CONF_API_KEY: import_data.get(CONF_API_KEY),
            }
        except (HomeAssistantError, KeyError):
            _LOGGER.debug(
                "No valid configuration found for import, delegating to user step"
            )
            return await self.async_step_user(user_input=user_input)

        try:
            info = await validate_input(self.hass, user_input)
            await self.async_set_unique_id(info.get("title"))
            self._abort_if_unique_id_configured()
            return await self.async_step_user(user_input=user_input)
            # return self.async_create_entry(title=info["title"], data=user_input)
        except CannotConnect:
            _LOGGER.debug(
                "Error connecting to Deltasol using configuration found for import, delegating to user step"
            )
            errors["base"] = "cannot_connect"


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
