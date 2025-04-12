"""Platform for climate integration."""
import os
import asyncio
from pprint import pprint
import random
import time
from collections import OrderedDict
from copy import deepcopy
from typing import Optional, Any, List, Mapping

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import DOMAIN as HA_DOMAIN, callback
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (ATTR_HVAC_MODE,
                                                    DOMAIN as CLIMATE_DOMAIN, SERVICE_SET_TEMPERATURE,
                                                    SERVICE_SET_HVAC_MODE, HVACMode, ClimateEntityFeature)
from homeassistant.const import (
    ATTR_TEMPERATURE,  CONF_ALIAS, SERVICE_TURN_OFF, ATTR_TIME, WEEKDAYS,
    CONF_CONDITION, CONF_WEEKDAY, ATTR_SERVICE, SERVICE_TURN_ON,
    ATTR_ENTITY_ID, STATE_ON, CONF_AT, ATTR_STATE, UnitOfTemperature)
import json

from homeassistant.core import HomeAssistant
from homeassistant.config import AUTOMATION_CONFIG_PATH

import logging

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import Throttle
from homeassistant.util.yaml import load_yaml, dump

from .api_helper import WCAPIClimateStatusView, WCAPIClimateEntitiesView, WCAPIClimateConfigurationView, \
    WCAPIMasterSlaveConfigurationView, WCAPIDefaultRuleConfigurationView, WCAPIBoardStateConfigurationView
from .configurator import ConfiguratorHelperThermostat, ConfiguratorHelperRelay, ConfiguratorHelperMasterSlave, \
    ConfiguratorHelperDefaultRule, ConfiguratorHelperBoard

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN, MIN_TEMP, MAX_TEMP, MOVING_AVERAGE_LENGTH, ROUND_VALUE, ATTR_MAX_TEMP, \
    ATTR_MOVING_AVERAGE_LENGTH, ATTR_MIN_TEMP, ATTR_ROUND_VALUE, MIN_TIME_BETWEEN_UPDATES, \
    ATTR_HOT_TOLERANCE, ATTR_COLD_TOLERANCE, ATTR_WINDOW_METHOD, HOT_TOLERANCE, COLD_TOLERANCE, WINDOW_METHOD_ENABLE
from homeassistant.components.automation import DOMAIN as DOMAIN_AUTOMATION
from homeassistant.const import SERVICE_RELOAD, CONF_ID

from .helpers.schedule_helper import ScheduleService
from .helpers.masterslave_helper import MasterSlaveService

SENSOR_TYPE_NTC = "NTC"
SENSOR_TYPE_DS18B20 = "DS18B20"
SENSOR_TYPE_SHTC3_TEMP = "SHTC3-TEMP"
SENSOR_TYPE_MQTT = "MQTT"

SWITCH_TYPE_RELAY_BOARD = "RL-BOARD"
SWITCH_TYPE_BUILTIN = "BUILTIN"

# Values of E-Thermostaat to map to operation mode
COMFORT = 32
SAVING = 64
AWAY = 0
FIXED_TEMP = 128
temp1 = 25

SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE

# List of integration names (string) your integration depends upon.
DEPENDENCIES = ["mqtt"]

DATA_ENTITIES_CLIMATE = "data_WC_entities_climate"
DATA_WC_THERMOSTATS = "data_WC_thermostats"

AUTOMATION_MASTERSLAVE_PREFIX = 'WiringCentral:MasterSlave'
AUTOMATION_DEFAULT_PREFIX = 'WiringCentral:Default'
AUTOMATION_CUSTOM_PREFIX = 'WiringCentral:Custom'

SERVICE_TRIGGER = "trigger"

ATTR_WC_RULE_ID_DEFAULT = "ruleid_default"
ATTR_WC_STARTTIME_DEFAULT = 'starttime_default'
ATTR_WC_ENDTIME_DEFAULT = 'endtime_default'
ATTR_WC_TEMPERATURE_DEFAULT = 'target_temperature_default'
ATTR_WC_DAY_OF_WEEK_DEFAULT = 'day_of_week_default'
ATTR_WC_HVAC_MODE_DEFAULT = 'hvac_mode_default'

ATTR_WC_RULE_ID_CUSTOM = "ruleid_custom"
ATTR_WC_STARTTIME_CUSTOM = 'starttime_custom'
ATTR_WC_ENDTIME_CUSTOM = 'endtime_custom'
ATTR_WC_TEMPERATURE_CUSTOM = 'target_temperature_custom'
ATTR_WC_DAY_OF_WEEK_CUSTOM = 'day_of_week_custom'
ATTR_WC_HVAC_MODE_CUSTOM = 'hvac_mode_custom'



class BoardStateManager:
    """Manages the state of all thermostats and controls relays accordingly."""

    def __init__(self, hass):
        self.hass = hass
        self.thermostat_states = {}  # Dictionary to track thermostat states
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.boards_filename = os.path.join(dir_path, 'configuration_boards.yaml')
        self.loop = asyncio.get_running_loop()
        self.configurator = ConfiguratorHelperBoard()
        self.settings = {}

    async def init(self):
        # self.settings = await self.async_read_boards_configuration_from_file()
        self.settings = await self.loop.run_in_executor(None, self.configurator.read_boards_configuration_from_file)
        if self.settings is None:
            self.settings = {}
        return self.settings
        # self.settings - {'WC-123456': {'enable_cooler_heater_control': 1, 'enable_transformer_control': 1}}

    def update_thermostat_status(self, board_id, entity_id, status):
        """
            Update the state of a thermostat and evaluate relay control.

            Args:
                board_id (str): The ID of the thermostat's board.
                entity_id (str): The ID of the thermostat entity.
                status (str): The new status of the thermostat.  - Cooler On, Heater On, Off

            thermostat_states = {
                "board1_id": { "thermostats": [
                    {
                        "entity_id": "climate.entity_id",
                        "status": "Heater On"
                    }
                ], "heater_relay": "Off", "cooler_relay": "Off", "transformer_relay": "Off" },
                "board2_id": { "thermostats": [
                    {
                        "entity_id": "climate.entity_id",
                        "status": "Cooler On"
                    }
                ], "heater_relay": "Off", "cooler_relay": "Off", "transformer_relay": "Off" }
            }

        """

        if board_id is None or entity_id is None or status is None:
            _LOGGER.error("Invalid arguments for update_thermostat_status: board_id={}, entity_id={}, status={}".format(board_id, entity_id, status))
            return

        if board_id not in self.thermostat_states:
            self.thermostat_states[board_id] = {"thermostats": [],
                                                "heater_relay": "Off",
                                                "cooler_relay": "Off",
                                                "transformer_relay": "Off",
                                                "pump_relay": "Off",
                                                "update_time": time.time()}

        if entity_id not in [thermostat["entity_id"] for thermostat in self.thermostat_states[board_id]["thermostats"]]:
            self.thermostat_states[board_id]["thermostats"].append({"entity_id": entity_id, "status": status})

        # Update the thermostat state
        for thermostat in self.thermostat_states[board_id]["thermostats"]:
            if thermostat["entity_id"] == entity_id:
                thermostat["status"] = status
                break

        if time.time() - self.thermostat_states[board_id]["update_time"] > 10:
            if  self.settings.get(board_id) is not None and json.loads(self.settings[board_id]).get("enable_cooler_heater_control") is not None:
                self.thermostat_states[board_id]["update_time"] = time.time()
                enable_cooler_heater_control = json.loads(self.settings[board_id]).get("enable_cooler_heater_control", False)
                enable_transformer_control = json.loads(self.settings[board_id]).get("enable_transformer_control", False)
                self.evaluate_relay_state(board_id, enable_cooler_heater_control, enable_transformer_control)
            else:
                _LOGGER.error("No Heater Cooler Relay settings found for board_id: {}".format(board_id))
                return

    def evaluate_relay_state(self, board_id, enable_cooler_heater_control, enable_transformer_control):
        # print("evaluate_relay_state for board_id", board_id)
        # print("thermostat_states", self.thermostat_states)
        """Check all thermostats and control relays accordingly."""
        heater_entity_id = ("_".join(self.thermostat_states[board_id]["thermostats"][0]["entity_id"].split("_")[:-1]) + "_10").replace("climate", "switch")
        cooler_entity_id = ("_".join(self.thermostat_states[board_id]["thermostats"][0]["entity_id"].split("_")[:-1]) + "_9").replace("climate", "switch")
        transformer_entity_id = ("_".join(self.thermostat_states[board_id]["thermostats"][0]["entity_id"].split("_")[:-1]) + "_11").replace("climate", "switch")
        pump_entity_id = ("_".join(self.thermostat_states[board_id]["thermostats"][0]["entity_id"].split("_")[:-1]) + "_12").replace("climate", "switch")
        # print("heater_entity_id", heater_entity_id)
        # print("cooler_entity_id", cooler_entity_id)
        # print("transformer_entity_id", transformer_entity_id)
        # print("pump_entity_id", pump_entity_id)
        # print("status", self.thermostat_states[board_id]["thermostats"][0]["status"])

        # check if any of the thermostats are having Heater On status
        if any(thermostat["status"] == "Heater On" for thermostat in self.thermostat_states[board_id]["thermostats"]):
            if enable_cooler_heater_control:
                self.thermostat_states[board_id]["heater_relay"] = "On"
                self.thermostat_states[board_id]["cooler_relay"] = "Off"
                self.hass.create_task(
                    self.hass.services.async_call("switch", "turn_on", {"entity_id": heater_entity_id}))
                self.hass.create_task(
                    self.hass.services.async_call("switch", "turn_off", {"entity_id": cooler_entity_id}))

            if enable_transformer_control:
                self.thermostat_states[board_id]["transformer_relay"] = "On"
                self.thermostat_states[board_id]["pump_relay"] = "On"
                self.hass.create_task(self.hass.services.async_call("switch", "turn_on", {"entity_id": transformer_entity_id}))
                self.hass.create_task(self.hass.services.async_call("switch", "turn_on", {"entity_id": pump_entity_id}))
            return
        elif any(thermostat["status"] == "Cooler On" for thermostat in self.thermostat_states[board_id]["thermostats"]):
            if enable_cooler_heater_control:
                self.thermostat_states[board_id]["heater_relay"] = "Off"
                self.thermostat_states[board_id]["cooler_relay"] = "On"
                self.hass.create_task(
                    self.hass.services.async_call("switch", "turn_off", {"entity_id": heater_entity_id}))
                self.hass.create_task(
                    self.hass.services.async_call("switch", "turn_on", {"entity_id": cooler_entity_id}))

            if enable_transformer_control:
                self.thermostat_states[board_id]["transformer_relay"] = "On"
                self.thermostat_states[board_id]["pump_relay"] = "On"
                self.hass.create_task(self.hass.services.async_call("switch", "turn_on", {"entity_id": transformer_entity_id}))
                self.hass.create_task(self.hass.services.async_call("switch", "turn_on", {"entity_id": pump_entity_id}))
            return
        else:
            if enable_cooler_heater_control:
                self.thermostat_states[board_id]["heater_relay"] = "Off"
                self.thermostat_states[board_id]["cooler_relay"] = "Off"
                self.hass.create_task(
                    self.hass.services.async_call("switch", "turn_off", {"entity_id": heater_entity_id}))
                self.hass.create_task(
                    self.hass.services.async_call("switch", "turn_off", {"entity_id": cooler_entity_id}))

            if enable_transformer_control:
                self.thermostat_states[board_id]["transformer_relay"] = "Off"
                self.thermostat_states[board_id]["pump_relay"] = "Off"
                self.hass.create_task(self.hass.services.async_call("switch", "turn_off", {"entity_id": transformer_entity_id}))
                self.hass.create_task(self.hass.services.async_call("switch", "turn_off", {"entity_id": pump_entity_id}))
            return

    def save_thermostat_board_configuration(self, board, board_config):
        self.configurator.save_thermostat_board_configuration(board, board_config)

    def async_save_thermostat_board_configuration(self, board, board_config):
        self.loop.run_in_executor(None, self.configurator.save_thermostat_board_configuration, board, board_config)

    def async_read_boards_configuration_from_file(self):
        return self.loop.run_in_executor(None, self.configurator.read_boards_configuration_from_file)

    def get_board_configuration(self, board):
        config =  self.configurator.get_thermostat_board_configuration(board)
        return config
    
    def async_get_board_configuration(self, board):
        return self.loop.run_in_executor(None, self.configurator.get_thermostat_board_configuration, board)


async def check_replace_temerature_sensor_from_wcConfigurator(thermostatConfigurator: ConfiguratorHelperThermostat,
                                                        board_id, object_id):
    loop = asyncio.get_event_loop()
    config = await loop.run_in_executor(None, thermostatConfigurator.get_thermostat_configuration, board_id)
    # config = thermostatConfigurator.get_thermostat_configuration(board_id)
    if config is not None:
        json_data = json.loads(config)
        for object in json_data:
            if object.get("name") == object_id and object.get("type") == SENSOR_TYPE_NTC:
                return SENSOR_TYPE_NTC, "wc/c/{BOARD}/ctt/s/{FEED}".format(BOARD=board_id, FEED=object.get("feed")), \
                    object.get("multiplier", 1), object.get("summer", 0)
            elif object.get("name") == object_id and object.get("type") == SENSOR_TYPE_DS18B20:
                # return SENSOR_TYPE_DS18B20, "wc/s/{BOARD}/ctt/s/DS18B20/{FEED}".format(BOARD=board_id, FEED=object.get("feed"))
                return SENSOR_TYPE_DS18B20, "wc/s/{BOARD}/ctt/s/DS18B20/{FEED}".format(BOARD="+",
                                                                                       FEED=object.get("feed")), \
                    object.get("multiplier", 1), object.get("summer", 0)
            elif object.get("name") == object_id and object.get("type") == SENSOR_TYPE_SHTC3_TEMP:
                # return SENSOR_TYPE_DS18B20, "wc/s/{BOARD}/ctt/s/DS18B20/{FEED}".format(BOARD=board_id, FEED=object.get("feed"))
                return SENSOR_TYPE_DS18B20, "wc/s/{BOARD}/ctt/s/SHTC3-TEMP/{FEED}".format(BOARD="+",
                                                                                          FEED=object.get("feed")), \
                    object.get("multiplier", 1), object.get("summer", 0)
            elif object.get("name") == object_id and object.get("type") == SENSOR_TYPE_MQTT:
                return SENSOR_TYPE_MQTT, "{FEED}".format(FEED=object.get("feed")), \
                    object.get("multiplier", 1), object.get("summer", 0)

    return None, None, 1, 0


async def check_replace_relay_from_wcConfigurator(relayConfigurator: ConfiguratorHelperRelay, board_id, object_id):
    loop = asyncio.get_event_loop()
    config = await loop.run_in_executor(None, relayConfigurator.get_relay_configuration, board_id)
    # config = relayConfigurator.get_relay_configuration(board_id)
    if config is not None:
        json_data = json.loads(config)
        for object in json_data:
            if object.get("name") == object_id:
                if object.get("type") == SWITCH_TYPE_RELAY_BOARD:
                    feed = object.get("feed")
                    enabled = object.get("enable", True)
                    relay_board_id, switch_number = feed.rsplit("-", 1)
                    return SWITCH_TYPE_RELAY_BOARD, "wc/c/{BOARD}/crt/s/{FEED_ID}/{FEED_SW}".format(BOARD="RELAY",
                                                                                                    FEED_ID=relay_board_id,
                                                                                                    FEED_SW=switch_number), enabled
                elif object.get("type") == SWITCH_TYPE_BUILTIN:
                    return SWITCH_TYPE_BUILTIN, None, object.get("enable", True)
    return None, None, True


# def check_and_configure_automation_masterslave(masterslaveConfigurator: ConfiguratorHelperMasterSlave, board_id):
#     masterslave_config = masterslaveConfigurator.get_thermostat_configuration(board=board_id)
#     if masterslave_config:
#         print(masterslave_config)


# def setup_platform(hass, config, add_entities, discovery_info=None):
async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_devices):
    """Set up the climate platform."""
    # We only want this platform to be set up via discovery.
    _LOGGER.info("Loading the WC climate platform")
    print("Set up the climate platform", config_entry.data)
    print("Options", len(config_entry.options))
    platform_config = config_entry.data or {}
    if len(config_entry.options) > 0:
        platform_config = config_entry.options

    moving_avg_length = platform_config.get(ATTR_MOVING_AVERAGE_LENGTH, MOVING_AVERAGE_LENGTH)
    round_value = platform_config.get(ATTR_ROUND_VALUE, ROUND_VALUE)
    min_temp = platform_config.get(ATTR_MIN_TEMP, MIN_TEMP)
    max_temp = platform_config.get(ATTR_MAX_TEMP, MAX_TEMP)
    hot_tolerance = platform_config.get(ATTR_HOT_TOLERANCE, HOT_TOLERANCE)
    cold_tolerance = platform_config.get(ATTR_COLD_TOLERANCE, COLD_TOLERANCE)
    window_method = platform_config.get(ATTR_WINDOW_METHOD, WINDOW_METHOD_ENABLE)

    _LOGGER.debug(f"moving_avg_length {moving_avg_length}")
    _LOGGER.debug(f"round_value {round_value}")
    _LOGGER.debug(f"min_temp {min_temp}")
    _LOGGER.debug(f"max_temp {max_temp}")
    _LOGGER.debug(f"hot_tolerance {hot_tolerance}")
    _LOGGER.debug(f"cold_tolerance {cold_tolerance}")
    _LOGGER.debug(f"window_method {window_method}")


    # Manage entity cache for service handler
    if DATA_ENTITIES_CLIMATE not in hass.data:
        hass.data[DATA_ENTITIES_CLIMATE] = []

    # Mapping of thermostat names and entities
    if DATA_WC_THERMOSTATS not in hass.data:
        hass.data[DATA_WC_THERMOSTATS] = {}

    defaultRuleConfigurator = ConfiguratorHelperDefaultRule()
    # wiringcentralAutomation = WiringCentralAutomation(hass=hass)
    # scheduleCloner = ScheduleCloner(defaultRuleConfigurator=defaultRuleConfigurator)
    # scheduleService = ScheduleService(automation_helper=wiringcentralAutomation, schedule_cloner=scheduleCloner)
    scheduleService = ScheduleService()
    await scheduleService.init()
    masterslaveService = MasterSlaveService()
    await masterslaveService.init()
    boardStateManager = BoardStateManager(hass=hass)
    await boardStateManager.init()

    # Setup HTTP API views
    hass.http.register_view(WCAPIClimateStatusView)
    hass.http.register_view(WCAPIClimateEntitiesView)
    hass.http.register_view(WCAPIClimateConfigurationView(hass=hass))
    hass.http.register_view(WCAPIMasterSlaveConfigurationView(masterslaveService))
    hass.http.register_view(WCAPIDefaultRuleConfigurationView(hass, scheduleService))
    hass.http.register_view(WCAPIBoardStateConfigurationView(hass, boardStateManager))

    # if discovery_info is None:
    #     return

    thermostatConfigurator = ConfiguratorHelperThermostat()
    relayConfigurator = ConfiguratorHelperRelay()
    # masterslaveConfigurator = ConfiguratorHelperMasterSlave()

    # masterslaveAutomation = MasterSlaveAutomation(hass=hass, masterSlaveConfiguratorHelper=masterslaveConfigurator)

    # Service to publish a message on MQTT.
    # def add_device(call):
    #     """Service to send a message."""
    #     print(DOMAIN, "add_device", call)
    #
    # hass.services.register(DOMAIN, "set_state", add_device)

    @callback
    async def device_config_received(msg):
        """Handle new MQTT messages."""
        _LOGGER.info("climate_config_received %s", DOMAIN)
        print(msg.topic, msg.payload)

        node_id = msg.topic.split("/")[2]
        internal_id = msg.topic.split("/")[5]
        board_id = msg.topic.split("/")[3]
        object_id = "{}-{}".format(board_id, internal_id)
        name = object_id

        if board_id not in hass.data[DATA_WC_THERMOSTATS]:
            hass.data[DATA_WC_THERMOSTATS].update({board_id: []})

        # dont attempt if already added
        if object_id not in hass.data[DATA_ENTITIES_CLIMATE]:
            hass.data[DATA_ENTITIES_CLIMATE].append(object_id)
            entity_data = json.loads(msg.payload)

            # Support for sensor change from the WC_configurator, with required mutiplier and summer support
            sensor_type, current_temp_topic, temp_multipler, temp_summer = await check_replace_temerature_sensor_from_wcConfigurator(
                thermostatConfigurator, board_id, object_id)
            if sensor_type is not None:
                entity_data['current_temperature_topic'] = current_temp_topic
                entity_data['sensor_type'] = sensor_type

            entity_data['temp_multiplier'] = temp_multipler
            entity_data['temp_summer'] = temp_summer

            entity_data['relay_type'] = None
            entity_data['relay_command_topic'] = None
            relay_type, relay_topic, enabled = await check_replace_relay_from_wcConfigurator(relayConfigurator, board_id, object_id)
            if relay_type is not None and relay_type == SWITCH_TYPE_RELAY_BOARD:
                entity_data['relay_command_topic'] = relay_topic  # None if not configured or using Builtin
                entity_data['relay_type'] = relay_type  # None if not configured or using Builtin
                entity_data['relay_enabled'] = enabled
            elif relay_type is None or relay_type == SWITCH_TYPE_BUILTIN:
                # Using buitin Relay
                entity_data['relay_command_topic'] = entity_data.get('current_relay_control_topic')
                entity_data['relay_type'] = SWITCH_TYPE_BUILTIN
                entity_data['relay_enabled'] = enabled
            # print(object_id, entity_data['heating_element_command_topic'], entity_data['relay_type'])

            # Support for sensor change from the platform configuration of configuration.yaml
            # preference given to platform configuration for Tasmota support
            # sensor_type, current_temp_topic = check_replace_temperature_sensor_from_platformconfig(platform_config, object_id)
            # if sensor_type is not None:
            #     entity_data['current_temperature_topic'] = current_temp_topic
            #     entity_data['sensor_type'] = sensor_type

            entity_data[ATTR_MOVING_AVERAGE_LENGTH] = moving_avg_length
            entity_data[ATTR_ROUND_VALUE] = round_value
            entity_data[ATTR_MIN_TEMP] = min_temp
            entity_data[ATTR_MAX_TEMP] = max_temp

            # temp_multipler, temp_summer = check_replace_temperature_multiplier_summmer_from_platformconfig(
            #     platform_config, object_id)
            # entity_data['temp_multiplier'] = temp_multipler
            # entity_data['temp_summer'] = temp_summer

            # hot_tolerance, cold_tolerance, window_method = check_replace_hysterisis_method_from_platformconfig(
            #     platform_config, object_id)
            # entity_data['hot_tolerance'] = hot_tolerance
            # entity_data['cold_tolerance'] = cold_tolerance
            # entity_data['window_method'] = window_method

            entity_data['hot_tolerance'] = hot_tolerance
            entity_data['cold_tolerance'] = cold_tolerance
            entity_data['window_method'] = window_method

            entity_data['board_id'] = board_id

            async_add_devices([EThermostat(
                name=name, node_id=node_id, object_id=object_id, data=entity_data,
                schedule_service=scheduleService,
                thermostat_state_manager=boardStateManager)], True)
        else:
            print("Thermostat already added! - {}".format(object_id))

    # mqtt = hass.components.mqtt
    # mqtt.subscribe("elementz/climate/+/+/config/+", device_config_received)
    # mqtt.publish(hass, "elementz/discover", "")
    await mqtt.async_subscribe(
        hass, "elementz/climate/+/+/config/+", device_config_received, 1
    )
    await mqtt.async_publish(hass, "elementz/discover", "")
    _LOGGER.info("setup_platform %s", DOMAIN)

    def handle_schedule(call):
        """Handle the service call."""
        # name = call.data.get(ATTR_NAME, DEFAULT_NAME)
        _LOGGER.info("schedule service: %s", DOMAIN)
        # hass.states.set("hello_service.hello", name)
        entity_id = call.data.get("entity_id")
        schedule_data = call.data.get("data", {})

        for entity in hass.data['climate'].entities:
            print(entity)

        scheduleService.add_service_data(entity_id, schedule_data)

        hass.bus.fire(f"{DOMAIN}_appdaemon_reload", {})


        # scheduleService.get_service_topic(hass, entity_id)

        # scheduleService.push_service_data(hass, entity_id, schedule_data)  ##

        # inputStateObject = hass.states.get(entity_id)
        # inputState = inputStateObject.state
        # inputAttributesObject = inputStateObject.attributes.copy()
        # inputAttributesObject["schedule"] ={"data": [4, 5, 6]}
        # hass.states.set(entity_id, inputState, inputAttributesObject)

    def handle_schedule_clear(call):
        """Handle the service call."""
        # name = call.data.get(ATTR_NAME, DEFAULT_NAME)
        _LOGGER.info("schedule service: %s", DOMAIN)
        # hass.states.set("hello_service.hello", name)
        entity_id = call.data.get("entity_id")
        schedule_data = call.data.get("data", {})

        scheduleService.clear_service_data(entity_id)

        hass.bus.fire(f"{DOMAIN}_appdaemon_reload", {})
        # scheduleService.get_service_topic(hass, entity_id)

        # scheduleService.push_service_data(hass, entity_id, schedule_data)  ##

        # inputStateObject = hass.states.get(entity_id)
        # inputState = inputStateObject.state
        # inputAttributesObject = inputStateObject.attributes.copy()
        # inputAttributesObject["schedule"] ={"data": [4, 5, 6]}
        # hass.states.set(entity_id, inputState, inputAttributesObject)

    def handle_masterslave(call):
        _LOGGER.info("handle_masterslave service: %s", DOMAIN)
        # board_id = call.data.get("board_id")
        # if board_id:
        #     # check_and_configure_automation_masterslave(masterslaveConfigurator, board_id)
        #     # masterslaveAutomation.save_automations(board=board_id)
        #     pass
        hass.bus.fire(f"{DOMAIN}_appdaemon_reload", {})

    # Listener to handle fired events
    def handle_getdata_request_event(event):
        # nonlocal count
        # count += 1
        # print(f"Answer {count} is: {event.data.get('answer')}")
        _LOGGER.info("handle_getdata_request_event called")
        pprint(event.data)
        hass.bus.fire(f"{DOMAIN}_data", {'schedules': scheduleService.data, 'masterslaves': masterslaveService.masterslave_data})

    # Listen for when example_component_my_cool_event is fired
    hass.bus.async_listen(f"{DOMAIN}_getdata_request", handle_getdata_request_event)

    # hass.services.register(DOMAIN, "schedule", handle_schedule)
    # hass.services.register(DOMAIN, "masterslave", handle_masterslave)

    hass.services.async_register(DOMAIN, "schedule", handle_schedule)
    hass.services.async_register(DOMAIN, "schedule_clear", handle_schedule_clear)
    hass.services.async_register(DOMAIN, "masterslave", handle_masterslave)


    # hass.states.set("{}.scheduledata".format(DOMAIN), {})


class EThermostat(ClimateEntity):
    """Representation of a E-Thermostaat device."""

    def __init__(self, name, node_id, object_id, data, schedule_service: ScheduleService,
                 thermostat_state_manager: BoardStateManager):
        """Initialize the thermostat."""
        _LOGGER.info(f"EThermostat adding : {object_id}")
        self._unique_id = object_id
        self._name = name
        self.node_id = node_id
        self.object_id = object_id
        self.scheduleService = schedule_service
        self.thermostatStateManager = thermostat_state_manager

        self._data = data
        self.sensor_type = data.get('sensor_type', SENSOR_TYPE_NTC)

        self.current_temperature_topic = self._data['current_temperature_topic']
        self.board_id = self._data['board_id']
        self.sw_version = self._data.get('sw', '1.0')
        self.hw_version = self._data.get('hw', '1.0')
        self.mode_command_topic = self._data['mode_command_topic']
        self.mode_state_topic = self._data['mode_state_topic']
        self._modes = self._data['modes']
        # self.temperature_low_command_topic = self._data['temperature_low_command_topic']
        # self.temperature_low_state_topic = self._data['temperature_low_state_topic']
        # self.temperature_high_command_topic = self._data['temperature_high_command_topic']
        # self.temperature_high_state_topic = self._data['temperature_high_state_topic']
        self.target_temperature_command_topic = self._data['target_temperature_command_topic']
        self.target_temperature_state_topic = self._data['target_temperature_state_topic']
        self._min_temp = float(self._data[ATTR_MIN_TEMP])
        self._max_temp = float(self._data[ATTR_MAX_TEMP])
        self._temp_step = float(self._data['temp_step'])
        self.service_command_topic = self._data['service_command_topic']
        self.service_state_topic = self._data['service_state_topic']
        self.heating_element_command_topic = self._data['heating_element_command_topic']
        self.relay_type = self._data['relay_type']
        self.relay_command_topic = self._data['relay_command_topic']
        self.relay_enabled = self._data.get('relay_enabled', True)
        self.moving_avg_length = self._data[ATTR_MOVING_AVERAGE_LENGTH]
        self.round_value = self._data[ATTR_ROUND_VALUE]
        self.temp_multiplier = self._data['temp_multiplier']
        self.temp_summer = self._data['temp_summer']
        # self.service_topic = "elementz/command/{}/{}/schedule".format(node_id,object_id)

        # Internal variables
        self._mode = HVACMode.OFF
        self._current_temperature = self._min_temp
        self._target_temperature = self._max_temp
        self._target_temp_low = self._min_temp
        self._target_temp_high = self._max_temp
        self._current_operation_mode = None

        self.min_cycle_duration = 60
        self.hot_tolerance = self._data['hot_tolerance']
        self.cold_tolerance = self._data['cold_tolerance']
        self.window_method = self._data['window_method']

        self.last_changed_millis = 0

        self.heater_cooler_status = 'Off'

        self.previous_temperatures = []

        self._icon = "mdi:power"
        print(self.name, self.hot_tolerance, self.cold_tolerance, self.window_method)

        self.background_tasks = []

    # @property
    # def device_class(self) -> str:
    #     return super().device_class()

    async def async_added_to_hass(self) -> None:
        result = await super().async_added_to_hass()
        _LOGGER.info("async_added_to_hass %s", self._name)

        if self.hass is not None:
            _LOGGER.info("susbcribing to mqtt %s", self._name)
            # print("!!!!!!!!!!loop_subscribe!!!!!!!")
            await mqtt.async_subscribe(self.hass, self.current_temperature_topic, self._set_current_temperature_from_mqtt)
            await mqtt.async_subscribe(self.hass, self.mode_state_topic, self._set_mode_from_mqtt)
            await mqtt.async_subscribe(self.hass, self.target_temperature_state_topic, self._set_target_temperature_from_mqtt)
            await mqtt.async_subscribe(self.hass, self.service_state_topic, self._set_device_service_data_from_mqtt)
            print("!!!!!!!!!!loop_subscribed!!!!!!!")

            print(self.entity_id)
            self.hass.data[DATA_WC_THERMOSTATS][self.board_id].append({"ENTITY_ID": self.entity_id,
                                                                       "OBJECT_ID": self.object_id})
            pprint(self.hass.data[DATA_WC_THERMOSTATS])
            # self.scheduleService.add_service_topic(self.entity_id, self.service_command_topic)
            # print("!!!!!!!!!!loop_subscribed  123 !!!!!!!")

            # await self.async_thermostat_turn_on()

            # set initial mode to OFF on startup
            self._mode = HVACMode.OFF
        return result

    def _set_device_service_data_from_mqtt(self, msg):
        # print("MQTT:  set state attributes received", msg)
        self.scheduleService.add_service_data(self.entity_id, json.loads(msg.payload))
        self.schedule_update_ha_state()

    def _get_moving_average(self, temp):
        self.previous_temperatures.append(temp)
        if len(self.previous_temperatures) > self.moving_avg_length:
            self.previous_temperatures.pop(0)

        # print("Previous temp", self.previous_temperatures, " avg", sum(self.previous_temperatures) / len(self.previous_temperatures))
        return round(sum(self.previous_temperatures) / len(self.previous_temperatures), 1)

    def _round_value(self, number):
        if self.round_value == 0:
            return number

        return round(number / self.round_value) * self.round_value

    def _apply_linear_mutiply_sum(self, number):
        return (number * self.temp_multiplier) + self.temp_summer

    def _set_current_temperature_from_mqtt(self, msg):
        # print("MQTT:  _set_current_temperature_from_mqtt received", msg)
        _LOGGER.info("MQTT: _set_current_temperature_from_mqtt %s", msg)
        self._current_temperature = float(msg.payload)

        # moving average
        if self.moving_avg_length > 0:
            self._current_temperature = self._get_moving_average(self._current_temperature)

        # Apply mutiplier and summer ( Mx + C)
        self._current_temperature = self._apply_linear_mutiply_sum(self._current_temperature)

        # round to nearest 0.5
        if self.round_value > 0:
            self._current_temperature = self._round_value(self._current_temperature)

        self._set_current_temperature_and_refresh_heater(self._current_temperature)

    def _set_current_temperature_and_refresh_heater(self, temperature_last_updated):
        temperature_last_updated = float(temperature_last_updated)
        # control heating/cooling according to the current state
        update_flag = False
        if self._mode == HVACMode.HEAT:
            if time.time() - self.last_changed_millis > self.min_cycle_duration:
                if self.window_method:
                    # Enter in window method for cycling t between T-C and T+H
                    if temperature_last_updated > self._target_temperature + self.hot_tolerance:
                        self.hass.add_job(self.async_heater_element_off)  # t > T + H - Turnoff heater
                        update_flag = True
                    elif temperature_last_updated < (self._target_temperature - self.cold_tolerance):
                        self.hass.add_job(self.async_heater_element_on)  # t < (T - C) - Turn on heater
                        update_flag = True
                    else:
                        update_flag = True  # No change if T-C < t < T + H
                else:
                    # Enter if not window method, normal behaviour
                    if temperature_last_updated > self._target_temperature + self.hot_tolerance:
                        self.hass.add_job(self.async_heater_element_off)  # Turn off heater at t  > T + H
                        update_flag = True
                    else:
                        self.hass.add_job(self.async_heater_element_on)
                        update_flag = True
        elif self._mode == HVACMode.COOL:
            if time.time() - self.last_changed_millis > self.min_cycle_duration:
                if self.window_method:
                    if temperature_last_updated < (self._target_temperature - self.cold_tolerance):
                        self.hass.add_job(self.async_cooler_element_off)  # Turn off cooler at t < T - C
                        update_flag = True
                    elif temperature_last_updated > (self._target_temperature + self.hot_tolerance):
                        self.hass.add_job(self.async_cooler_element_on)  # Turn on cooler when t > T + H
                        update_flag = True
                    else:
                        update_flag = True  # No change if T-C < t < T + H
                else:
                    if temperature_last_updated < (self._target_temperature - self.cold_tolerance):
                        self.hass.add_job(self.async_cooler_element_off)  # Turn off cooler at t < T - C
                        update_flag = True
                    else:
                        self.hass.add_job(self.async_cooler_element_on)
                        update_flag = True
        elif self._mode == HVACMode.OFF:
            self.heater_cooler_status = "Off"

        if update_flag:
            self.last_changed_millis = time.time()

        self.thermostatStateManager.update_thermostat_status(self.board_id, self.entity_id, self.heater_cooler_status)

        # if self._name == 'WC-12345678-1':
        #     print("WC-12345678-1", temperature, self.heater_cooler_status)
        #     pass

        self.schedule_update_ha_state()

    def _set_mode_from_mqtt(self, msg):
        # _LOGGER.info("MQTT: Mode update from hardware received")
        # print("MQTT:  Mode received", msg)
        # self.icon =
        self._mode = msg.payload
        self.last_changed_millis = 0  # override minimum cycle duration if mode changed
        self.schedule_update_ha_state()

    def _set_target_temperature_from_mqtt(self, msg):
        # _LOGGER.info("MQTT: Target Temp update from hardware received")
        # print("MQTT:  Target Temp received", msg)
        self._target_temperature = float(msg.payload)
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
    def extra_state_attributes(self) -> Optional[Mapping[str, Any]]:
        state_attributes = self.state_attributes
        state_attributes["schedule"] = self.scheduleService.get_service_data(entity_id=self.entity_id)
        state_attributes["heater_cooler_status"] = self.heater_cooler_status
        state_attributes["platform"] = DOMAIN
        # print("device_state_attributes: ", state_attributes)
        # print(self.entity_id)
        return state_attributes

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def should_poll(self):
        """Polling is required."""
        return True

    async def async_device_update(self, warning: bool = True) -> None:
        """Handle polling."""
        _LOGGER.info("async_device_update %s", self._name)

        # Force refresh of current temperature
        # ESPNOW sensors will send data every 6 minutes only.
        self._set_current_temperature_and_refresh_heater(self._current_temperature)
        return await self.refresh_relay()

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def refresh_relay(self):
        # _LOGGER.warning("refresh_relay starting")
        if self.hass is not None:
            # _LOGGER.warning(f"refresh_relay for {self.entity_id}")
            if self.heater_cooler_status == "Heater On" or self.heater_cooler_status == "Cooler On":
                mqtt.publish(self.hass, self.heating_element_command_topic, payload=self.heater_cooler_status)
                if self.relay_enabled and self.relay_type is not None and (self.relay_type == SWITCH_TYPE_RELAY_BOARD or self.relay_type == SWITCH_TYPE_BUILTIN):
                    if self.relay_command_topic is not None:
                        # mqtt.publish(self.hass, self.relay_command_topic, "1")
                        task = self.hass.async_create_task(self.delay_and_call_relay("1"))
                        self.background_tasks.append(task)
            else:
                mqtt.publish(self.hass, self.heating_element_command_topic, self.heater_cooler_status)
                if self.relay_enabled and self.relay_type is not None and (
                        self.relay_type == SWITCH_TYPE_RELAY_BOARD or self.relay_type == SWITCH_TYPE_BUILTIN):
                    if self.relay_command_topic is not None:
                        self.remove_background_tasks()
                        mqtt.publish(self.hass, self.relay_command_topic, "0")
        # _LOGGER.warning("refresh_relay finished")
        return

    def remove_background_tasks(self):
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
                _LOGGER.warning("Cancelled task ")
            # Remove the task from the list of background tasks
            self.background_tasks.remove(task)
        # self.background_tasks = []

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def target_temperature_low(self):
        """Return the low target temperature we try to reach."""
        return self._target_temp_low

    @property
    def target_temperature_high(self):
        """Return the high target temperature we try to reach."""
        return self._target_temp_high

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._temp_step

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode."""
        return self._mode

    @property
    def hvac_modes(self):
        """HVAC modes."""
        return self._modes

    @property
    def icon(self) -> Optional[str]:
        if self._mode == HVACMode.OFF:
            return 'mdi:power'
        elif self._mode == HVACMode.HEAT:
            return 'mdi:fire'
        elif self._mode == HVACMode.COOL:
            return 'mdi:snowflake'
        return self._icon

    # Buiiltin function
    def set_temperature(self, **kwargs) -> None:
        _LOGGER.info("set_temperature called")
        self._target_temperature = kwargs.get('temperature', None)
        mqtt.publish(self.hass, self.target_temperature_command_topic, self._target_temperature)

    # built in function
    def set_hvac_mode(self, hvac_mode: str) -> None:
        self._mode = hvac_mode
        _LOGGER.info("mode change %s", hvac_mode)
        mqtt.publish(self.hass, self.mode_command_topic, self._mode)
        if self.relay_type is not None and (self.relay_type == SWITCH_TYPE_RELAY_BOARD or self.relay_type == SWITCH_TYPE_BUILTIN):
            if self._mode == HVACMode.OFF:
                if self.relay_command_topic is not None:
                    self.remove_background_tasks()   # Needed if a relay ON with delay is already pending
                    mqtt.publish(self.hass, self.relay_command_topic, "0")

    async def delay_and_call_relay(self, logic):
        await asyncio.sleep(random.randint(1, 24))
        mqtt.publish(self.hass, self.relay_command_topic, logic)

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    async def _async_control_heating(self):
        return

    async def async_heater_element_on(self) -> None:
        if self.hass is not None:
            self.heater_cooler_status = "Heater On"
            mqtt.publish(self.hass, self.heating_element_command_topic, payload="Heater On")
            if self.relay_enabled and self.relay_type is not None and (self.relay_type == SWITCH_TYPE_RELAY_BOARD or self.relay_type == SWITCH_TYPE_BUILTIN):
                if self.relay_command_topic is not None:
                    # mqtt.publish(self.hass, self.relay_command_topic, "1")
                    task = self.hass.async_create_task(self.delay_and_call_relay("1"))
                    self.background_tasks.append(task)

    async def async_heater_element_off(self) -> None:
        if self.hass is not None:
            self.heater_cooler_status = "Heater Off"
            mqtt.publish(self.hass, self.heating_element_command_topic, payload="Heater Off")
            if self.relay_enabled and self.relay_type is not None and (self.relay_type == SWITCH_TYPE_RELAY_BOARD or self.relay_type == SWITCH_TYPE_BUILTIN):
                if self.relay_command_topic is not None:
                    self.remove_background_tasks()
                    mqtt.publish(self.hass, self.relay_command_topic, "0")
                    # self.hass.async_create_task(self.delay_and_call_relay("0"))

    async def async_cooler_element_on(self) -> None:
        if self.hass is not None:
            self.heater_cooler_status = "Cooler On"
            mqtt.publish(self.hass, self.heating_element_command_topic, "Cooler On")
            if self.relay_type is not None and (self.relay_type == SWITCH_TYPE_RELAY_BOARD or self.relay_type == SWITCH_TYPE_BUILTIN):
                if self.relay_command_topic is not None:
                    # mqtt.publish(self.hass, self.relay_command_topic, "1")
                    task = self.hass.async_create_task(self.delay_and_call_relay("1"))
                    self.background_tasks.append(task)

    async def async_cooler_element_off(self) -> None:
        if self.hass is not None:
            self.heater_cooler_status = "Cooler Off"
            mqtt.publish(self.hass, self.heating_element_command_topic, "Cooler Off")
            if self.relay_type is not None and (self.relay_type == SWITCH_TYPE_RELAY_BOARD or self.relay_type == SWITCH_TYPE_BUILTIN):
                if self.relay_command_topic is not None:
                    self.remove_background_tasks()
                    mqtt.publish(self.hass, self.relay_command_topic, "0")
                    # self.hass.async_create_task(self.delay_and_call_relay("0"))

    async def async_thermostat_turn_on(self) -> None:
        """Turn thermostat to on."""
        _LOGGER.info("async_thermostat_turn_on")
        await self.hass.services.async_call(HA_DOMAIN, SERVICE_TURN_ON,
                                            {ATTR_ENTITY_ID: self.entity_id})

    async def async_thermostat_turn_off(self) -> None:
        """Turn thermostat to off."""
        _LOGGER.info("async_thermostat_turn_off")
        await self.hass.services.async_call(HA_DOMAIN, SERVICE_TURN_OFF,
                                            {ATTR_ENTITY_ID: self.entity_id})

    async def _async_set_mode_off(self):
        """Turn mode to off."""
        await self.hass.services.async_call(CLIMATE_DOMAIN, SERVICE_SET_HVAC_MODE,
                                            {ATTR_ENTITY_ID: self.entity_id, ATTR_HVAC_MODE: HVACMode.OFF})

    async def _async_set_mode_heating(self):
        """Turn mode to heat."""
        await self.hass.services.async_call(CLIMATE_DOMAIN, SERVICE_SET_HVAC_MODE,
                                            {ATTR_ENTITY_ID: self.entity_id, ATTR_HVAC_MODE: HVACMode.HEAT})

    async def _async_set_mode_cooling(self):
        """Turn mode to cool."""
        await self.hass.services.async_call(CLIMATE_DOMAIN, SERVICE_SET_HVAC_MODE,
                                            {ATTR_ENTITY_ID: self.entity_id, ATTR_HVAC_MODE: HVACMode.COOL})


def _read_automations_from_file(automation_path):
    """Read YAML helper."""
    if not os.path.isfile(automation_path):
        return None

    return load_yaml(automation_path)


def _write_automations_to_file(automation_path, automations):
    """Write YAML helper."""
    # Do it before opening file. If dump causes error it will now not
    # truncate the file.
    data = dump(automations)
    # print(data)
    with open(automation_path, "w", encoding="utf-8") as outfile:
        outfile.write(data)


class WiringCentralAutomation:
    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__()
        self.default_type = True
        self.custom_type = False
        self.hass = hass
        self.automation_path = self.hass.config.path(AUTOMATION_CONFIG_PATH)
        self.automations = _read_automations_from_file(self.hass.config.path(AUTOMATION_CONFIG_PATH))
        print("==========Printing all - automations =========")
        print(len(self.automations), self.automations)
        # _write_automations_to_file(self.hass.config.path(AUTOMATION_CONFIG_PATH), self.automations)

        # print("config directory path", hass.config.config_dir)
        # print("automation config path", AUTOMATION_CONFIG_PATH)
        # print("automation full path", hass.config.path(AUTOMATION_CONFIG_PATH))
        # print("automation rules ", _read(hass.config.path(AUTOMATION_CONFIG_PATH)))

    def get_automations(self, entity_id):
        entity_default_automations = []
        entity_custom_automations = []
        for automation in self.automations:
            valid, automation_type = self.check_automation_for_entity(entity_id, automation)
            if valid:
                if automation_type == self.default_type:
                    entity_default_automations.append(automation)
                if automation_type == self.custom_type:
                    entity_custom_automations.append(automation)
        return entity_default_automations, entity_custom_automations

    def check_automation_for_entity(self, entity, automation):
        """
        :param entity: wiringcentral entity
        :param automation: HA automation rule
        :return: isWiringCentralEntity, entityType
        """
        isWiringCentralEntity, entityType = False, False
        if automation[CONF_ID].startswith(AUTOMATION_DEFAULT_PREFIX):
            try:
                if automation['action'][0]['data'][ATTR_ENTITY_ID] == entity:
                    isWiringCentralEntity, entityType = True, self.default_type
            except:
                pass
        elif automation[CONF_ID].startswith(AUTOMATION_CUSTOM_PREFIX):
            try:
                if automation['action'][0]['data'][ATTR_ENTITY_ID] == entity:
                    isWiringCentralEntity, entityType = True, self.custom_type
            except:
                pass
        return isWiringCentralEntity, entityType

    def delete_automations_for_entity(self, entity, automations):
        if not isinstance(automations, List):
            return []

        _automations = deepcopy(automations)
        for automation in _automations:
            isWiringCentralEntity, entityType = self.check_automation_for_entity(entity, automation)
            if isWiringCentralEntity:
                automations.remove(automation)

        return automations

    def save_automations(self, entity, automations, default_status):
        # save automations back to file
        if automations is None:
            return

        # Needed for loading automation changes done from HA Automation editpr
        self.automations = _read_automations_from_file(self.hass.config.path(AUTOMATION_CONFIG_PATH))
        old_automations = self.delete_automations_for_entity(entity, self.automations)
        print("before change", len(old_automations))
        # print(old_automations)

        for automation in automations:
            # updateFlag = False
            # for index, old_automation in enumerate(old_automations):
            #     if old_automation.get(CONF_ID, "") == automation[CONF_ID]:
            #         old_automations[index] = automation
            #         updateFlag = True
            #         print("######## Update #############")
            # if not updateFlag:
            old_automations.append(automation)

        print("after change", len(old_automations))
        # print(old_automations)

        _write_automations_to_file(self.automation_path, old_automations)

        # refresh the automation variable
        self.automations = _read_automations_from_file(self.hass.config.path(AUTOMATION_CONFIG_PATH))
        self.reload_automation()

        self.set_on_off_default_automations(entity, automations, default_status)

    def reload_automation(self):
        self.hass.services.call(DOMAIN_AUTOMATION, SERVICE_RELOAD)

    def get_automation_stateObj_from_states(self, automation_id):
        return None

    def get_on_off_default_automations(self, entity, default_automation_rules):
        ha_states = self.hass.states._states

        wiringCentral_entities = []
        for ha_state in ha_states:
            if self.hass.states._states[ha_state].domain == DOMAIN_AUTOMATION:
                if self.hass.states._states[ha_state].attributes.get(CONF_ID, None) == None:
                    continue
                if self.hass.states._states[ha_state].attributes[CONF_ID].startswith(AUTOMATION_DEFAULT_PREFIX):
                    wiringCentral_entities.append({ATTR_ENTITY_ID: self.hass.states._states[ha_state].entity_id,
                                                   CONF_ID: self.hass.states._states[ha_state].attributes[CONF_ID]})
        print(wiringCentral_entities)

        # Loop through entity default automations
        for automation in default_automation_rules:
            isWiringCentralEntity, entityType = self.check_automation_for_entity(entity, automation)
            # check if the automation is for the default schedule
            if isWiringCentralEntity and entityType == self.default_type:
                # call turnoff/turnon of automation based on the automation entityid
                for wiringCentral_entity in wiringCentral_entities:
                    if wiringCentral_entity[CONF_ID] == automation[CONF_ID]:
                        print("getting state from automation", automation)
                        return self.hass.states.get(wiringCentral_entity['entity_id']).state == STATE_ON

        return False

    def set_on_off_default_automations(self, entity, automations, default_status):
        ha_states = self.hass.states._states

        # Get the wiringcentral automation entities alone from automation states
        wiringCentral_entities = []
        for ha_state in ha_states:
            if self.hass.states._states[ha_state].domain == DOMAIN_AUTOMATION:
                if self.hass.states._states[ha_state].attributes.get(CONF_ID, None) == None:
                    continue
                if self.hass.states._states[ha_state].attributes[CONF_ID].startswith(AUTOMATION_DEFAULT_PREFIX):
                    wiringCentral_entities.append({ATTR_ENTITY_ID: self.hass.states._states[ha_state].entity_id,
                                                   CONF_ID: self.hass.states._states[ha_state].attributes[CONF_ID]})

        # Loop through all entity automations
        for automation in automations:
            isWiringCentralEntity, entityType = self.check_automation_for_entity(entity, automation)
            # check if the automation is for the default schedule
            if isWiringCentralEntity and entityType == self.default_type:
                # call turnoff/turnon of automation based on the automation entityid
                for wiringCentral_entity in wiringCentral_entities:
                    if wiringCentral_entity[CONF_ID] == automation[CONF_ID]:
                        print("setting state {} for automation".format(default_status), automation)
                        if default_status:
                            self.hass.services.call(DOMAIN_AUTOMATION, SERVICE_TURN_ON,
                                                    {ATTR_ENTITY_ID: wiringCentral_entity[ATTR_ENTITY_ID]})
                        else:
                            self.hass.services.call(DOMAIN_AUTOMATION, SERVICE_TURN_OFF,
                                                    {ATTR_ENTITY_ID: wiringCentral_entity[ATTR_ENTITY_ID]})


class ScheduleCloner:
    def __init__(self, defaultRuleConfigurator: ConfiguratorHelperDefaultRule) -> None:
        super().__init__()
        self.defaultRuleConfigurator = defaultRuleConfigurator
        self.exclude_list = set()
        self.default_rules = []
        self.update_config_from_file()

    def save_entity_to_default_rule_exclusion(self, entity):
        self.update_config_from_file()  # Reread the file
        if entity not in self.exclude_list:
            self.exclude_list.add(entity)
        print("Exclude list ", self.exclude_list)
        self.defaultRuleConfigurator.save_exclusion_list_configuration('', exclusion_list=json.dumps(
            list(self.exclude_list)))
        self.update_config_from_file()

    def save_default_rule_tofile(self, default_rules):
        self.update_config_from_file()  # Reread the file
        self.defaultRuleConfigurator.save_defaultrule_configuration('',
                                                                    defaultrule_config=json.dumps(list(default_rules)))
        self.update_config_from_file()
        print("default_rules saving ", default_rules)

    def update_config_from_file(self):
        exclude_list = self.defaultRuleConfigurator.get_exclusion_list_configuration('')
        default_rules = self.defaultRuleConfigurator.get_defaultrule_configuration('')
        if exclude_list is not None:
            self.exclude_list = set(json.loads(exclude_list))
        if default_rules is not None:
            self.default_rules = json.loads(default_rules)

    def get_default_rules_for_entity(self, entity, old_rules):
        # self.read_default_rules_from_file()
        if entity in self.exclude_list:
            return old_rules
        rules = []
        for rule in self.default_rules:
            rule[ATTR_WC_RULE_ID_DEFAULT] = "{}_Cloned:{}:{}".format(AUTOMATION_DEFAULT_PREFIX, random.randint(0, 1000),
                                                                     int(time.time()))
            rules.append(rule)
        return rules


class ScheduleService1:
    """
    TOPIC:  elementz_room/climate/wiringcentral1/service_topic/command
    DATA:
    b'{"default": [
        {"ruleid_default": "Rule 1", "starttime_default": "0:0", "endtime_default": "1:0", "target_temperature_default": 10.1, "day_of_week_default": "Mon - Fri", "onoff_default": false}
        ],
    "custom": [
        {"ruleid_custom": "Rule 1", "starttime_custom": "0:0", "endtime_custom": "1:0", "target_temperature_custom": 10.1, "day_of_week_custom": "Mon", "onoff_custom": false}
        ],
    "status": true}'


    """

    def __init__(self, automation_helper: WiringCentralAutomation, schedule_cloner: ScheduleCloner) -> None:
        super().__init__()
        self.automation_helper = automation_helper
        self.schedule_cloner = schedule_cloner
        self.data = {}
        self.topics = {}

    def get_service_data(self, entity):
        """ Called from the entity get attribute"""
        # _LOGGER.info("service data get")
        data = {"default": [], "custom": [], "status": False}
        # Enter if schedule data is read for the first time, load rules from the automations.yaml
        if self.data.get(entity, None) is None:
            default_automations, custom_automations = self.automation_helper.get_automations(entity)
            default, custom, status = self.convert_automations_to_schedule_data(entity, default_automations,
                                                                                custom_automations)
            # default = self.schedule_cloner.get_default_rules(entity, default)
            data = {"default": default, "custom": custom, "status": status}
            self.add_service_data(entity, data)

        service_data = self.data.get(entity, data)
        # returns the same default rule if the entity is in excluded list
        service_data["default"] = self.schedule_cloner.get_default_rules_for_entity(entity, service_data["default"])
        return service_data

    def convert_default_automation_to_schedule(self, automation_rule):
        """Return the schedule data in format
        {"ruleid_default": "Rule 1", "starttime_default": "0:0", "endtime_default": "1:0", "target_temperature_default": 10.1, "day_of_week_default": "Mon - Fri", "onoff_default": false}
        """
        rule = {}
        try:
            rule[ATTR_WC_RULE_ID_DEFAULT] = automation_rule[CONF_ID]
            rule[ATTR_WC_STARTTIME_DEFAULT] = automation_rule[SERVICE_TRIGGER][0][CONF_AT]
            rule[ATTR_WC_ENDTIME_DEFAULT] = automation_rule[SERVICE_TRIGGER][1][CONF_AT]
            rule[ATTR_WC_TEMPERATURE_DEFAULT] = automation_rule["action"][0]['data'][ATTR_TEMPERATURE]
            rule[ATTR_WC_DAY_OF_WEEK_DEFAULT] = "Mon - Fri" if automation_rule[CONF_CONDITION][0][CONF_WEEKDAY][
                                                                   0] == WEEKDAYS[0] else "Sat - Sun"
            template_data = automation_rule["action"][1]['data_template'][ATTR_HVAC_MODE]
            start_index = template_data.find('\'')
            end_index = template_data.find('\'', start_index + 1)
            rule[ATTR_WC_HVAC_MODE_DEFAULT] = template_data[start_index + 1:end_index].capitalize()
        except Exception as e:
            _LOGGER.info("Exception on convert_default_automation_to_schedule {}".format(e.__str__()))
            return None
        return rule

    def convert_custom_automation_to_schedule(self, automation_rule):
        """Return the schedule data in format
        {"ruleid_custom": "Rule 1", "starttime_custom": "0:0", "endtime_custom": "1:0", "target_temperature_custom": 10.1, "day_of_week_custom": "Mon", "onoff_custom": false}
        """
        rule = {}
        try:
            rule[ATTR_WC_RULE_ID_CUSTOM] = automation_rule[CONF_ID]
            rule[ATTR_WC_STARTTIME_CUSTOM] = automation_rule[SERVICE_TRIGGER][0][CONF_AT]
            rule[ATTR_WC_ENDTIME_CUSTOM] = automation_rule[SERVICE_TRIGGER][1][CONF_AT]
            rule[ATTR_WC_TEMPERATURE_CUSTOM] = automation_rule["action"][0]['data'][ATTR_TEMPERATURE]
            rule[ATTR_WC_DAY_OF_WEEK_CUSTOM] = automation_rule[CONF_CONDITION][0][CONF_WEEKDAY][0].capitalize()
            template_data = automation_rule["action"][1]['data_template'][ATTR_HVAC_MODE]
            start_index = template_data.find('\'')
            end_index = template_data.find('\'', start_index + 1)
            rule[ATTR_WC_HVAC_MODE_CUSTOM] = template_data[start_index + 1:end_index].capitalize()
        except Exception as e:
            _LOGGER.info("Exception on convert_custom_automation_to_schedule {}".format(e.__str__()))
            return None
        return rule

    def convert_default_schedule_to_automation(self, entity, schedule_default_rule):
        automation = OrderedDict()
        automation[CONF_ID] = schedule_default_rule[ATTR_WC_RULE_ID_DEFAULT]
        automation[CONF_ALIAS] = '{}-{} {}'.format(AUTOMATION_DEFAULT_PREFIX, entity,
                                                   schedule_default_rule[ATTR_WC_HVAC_MODE_DEFAULT])
        automation['description'] = AUTOMATION_DEFAULT_PREFIX

        trigger0 = OrderedDict()
        trigger0['at'] = schedule_default_rule[ATTR_WC_STARTTIME_DEFAULT]
        trigger0['platform'] = ATTR_TIME
        trigger1 = OrderedDict()
        trigger1['at'] = schedule_default_rule[ATTR_WC_ENDTIME_DEFAULT]
        trigger1['platform'] = ATTR_TIME

        automation['trigger'] = []
        automation['trigger'].append(trigger0)
        automation['trigger'].append(trigger1)

        condition = OrderedDict()
        # condition[CONF_AFTER] = schedule_default_rule['starttime_default']
        # condition[CONF_BEFORE] = schedule_default_rule['endtime_default']
        condition[CONF_CONDITION] = ATTR_TIME
        condition[CONF_WEEKDAY] = WEEKDAYS[0:5] if schedule_default_rule[
                                                       ATTR_WC_DAY_OF_WEEK_DEFAULT] == 'Mon - Fri' else WEEKDAYS[5:]

        automation[CONF_CONDITION] = [condition]

        action0 = OrderedDict()
        action0['data'] = OrderedDict()
        action0['data']['entity_id'] = entity
        action0['data'][ATTR_TEMPERATURE] = float(schedule_default_rule[ATTR_WC_TEMPERATURE_DEFAULT])
        action0[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_TEMPERATURE)

        action1 = OrderedDict()
        action1['data_template'] = OrderedDict()
        action1['data_template']['entity_id'] = entity
        # action1['data_template'][ATTR_HVAC_MODE] = schedule_default_rule['hvac_mode_default'].lower()
        action1['data_template'][
            ATTR_HVAC_MODE] = "{{{{ '{}' if now().hour |int == {} and now().minute |int == {} else 'off' }}}}".format(
            schedule_default_rule[ATTR_WC_HVAC_MODE_DEFAULT].lower(),
            int(schedule_default_rule[ATTR_WC_STARTTIME_DEFAULT].split(':')[0]),
            int(schedule_default_rule[ATTR_WC_STARTTIME_DEFAULT].split(':')[1]))
        action1[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_HVAC_MODE)

        # action1 = OrderedDict()
        # if schedule_default_rule['onoff_default']:
        #     action1['data'] = OrderedDict()
        #     action1['data']['entity_id'] = entity
        #     action1['data'][ATTR_HVAC_MODE] = HVACMode.HEAT_COOL
        #     action1[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_HVAC_MODE)
        # else:
        #     action1['data'] = OrderedDict()
        #     action1['data']['entity_id'] = entity
        #     action1[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_TURN_OFF)

        automation['action'] = []
        automation['action'].append(action0)
        automation['action'].append(action1)
        return automation

    def convert_custom_schedule_to_automation(self, entity, schedule_custom_rule):
        automation = OrderedDict()
        automation[CONF_ID] = schedule_custom_rule[ATTR_WC_RULE_ID_CUSTOM]
        automation[CONF_ALIAS] = '{}-{} {}'.format(AUTOMATION_CUSTOM_PREFIX, entity,
                                                   schedule_custom_rule[ATTR_WC_HVAC_MODE_CUSTOM])
        automation['description'] = AUTOMATION_CUSTOM_PREFIX

        trigger0 = OrderedDict()
        trigger0['at'] = schedule_custom_rule[ATTR_WC_STARTTIME_CUSTOM]
        trigger0['platform'] = ATTR_TIME
        trigger1 = OrderedDict()
        trigger1['at'] = schedule_custom_rule[ATTR_WC_ENDTIME_CUSTOM]
        trigger1['platform'] = ATTR_TIME

        automation['trigger'] = []
        automation['trigger'].append(trigger0)
        automation['trigger'].append(trigger1)

        condition = OrderedDict()
        # condition[CONF_AFTER] = schedule_custom_rule['starttime_custom']
        # condition[CONF_BEFORE] = schedule_custom_rule['endtime_custom']
        condition[CONF_CONDITION] = ATTR_TIME
        condition[CONF_WEEKDAY] = [schedule_custom_rule[ATTR_WC_DAY_OF_WEEK_CUSTOM].lower()]

        automation[CONF_CONDITION] = [condition]

        action0 = OrderedDict()
        action0['data'] = OrderedDict()
        action0['data']['entity_id'] = entity
        action0['data'][ATTR_TEMPERATURE] = float(schedule_custom_rule[ATTR_WC_TEMPERATURE_CUSTOM])
        action0[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_TEMPERATURE)

        action1 = OrderedDict()
        action1['data_template'] = OrderedDict()
        action1['data_template']['entity_id'] = entity
        # action1['data'][ATTR_HVAC_MODE] = schedule_custom_rule['hvac_mode_custom'].lower()

        action1['data_template'][
            ATTR_HVAC_MODE] = "{{{{ '{}' if now().hour |int == {} and now().minute |int == {} else 'off' }}}}".format(
            schedule_custom_rule[ATTR_WC_HVAC_MODE_CUSTOM].lower(),
            int(schedule_custom_rule[ATTR_WC_STARTTIME_CUSTOM].split(':')[0]),
            int(schedule_custom_rule[ATTR_WC_STARTTIME_CUSTOM].split(':')[1]))
        action1[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_HVAC_MODE)

        # action1 = OrderedDict()
        # if schedule_custom_rule['onoff_custom']:
        #     action1['data'] = OrderedDict()
        #     action1['data']['entity_id'] = entity
        #     action1['data'][ATTR_HVAC_MODE] = HVACMode.HEAT_COOL
        #     action1[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_HVAC_MODE)
        # else:
        #     action1['data'] = OrderedDict()
        #     action1['data']['entity_id'] = entity
        #     action1[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_TURN_OFF)

        automation['action'] = []
        automation['action'].append(action0)
        automation['action'].append(action1)

        return automation

    def save_entity_to_default_rule_exclusion(self, entity, automations):
        self.schedule_cloner.save_entity_to_default_rule_exclusion(entity)
        # self.schedule_cloner.save_default_rule_tofile(automations)

    def convert_schedule_data_to_automations(self, entity, schedule_data):
        # convert the default, custom to automation rules
        automations = []
        print(self.automation_helper.automations)
        schedule_default_rules = schedule_data.get('default', [])
        schedule_default_status = schedule_data.get('status', False)
        schedule_custom_rules = schedule_data.get('custom', [])

        for schedule_default_rule in schedule_default_rules:
            automation = self.convert_default_schedule_to_automation(entity, schedule_default_rule)
            if automation is not None:
                automations.append(automation)

        for schedule_custom_rule in schedule_custom_rules:
            automation = self.convert_custom_schedule_to_automation(entity, schedule_custom_rule)
            if automation is not None:
                automations.append(automation)

        return automations, schedule_default_status

    def convert_automations_to_schedule_data(self, entity, default_rules, custom_rules):
        default = []
        custom = []
        status = self.automation_helper.get_on_off_default_automations(entity, default_rules)

        for automation_rule in default_rules:
            schedule_rule = self.convert_default_automation_to_schedule(automation_rule=automation_rule)
            if schedule_rule is not None:
                default.append(schedule_rule)
        for automation_rule in custom_rules:
            schedule_rule = self.convert_custom_automation_to_schedule(automation_rule=automation_rule)
            if schedule_rule is not None:
                custom.append(schedule_rule)
        return default, custom, status

    def add_service_data(self, entity, data):
        self.data[entity] = data
        _LOGGER.info("service data add")

    def get_service_topic(self, entity):
        # _LOGGER.info("service topic get")
        return self.topics.get(entity, None)

    def add_service_topic(self, entity, data):
        self.topics[entity] = data
        _LOGGER.info("service topic add")

    def push_service_data(self, hass, entity, data):
        _LOGGER.info("service topic pushing")
        # data = self.data.get(entity, None)
        topic = self.topics.get(entity, None)
        print(topic, data)
        mqtt = hass.components.mqtt
        mqtt.publish(hass, topic, json.dumps(data))
        _LOGGER.info("service topic pushed")

        self.add_service_data(entity, data)

        automations, schedule_default_status = self.convert_schedule_data_to_automations(entity, data)
        self.automation_helper.save_automations(entity, automations, schedule_default_status)
        self.save_entity_to_default_rule_exclusion(entity, data.get('default', []))


class MasterSlaveAutomation:
    def __init__(self, hass: HomeAssistant, masterSlaveConfiguratorHelper: ConfiguratorHelperMasterSlave) -> None:
        super().__init__()
        self.hass = hass
        self.automation_path = self.hass.config.path(AUTOMATION_CONFIG_PATH)
        self.masterSlaveConfiguratorHelper = masterSlaveConfiguratorHelper

    def convert_name_to_entityID(self, domain, name):
        return "{}.{}".format(domain, name.replace('-', '_').lower())

    def convert_entityID_to_name(self, domain, entity_id):
        _, id_ = entity_id.split('.')
        return id_.replace('_', '-').upper()

    def check_automation_for_entity(self, entity, automation):
        """
        :param entity: wiringcentral entity
        :param automation: HA automation rule
        :return: isWiringCentralEntity
        """
        isWiringCentralEntity = False
        if automation[CONF_ID].startswith(AUTOMATION_MASTERSLAVE_PREFIX):
            try:
                if automation['action'][0]['data_template'][ATTR_ENTITY_ID] == entity:
                    isWiringCentralEntity = True
            except:
                pass
        return isWiringCentralEntity

    def check_automation_for_board(self, board, automation):
        isWiringCentralEntity = False
        for i in range(1, 9):
            entity_id = self.convert_name_to_entityID(domain=CLIMATE_DOMAIN, name="{}-{}".format(board, i))
            if self.check_automation_for_entity(entity=entity_id, automation=automation):
                isWiringCentralEntity = True
                return isWiringCentralEntity
        return isWiringCentralEntity

    def delete_automations_for_board(self, board, automations):
        if not isinstance(automations, List):
            return []

        _automations = deepcopy(automations)
        for automation in _automations:
            isWiringCentralEntity = self.check_automation_for_board(board=board, automation=automation)
            if isWiringCentralEntity:
                automations.remove(automation)

        return automations

    def convert_masterslaverule_to_automation(self, master_name, slave_name):
        master_entity_id = self.convert_name_to_entityID(domain="climate", name=master_name)
        slave_entity_id = self.convert_name_to_entityID(domain="climate", name=slave_name)
        automation = OrderedDict()
        automation[CONF_ID] = "{}:{}:{}".format(AUTOMATION_MASTERSLAVE_PREFIX, random.randint(0, 1000),
                                                int(time.time()))
        automation[CONF_ALIAS] = '{}-{}'.format(AUTOMATION_MASTERSLAVE_PREFIX, slave_entity_id)
        automation['description'] = '{}-{}'.format(AUTOMATION_MASTERSLAVE_PREFIX, slave_entity_id)

        trigger0 = OrderedDict()
        trigger0['entity_id'] = master_entity_id
        trigger0['platform'] = ATTR_STATE

        automation['trigger'] = []
        automation['trigger'].append(trigger0)

        automation[CONF_CONDITION] = []

        action0 = OrderedDict()
        action0['data_template'] = OrderedDict()
        action0['data_template']['entity_id'] = slave_entity_id
        action0['data_template'][ATTR_HVAC_MODE] = "{{{{ states.{}.state }}}}".format(master_entity_id)
        action0[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_HVAC_MODE)
        #
        action1 = OrderedDict()
        action1['data_template'] = OrderedDict()
        action1['data_template']['entity_id'] = slave_entity_id
        action1['data_template'][ATTR_TEMPERATURE] = "{{{{ state_attr('{}', 'temperature') }}}}".format(
            master_entity_id)
        action1[ATTR_SERVICE] = '{DOMAIN}.{SERVICE}'.format(DOMAIN=CLIMATE_DOMAIN, SERVICE=SERVICE_SET_TEMPERATURE)

        automation['action'] = []
        automation['action'].append(action0)
        automation['action'].append(action1)

        return automation

    def create_masterslave_automations(self, masterslaveConfig):
        print(masterslaveConfig)
        masterslaveAutomations = []
        for config in masterslaveConfig:
            if config["master"] != "NO FOLLOW":
                masterslaveAutomations.append(self.convert_masterslaverule_to_automation(master_name=config["master"],
                                                                                         slave_name=config["name"]))
        print("===========================")
        print(masterslaveAutomations)
        return masterslaveAutomations

    def save_automations(self, board):
        masterslaveConfig = self.masterSlaveConfiguratorHelper.get_thermostat_configuration(board=board)
        masterslave_automations = []
        if masterslaveConfig is not None:
            masterslave_automations = self.create_masterslave_automations(json.loads(masterslaveConfig))

        self.automations = _read_automations_from_file(self.hass.config.path(AUTOMATION_CONFIG_PATH))

        # delete all existing master slave config for the board
        old_automations = self.delete_automations_for_board(board, self.automations)

        # Needed for loading automation changes done from HA Automation editpr
        for masterslave_automation in masterslave_automations:
            updateFlag = False
            for index, old_automation in enumerate(old_automations):
                if old_automation.get(CONF_ID, "") == masterslave_automation[CONF_ID]:
                    old_automations[index] = masterslave_automation
                    updateFlag = True
            if not updateFlag:
                old_automations.append(masterslave_automation)

        print("after change")
        print(old_automations)

        _write_automations_to_file(self.automation_path, old_automations)

        # refresh the automation variable
        self.automations = _read_automations_from_file(self.hass.config.path(AUTOMATION_CONFIG_PATH))
        self.reload_automation()

    def reload_automation(self):
        self.hass.services.call(DOMAIN_AUTOMATION, SERVICE_RELOAD)
