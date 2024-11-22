import logging

from homeassistant import config_entries, data_entry_flow
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo
from homeassistant.core import callback

from .const import DOMAIN, MOVING_AVERAGE_LENGTH, ROUND_VALUE, MAX_TEMP, MIN_TEMP, ATTR_MOVING_AVERAGE_LENGTH, \
    ATTR_MAX_TEMP, ATTR_MIN_TEMP, ATTR_ROUND_VALUE, ATTR_HOT_TOLERANCE, ATTR_COLD_TOLERANCE, ATTR_WINDOW_METHOD, \
    HOT_TOLERANCE, COLD_TOLERANCE, WINDOW_METHOD_ENABLE

import voluptuous as vol
_LOGGER = logging.getLogger(__name__)


class WCConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        errors = {}
        # Specify items in the order they are to be displayed in the UI
        data_schema = vol.Schema(
            {
                vol.Required(ATTR_MOVING_AVERAGE_LENGTH, default=MOVING_AVERAGE_LENGTH): vol.All(int,
                                                                                                 vol.Range(min=0,
                                                                                                           max=10)),
                vol.Required(ATTR_ROUND_VALUE, default=ROUND_VALUE): vol.All(float, vol.Range(min=0.1, max=0.9)),
                vol.Required(ATTR_MIN_TEMP, default=MIN_TEMP): vol.All(int, vol.Range(min=0, max=15)),
                vol.Required(ATTR_MAX_TEMP, default=MAX_TEMP): vol.All(int, vol.Range(min=16, max=100)),
                vol.Required(ATTR_WINDOW_METHOD, default=WINDOW_METHOD_ENABLE): bool,
                vol.Required(ATTR_HOT_TOLERANCE, default=HOT_TOLERANCE): vol.All(float, vol.Range(min=0.1, max=2.5)),
                vol.Required(ATTR_COLD_TOLERANCE, default=COLD_TOLERANCE): vol.All(float, vol.Range(min=0.1, max=2.5)),
            }
        )

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=data_schema, errors=errors
            )

        self.data = user_input

        is_valid = self.data[ATTR_MAX_TEMP] > self.data[ATTR_MIN_TEMP]
        if not is_valid:
            errors["base"] = "min_max_error"
            return self.async_show_form(
                step_id="user", data_schema=data_schema, errors=errors
            )

        if self.hass.data.get(DOMAIN, None) is not None and self.hass.data[DOMAIN].__len__() > 0:
            errors["base"] = "exist_error"
            return self.async_show_form(
                step_id="user", data_schema=data_schema, errors=errors
            )

        return self.async_create_entry(
            title="Wiring Central",
            data=self.data,
        )

    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> data_entry_flow.FlowResult:
        _LOGGER.debug(f"async_step_mqtt: {discovery_info}")
        if self.hass.data.get(DOMAIN, None) is not None and self.hass.data[DOMAIN].__len__() > 0:
            return self.async_abort(reason="already_configured")
        self.data = {}
        return self.async_create_entry(
                    title="Wiring Central",
                    data=self.data,
                )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input=None)

    async def async_step_user(
            self, user_input
    ):
        if user_input is not None:
            _LOGGER.info("OptionsFlowHandler: saving options ")
            return self.async_create_entry(title="Wiring Central", data=user_input)

        config_entry = self.config_entry.data
        if len(self.config_entry.options) > 0:
            config_entry = self.config_entry.options

        data_schema = vol.Schema(
            {
                vol.Required(ATTR_MOVING_AVERAGE_LENGTH, default=config_entry.get(ATTR_MOVING_AVERAGE_LENGTH, MOVING_AVERAGE_LENGTH)): vol.All(int,
                                                                                                 vol.Range(min=0,
                                                                                                           max=10)),
                vol.Required(ATTR_ROUND_VALUE, default=config_entry.get(ATTR_ROUND_VALUE, ROUND_VALUE)): vol.All(float, vol.Range(min=0.1, max=0.9)),
                vol.Required(ATTR_MIN_TEMP, default=config_entry.get(ATTR_MIN_TEMP, MIN_TEMP)): vol.All(int, vol.Range(min=0, max=15)),
                vol.Required(ATTR_MAX_TEMP, default=config_entry.get(ATTR_MAX_TEMP, MAX_TEMP)): vol.All(int, vol.Range(min=16, max=100)),
                vol.Required(ATTR_WINDOW_METHOD, default=config_entry.get(ATTR_WINDOW_METHOD, WINDOW_METHOD_ENABLE)): bool,
                vol.Required(ATTR_HOT_TOLERANCE, default=config_entry.get(ATTR_HOT_TOLERANCE, HOT_TOLERANCE)): vol.All(float, vol.Range(min=0.1, max=2.5)),
                vol.Required(ATTR_COLD_TOLERANCE, default=config_entry.get(ATTR_COLD_TOLERANCE, COLD_TOLERANCE)): vol.All(float, vol.Range(min=0.1, max=2.5)),

            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )