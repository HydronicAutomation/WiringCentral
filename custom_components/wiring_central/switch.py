import json
import os
import random
import time
import logging
from typing import Optional, Any

from homeassistant.components.binary_sensor import DEVICE_CLASS_OPENING
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.components import mqtt

from .const import DOMAIN

from .api_helper import WCAPIRelayStatusView, WCAPIRelayEntitiesView, WCAPIRelayEntityDetailsView, WCAPIRelayConfigurationView

DATA_ENTITIES_SWITCH = "data_WC_entities_switch"
DATA_ENTITIES_SWITCH_DETAILS = "data_WC_entities_switch_details"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    _LOGGER.info("Loading the WC sensor platform")

    hass.http.register_view(WCAPIRelayStatusView)
    hass.http.register_view(WCAPIRelayEntitiesView)
    hass.http.register_view(WCAPIRelayEntityDetailsView)
    hass.http.register_view(WCAPIRelayConfigurationView)

    if DATA_ENTITIES_SWITCH not in hass.data:
        hass.data[DATA_ENTITIES_SWITCH] = []

    if DATA_ENTITIES_SWITCH_DETAILS not in hass.data:
        hass.data[DATA_ENTITIES_SWITCH_DETAILS] = []

    @callback
    def device_config_received(msg):
        """Handle new MQTT messages."""
        _LOGGER.info("relay_config_received %s", DOMAIN)
        node_id = msg.topic.split("/")[2]
        switch_type = msg.topic.split("/")[3]
        board_id = msg.topic.split("/")[5]
        switch_id = msg.topic.split("/")[6]
        object_id = "{}-{}".format(board_id, switch_id)
        name = object_id
        # dont attempt if already added
        if object_id not in hass.data[DATA_ENTITIES_SWITCH]:
            hass.data[DATA_ENTITIES_SWITCH].append(object_id)
            # if board_id != "ESPNOW":
            hass.data[DATA_ENTITIES_SWITCH_DETAILS].append({"BOARD": board_id, "OBJECT_ID": object_id,
                                                            "TYPE": switch_type, "SWITCH": switch_id})

            entity_data = json.loads(msg.payload)
            # sensor_status = check_sensor_disabled(configHelperSensor, board_id, sensor_type, sensor_id)
            # if sensor_status:
            async_add_devices([ESwitch(
                object_id, name,board_id, entity_data)], True)
        else:
            print("Relay already added! - {}".format(object_id))

    # mqtt = hass.components.mqtt
    #  elementz/relay/wc/RELAY/config/RL-4C1EB9962BC8/1
    # mqtt.subscribe("elementz/relay/+/+/config/+/+", device_config_received)
    await mqtt.async_subscribe(
        hass, "elementz/relay/+/+/config/+/+", device_config_received, 1
    )


class ESwitch(SwitchEntity):
    """Representation of a Demo sensor."""

    def __init__(
        self, object_id, name,board_id, data
    ):
        """Initialize the sensor."""
        self.board_id = board_id
        self._unique_id = object_id
        self._name = name
        self._device_class = DEVICE_CLASS_OPENING
        self._data = data
        self.sw_version = self._data.get('sw', '1.0')
        self.hw_version = self._data.get('hw', '1.0')
        self.current_relay_status_topic = self._data['current_relay_status_topic']
        self.current_relay_control_topic = self._data.get('current_relay_control_topic')
        if self.current_relay_control_topic is None:  # For backward compatibility for Relay board version < 1.1
            data_split = self.current_relay_status_topic.split('/')
            data_split[1] = 'c'
            self.current_relay_control_topic = "/".join(data_split)
        self._state = False

    async def async_added_to_hass(self) -> None:
        result = await super().async_added_to_hass()
        _LOGGER.info("async_added_to_hass %s", self._name)
        if self.hass is not None:
            _LOGGER.info("susbcribing to mqtt %s", self._name)
            self.mqtt = self.hass.components.mqtt
            # print("!!!!!!!!!!loop_subscribe!!!!!!!")
            await self.mqtt.async_subscribe(self.current_relay_status_topic, self._set_current_temperature)
        return result

    def _set_current_temperature(self, msg):
        state = int(msg.payload) == 1
        # if self._state != state:
        self._state = state
        self.schedule_update_ha_state()

    @property
    def device_info(self):
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.board_id)},
            manufacturer="Hydronic Automation",
            model=f"WiringCentral {self.hw_version}",
            name=self.board_id,
            sw_version=self.sw_version,
        )

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def should_poll(self):
        """No polling needed for a demo sensor."""
        return False

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        # self._state = True
        self.mqtt.publish(self.hass, self.current_relay_control_topic, 1)
        print("Turning ON")

    async def async_turn_off(self, **kwargs: Any) -> None:
        # self._state = False
        self.mqtt.publish(self.hass, self.current_relay_control_topic, 0)
        print("Turning OFF")



