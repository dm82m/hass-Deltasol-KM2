"""Config flow for Resol KM1/KM2, DL2/DL2Plus/DL3, VBus/LAN, VBus/USB component."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, IntegrationError
from homeassistant.helpers import config_validation as cv

from .const import (
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)
from .deltasolapi import DeltasolApi

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

STEP_AUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)

STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
        ),
    }
)

STEP_DL23OPTIONS_DATA_SCHEMA = STEP_OPTIONS_DATA_SCHEMA.extend(
    {
        vol.Optional(CONF_API_KEY): cv.string,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    api = DeltasolApi(
        host=data.get(CONF_HOST),
        port=data.get(CONF_PORT),
    )

    try:
        await hass.async_add_executor_job(api.detect_product)
    except IntegrationError as err:
        raise CannotConnect from err

    return {
        "title": f"{api.product_details["name"]}@{data.get(CONF_HOST)}:{data.get(CONF_PORT)}",
        "product": {api.product},
    }


async def validate_auth(hass: HomeAssistant, data: dict[str, Any]) -> bool:
    """Validates the authentication to the Resol device."""

    api = DeltasolApi(
        host=data.get(CONF_HOST),
        port=data.get(CONF_PORT),
        username=data.get(CONF_USERNAME, None),
        password=data.get(CONF_PASSWORD, None),
    )

    try:
        await hass.async_add_executor_job(api.fetch_data)
    except IntegrationError as err:
        raise InvalidAuth from err

    return True


class ResolConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Resol integration."""

    VERSION = 1
    _title: str
    _product: str
    _input_data: dict[str, Any]
    _reconfigure_entry = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                if not self._reconfigure_entry:
                    await self.async_set_unique_id(info.get("title"))
                    self._abort_if_unique_id_configured()

                self._title = info["title"]
                self._product = info["product"]
                self._input_data = user_input
                try:
                    await validate_auth(self.hass, user_input)
                except InvalidAuth:
                    return await self.async_step_auth()

                return await self.async_step_options()

        schema = STEP_USER_DATA_SCHEMA
        if self._reconfigure_entry:
            STEP_USER_DATA_SCHEMA_RECON = vol.Schema(
                {
                    vol.Required(
                        CONF_HOST, default=self._reconfigure_entry.data.get(CONF_HOST)
                    ): cv.string,
                    vol.Required(
                        CONF_PORT,
                        default=self._reconfigure_entry.data.get(CONF_PORT),
                    ): cv.port,
                }
            )
            schema = STEP_USER_DATA_SCHEMA_RECON

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the auth step, if auth is needed."""

        errors: dict[str, str] = {}

        if user_input is not None:
            user_input.update(self._input_data)

            try:
                await validate_auth(self.hass, user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if "base" not in errors:
                self._input_data.update(user_input)

                if self._product in ["dl2", "dl3"]:
                    return await self.async_step_dl23options()
                else:
                    return await self.async_step_options()

        schema = STEP_AUTH_DATA_SCHEMA
        if self._reconfigure_entry:
            STEP_AUTH_DATA_SCHEMA_RECON = vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=self._reconfigure_entry.data.get(CONF_USERNAME, ""),
                    ): cv.string,
                    vol.Required(
                        CONF_PASSWORD,
                        default=self._reconfigure_entry.data.get(CONF_PASSWORD, ""),
                    ): cv.string,
                }
            )
            schema = STEP_AUTH_DATA_SCHEMA_RECON

        return self.async_show_form(
            step_id="auth",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the final options step."""

        if user_input is not None:
            self._input_data.update(user_input)
            if not self._reconfigure_entry:
                return self.async_create_entry(title=self._title, data=self._input_data)
            else:
                return self.async_update_reload_and_abort(
                    self._reconfigure_entry,
                    unique_id=self._reconfigure_entry.unique_id,
                    data={**self._reconfigure_entry.data, **self._input_data},
                    reason="reconfigure_successful",
                )

        schema = STEP_OPTIONS_DATA_SCHEMA
        if self._reconfigure_entry:
            STEP_OPTIONS_DATA_SCHEMA_RECON = vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self._reconfigure_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                }
            )
            schema = STEP_OPTIONS_DATA_SCHEMA_RECON

        return self.async_show_form(
            step_id="options",
            data_schema=schema,
            last_step=True,
        )

    async def async_step_dl23options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the final DL2/DL3 options step."""

        if user_input is not None:
            self._input_data.update(user_input)
            if not self._reconfigure_entry:
                return self.async_create_entry(title=self._title, data=self._input_data)
            else:
                return self.async_update_reload_and_abort(
                    self._reconfigure_entry,
                    unique_id=self._reconfigure_entry.unique_id,
                    data={**self._reconfigure_entry.data, **self._input_data},
                    reason="reconfigure_successful",
                )

        schema = STEP_DL23OPTIONS_DATA_SCHEMA
        if self._reconfigure_entry:
            STEP_DL23OPTIONS_DATA_SCHEMA_RECON = vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self._reconfigure_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                    vol.Optional(
                        CONF_API_KEY,
                        default=self._reconfigure_entry.data.get(CONF_API_KEY, ""),
                    ): cv.string,
                }
            )
            schema = STEP_DL23OPTIONS_DATA_SCHEMA_RECON

        return self.async_show_form(
            step_id="dl23options",
            data_schema=schema,
            last_step=True,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add reconfigure step to allow to reconfigure a config entry."""

        self._reconfigure_entry = self._get_reconfigure_entry()

        return await self.async_step_user()

    async def async_step_import(self, import_data):
        """Import config from configuration.yaml.

        Triggered by async_setup only if a config entry doesn't already exist.
        We will attempt to validate the credentials
        and create an entry if valid. Otherwise, we will delegate to the user
        step so that the user can continue the config flow.
        """
        # This function can be removed in a future version when migration to config flow completed.
        user_input = {}
        _LOGGER.warning(
            "Importing old configuration of 'configuration.yaml': %s", import_data
        )
        try:
            conf_scan_interval_sec = import_data.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            )
            if isinstance(conf_scan_interval_sec, timedelta):
                conf_scan_interval_sec = conf_scan_interval_sec.total_seconds()
            user_input = {
                CONF_HOST: (
                    import_data[CONF_HOST].split(":")[0]
                    if ":" in import_data[CONF_HOST]
                    else import_data[CONF_HOST]
                ),
                CONF_PORT: (
                    import_data[CONF_HOST].split(":")[1]
                    if ":" in import_data[CONF_HOST]
                    else 80
                ),
                CONF_USERNAME: import_data.get(CONF_USERNAME, ""),
                CONF_PASSWORD: import_data.get(CONF_PASSWORD, ""),
                CONF_SCAN_INTERVAL: conf_scan_interval_sec,
                CONF_API_KEY: import_data.get(CONF_API_KEY, ""),
            }
        except (HomeAssistantError, KeyError):
            _LOGGER.debug(
                "No valid configuration found for import, delegating to user step"
            )
            return await self.async_step_user(user_input=user_input)

        try:
            info = await validate_input(self.hass, user_input)
            await validate_auth(self.hass, user_input)
            await self.async_set_unique_id(info.get("title"))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info.get("title"), data=user_input)
        except (CannotConnect, InvalidAuth):
            _LOGGER.debug(
                "Error connecting to Resol using configuration found for import, delegating to user step"
            )
            return await self.async_step_user(user_input=user_input)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
