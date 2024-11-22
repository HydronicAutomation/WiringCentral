"""Platform for sensor integration."""
import json
import os
import random
import time
import logging
from typing import Optional

from homeassistant.components import mqtt
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.const import (
    DEVICE_CLASS_TEMPERATURE,
    TEMP_CELSIUS,
    DEVICE_CLASS_HUMIDITY, PERCENTAGE)
from homeassistant.core import HomeAssistant, callback
from .const import DOMAIN, ATTR_MOVING_AVERAGE_LENGTH, MOVING_AVERAGE_LENGTH
from .api_helper import WCAPISensorStatusView, WCAPISensorEntitiesView, WCAPISensorBoardDetailsView, \
    WCAPISensorEntityDetailsView, WCAPISensorBoardsView, WCAPISensorConfigurationView
from .configurator import ConfiguratorHelperSensor

DATA_ENTITIES_SENSOR = "data_WC_entities_sensor"
DATA_ENTITIES_SENSOR_DETAILS = "data_WC_entities_sensor_details"

_LOGGER = logging.getLogger(__name__)


def check_sensor_disabled(sensor_configurator, board_id, sensor_type, sensor_id):
    config = sensor_configurator.get_sensor_configuration(board_id)
    if config is not None:
        json_data = json.loads(config)
        for sensor_config in json_data:
            if sensor_config.get('type') == sensor_type and sensor_config.get('feed') == sensor_id:
                return sensor_config.get('enabled', False)
    return True


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_devices):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    _LOGGER.info("Loading the WC sensor platform")

    hass.http.register_view(WCAPISensorStatusView)
    hass.http.register_view(WCAPISensorEntitiesView)
    hass.http.register_view(WCAPISensorEntityDetailsView)
    hass.http.register_view(WCAPISensorBoardDetailsView)
    hass.http.register_view(WCAPISensorBoardsView)
    hass.http.register_view(WCAPISensorConfigurationView)

    platform_config = config_entry.data or {}
    if len(config_entry.options) > 0:
        platform_config = config_entry.options

    moving_avg_length = platform_config.get(ATTR_MOVING_AVERAGE_LENGTH, MOVING_AVERAGE_LENGTH)

    if DATA_ENTITIES_SENSOR not in hass.data:
        hass.data[DATA_ENTITIES_SENSOR] = []

    if DATA_ENTITIES_SENSOR_DETAILS not in hass.data:
        hass.data[DATA_ENTITIES_SENSOR_DETAILS] = []

    configHelperSensor = ConfiguratorHelperSensor()

    @callback
    def device_config_received(msg):
        """Handle new MQTT messages."""
        _LOGGER.info("sensor_config_received %s", DOMAIN)
        node_id = msg.topic.split("/")[2]
        board_id = msg.topic.split("/")[3]
        sensor_type = msg.topic.split("/")[5]
        bus_id = msg.topic.split("/")[6]
        index_id = msg.topic.split("/")[7]
        sensor_id = msg.topic.split("/")[8]
        object_id = "{}-{}-{}".format(board_id, sensor_type, sensor_id)
        name = object_id
        # dont attempt if already added
        if object_id not in hass.data[DATA_ENTITIES_SENSOR]:
            hass.data[DATA_ENTITIES_SENSOR].append(object_id)
            # if board_id != "ESPNOW":
            hass.data[DATA_ENTITIES_SENSOR_DETAILS].append({"BOARD": board_id, "OBJECT_ID": object_id, "TYPE": sensor_type, "BUS": bus_id, "INDEX": index_id, "SENSOR": sensor_id})

            entity_data = json.loads(msg.payload)
            sensor_status = check_sensor_disabled(configHelperSensor, board_id, sensor_type, sensor_id)
            if sensor_status:
                entity_data[ATTR_MOVING_AVERAGE_LENGTH] = moving_avg_length
                async_add_devices([ESensor(
                    object_id, name, board_id, entity_data)], True)
        else:
            print("Sensor already added! - {}".format(object_id))


    # mqtt = hass.components.mqtt
    # mqtt.subscribe("elementz/sensor/+/+/config/+/+/+/+", device_config_received)
    await mqtt.async_subscribe(
        hass, "elementz/sensor/+/+/config/+/+/+/+", device_config_received, 1
    )


class ESensor(Entity):
    """Representation of a Demo sensor."""

    def __init__(
        self, unique_id, name,board_id, data
    ):
        """Initialize the sensor."""
        self.board_id = board_id
        self._unique_id = unique_id
        self._name = name
        self._current_temperature = 0
        self._device_class = DEVICE_CLASS_TEMPERATURE
        self._unit_of_measurement = TEMP_CELSIUS
        if self._unique_id.find("SHTC3-HUM") > 0:
            self._device_class = DEVICE_CLASS_HUMIDITY
            self._unit_of_measurement = PERCENTAGE
        self._data = data

        self.sw_version = self._data.get('sw', '1.0')
        self.hw_version = self._data.get('hw', '1.0')
        self.current_temperature_topic = self._data['current_temperature_topic']
        self.moving_avg_length = self._data['moving_avg_length']

        self.previous_temperatures = []

    async def async_added_to_hass(self) -> None:
        result = await super().async_added_to_hass()
        _LOGGER.info("async_added_to_hass %s", self._name)
        if self.hass is not None:
            _LOGGER.info("susbcribing to mqtt %s", self._name)
            self.mqtt = self.hass.components.mqtt
            # print("!!!!!!!!!!loop_subscribe!!!!!!!")
            await self.mqtt.async_subscribe(self.current_temperature_topic, self._set_current_temperature)

        return result

    def _get_moving_average(self, temp):
        self.previous_temperatures.append(temp)
        if len(self.previous_temperatures) > self.moving_avg_length:
            self.previous_temperatures.pop(0)

        # print("Previous sensor temp", self.previous_temperatures, " avg", sum(self.previous_temperatures) / len(self.previous_temperatures))
        return round(sum(self.previous_temperatures) / len(self.previous_temperatures),1)

    def _set_current_temperature(self, msg):
        self._current_temperature = float(msg.payload)

        if self.moving_avg_length > 0:
            self._current_temperature = self._get_moving_average(self._current_temperature)

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
    def state(self):
        """Return the state of the sensor."""
        return self._current_temperature

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement




