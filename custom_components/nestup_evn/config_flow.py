"""Config flow for EVN Data integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.data_entry_flow import FlowResult

from homeassistant import config_entries
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_AREA,
    CONF_CUSTOMER_ID,
    CONF_ERR_UNKNOWN,
    CONF_MONTHLY_START,
    CONF_PASSWORD,
    CONF_SUCCESS,
    CONF_USERNAME,
    DOMAIN,
    VIETNAM_EVN_AREA,
)
from . import ha_evn

_LOGGER = logging.getLogger(__name__)

AREA_CONFIG = vol.Schema(
    {vol.Required(CONF_AREA): vol.In([area.name for area in VIETNAM_EVN_AREA])}
)

CONNECT_CONFIG = vol.Schema(
    {
        vol.Required(CONF_CUSTOMER_ID): vol.All(str, vol.Length(min=13, max=13)),
        vol.Required(CONF_MONTHLY_START, default=25): vol.All(
            int, vol.Range(min=1, max=28)
        ),
    }
)

AUTH_CONFIG = vol.Schema(
    {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EVN Data."""

    VERSION = 1

    def __init__(self):
        self._api = ha_evn.EVNAPI()
        self._user_data = {}

    async def async_step_connect(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is None:
            return self.async_show_form(
                step_id="connect", data_schema=CONNECT_CONFIG, errors=errors
            )

        self._user_data.update(user_input)

        try:
            res = await self.hass.async_add_executor_job(
                self._api.request_update,
                self._user_data[CONF_AREA],
                self._user_data[CONF_CUSTOMER_ID],
                self._user_data[CONF_MONTHLY_START],
            )
        except Exception as e:
            _LOGGER.exception("Unexpected exception: {e}")
            errors["base"] = CONF_ERR_UNKNOWN
        else:
            if res["status"] != CONF_SUCCESS:
                errors["base"] = res["data"]
            else:
                return self.async_create_entry(
                    title=self._user_data[CONF_CUSTOMER_ID], data=self._user_data
                )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}

        if user_input is not None:

            self._user_data.update(user_input)

            try:
                res = await self.hass.async_add_executor_job(
                    self._api.login,
                    self._user_data[CONF_AREA],
                    self._user_data[CONF_USERNAME],
                    self._user_data[CONF_PASSWORD],
                )
            except Exception as e:
                _LOGGER.exception("Unexpected exception: {e}")
                errors["base"] = CONF_ERR_UNKNOWN
            else:
                if res != CONF_SUCCESS:
                    errors["base"] = res
                else:
                    return await self.async_step_connect()

        return self.async_show_form(
            step_id="auth", data_schema=AUTH_CONFIG, errors=errors
        )

    async def async_step_area(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}

        if user_input is None:
            return self.async_show_form(
                step_id="area", data_schema=AREA_CONFIG, errors=errors
            )

        self._user_data[CONF_AREA] = user_input[CONF_AREA]

        if user_input[CONF_AREA] == VIETNAM_EVN_AREA[0].name:
            return await self.async_step_auth()
        else:
            return await self.async_step_connect()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_area()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
