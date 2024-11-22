import os
import json
from pprint import pprint
from homeassistant.components.http import HomeAssistantView, KEY_HASS
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .configurator import ConfiguratorHelperThermostat, ConfiguratorHelperSensor, ConfiguratorHelperRelay, \
    ConfiguratorHelperMasterSlave, ConfiguratorHelperDefaultRule
from .helpers.schedule_helper import ScheduleService
from .helpers.masterslave_helper import MasterSlaveService

DATA_WC_THERMOSTATS = "data_WC_thermostats"

DATA_ENTITIES_CLIMATE = "data_WC_entities_climate"
DATA_ENTITIES_SENSOR = "data_WC_entities_sensor"
DATA_ENTITIES_SENSOR_DETAILS = "data_WC_entities_sensor_details"
DATA_ENTITIES_SWITCH = "data_WC_entities_switch"
DATA_ENTITIES_SWITCH_DETAILS = "data_WC_entities_switch_details"

URL_WC_CLIMATE_API = "/api/wc/climate/status"
URL_WC_CLIMATE_ENTITIES = "/api/wc/climate/entities"

URL_WC_RELAY_API = "/api/wc/sensor/status"
URL_WC_RELAY_ENTITIES = "/api/wc/relay/entities"
URL_WC_RELAY_ENTITY_DETAILS = "/api/wc/relay/entity/details"

URL_WC_SENSOR_API = "/api/wc/sensor/status"
URL_WC_SENSOR_ENTITIES = "/api/wc/sensor/entities"
URL_WC_SENSOR_BOARDS = "/api/wc/sensor/boards"
URL_WC_SENSOR_ENTITY_DETAILS = "/api/wc/sensor/entity/details"
URL_WC_SENSOR_BOARD_DETAILS = "/api/wc/sensor/board/{board_id}"

URL_WC_CLIMATE_BOARD_MASTERSLAVE_CONFIGURATION = "/api/wc/climate/board_masterslave/configuration/{board_id}"
URL_WC_CLIMATE_BOARD_DEFAULT_RULE_CONFIGURATION = "/api/wc/climate/default_rule/configuration/{board_id}"
URL_WC_CLIMATE_BOARD_CONFIGURATION = "/api/wc/climate/board/configuration/{board_id}"
URL_WC_SENSOR_BOARD_CONFIGURATION = "/api/wc/sensor/board/configuration/{board_id}"
URL_WC_RELAY_BOARD_CONFIGURATION = "/api/wc/relay/board/configuration/{board_id}"


class WCAPIClimateEntitiesView(HomeAssistantView):
    """View to handle Climate Entity requests."""

    url = URL_WC_CLIMATE_ENTITIES
    name = "api:wc:climate:entities"

    @callback
    def get(self, request):
        """Get all climate entities registered using WC."""
        return self.json(request.app["hass"].data[DATA_ENTITIES_CLIMATE])


class WCAPIClimateStatusView(HomeAssistantView):
    """View to handle Climate Status requests."""

    url = URL_WC_CLIMATE_API
    name = "api:wc:climate:status"

    @callback
    def get(self, request):
        """Retrieve if API is running."""
        return self.json_message("WC Climate Platform running.")


class WCAPISensorBoardDetailsView(HomeAssistantView):
    """View to handle Board Senror requests."""

    url = URL_WC_SENSOR_BOARD_DETAILS
    name = "api:wc:sensor:board:board-id"

    @callback
    def get(self, request, board_id):
        """Get all sensor entity details registered using WC for the Board"""
        board_data = []
        all_data = request.app["hass"].data[DATA_ENTITIES_SENSOR_DETAILS]
        for data in all_data:
            if data.get("BOARD", "") == board_id or data.get("BOARD", "") == "ESPNOW":
                board_data.append(data)
        print("board_data")
        print(board_data)
        return self.json(board_data)


class WCAPISensorBoardsView(HomeAssistantView):
    """View to handle Boards requests."""

    url = URL_WC_SENSOR_BOARDS
    name = "api:wc:sensor:boards"

    @callback
    def get(self, request):
        """Get all boards registered using WC for the Board"""
        boards = []
        all_data = request.app["hass"].data[DATA_ENTITIES_SENSOR_DETAILS]
        for data in all_data:
            if data.get("BOARD", "") not in boards and data.get("BOARD", "") != "ESPNOW":
                boards.append(data.get("BOARD", ""))
        return self.json(boards)


class WCAPISensorEntityDetailsView(HomeAssistantView):
    """View to handle Sensor Entities requests."""

    url = URL_WC_SENSOR_ENTITY_DETAILS
    name = "api:wc:sensor:entity:details"

    @callback
    def get(self, request):
        """Get all sensor entity details registered using WC."""
        return self.json(request.app["hass"].data[DATA_ENTITIES_SENSOR_DETAILS])


class WCAPISensorEntitiesView(HomeAssistantView):
    """View to handle Status requests."""

    url = URL_WC_SENSOR_ENTITIES
    name = "api:wc:sensor:entities"

    @callback
    def get(self, request):
        """Get all sensor entities registered using WC."""
        return self.json(request.app["hass"].data[DATA_ENTITIES_SENSOR])


class WCAPISensorStatusView(HomeAssistantView):
    """View to handle Status requests."""

    url = URL_WC_SENSOR_API
    name = "api:wc:sensor:status"

    @callback
    def get(self, request):
        """Retrieve if API is running."""
        return self.json_message("WC Sensor Platform running.")


class WCAPIRelayStatusView(HomeAssistantView):
    """View to handle Status requests."""

    url = URL_WC_RELAY_API
    name = "api:wc:relay:status"

    @callback
    def get(self, request):
        """Retrieve if API is running."""
        return self.json_message("WC Relay Platform running.")


class WCAPIRelayEntitiesView(HomeAssistantView):
    """View to handle Status requests."""

    url = URL_WC_RELAY_ENTITIES
    name = "api:wc:relay:entities"

    @callback
    def get(self, request):
        """Get all sensor entities registered using WC."""
        return self.json(request.app["hass"].data[DATA_ENTITIES_SWITCH])


class WCAPIRelayEntityDetailsView(HomeAssistantView):
    """View to handle Relay Entities requests."""

    url = URL_WC_RELAY_ENTITY_DETAILS
    name = "api:wc:relay:entity:details"

    @callback
    def get(self, request):
        """Get all sensor entity details registered using WC."""
        return self.json(request.app["hass"].data[DATA_ENTITIES_SWITCH_DETAILS])


class WCAPIClimateConfigurationView(HomeAssistantView):
    """View to handle thermostat configuration requests."""

    url = URL_WC_CLIMATE_BOARD_CONFIGURATION
    name = "api:wc:climate:board:configuration"
    dir_path = os.path.dirname(os.path.realpath(__file__))

    @callback
    def get(self, request, board_id):
        json_data = []
        try:
            thermostat_configurator = ConfiguratorHelperThermostat()
            config = thermostat_configurator.get_thermostat_configuration(board_id)
            if config is not None:
                json_data = json.loads(config)
            # f = open(f"{self.dir_path}/{board_id}.txt", "r")
            # json_data = f.readline()
            # f.close()
        except Exception as e:
            print("Exception {}".format(e))
        return self.json(json_data)

    async def post(self, request, board_id):
        body = await request.text()
        try:
            event_data = json.loads(body) if body else None
            if event_data is not None:
                thermostat_configurator = ConfiguratorHelperThermostat()
                thermostat_configurator.save_thermostat_configuration(board_id, event_data)
                # f = open(f"{self.dir_path}/{board_id}.txt", "w")
                # f.write(event_data)
                # f.close()

        except ValueError:
            return self.json_message(
                "Event data should be valid JSON."
            )
        except Exception as e:
            print("Exception {}".format(e))
            raise Exception
        return self.json_message(f"{board_id} - {event_data}")


class WCAPIMasterSlaveConfigurationView(HomeAssistantView):
    """View to handle thermostat configuration requests."""

    url = URL_WC_CLIMATE_BOARD_MASTERSLAVE_CONFIGURATION
    name = "api:wc:climate:board_masterslave:configuration"
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, masterslaveService: MasterSlaveService) -> None:
        super().__init__()
        self.masterslaveService = masterslaveService


    @callback
    def get(self, request, board_id):
        data = []
        try:
            config = self.masterslaveService.get_masterslave_settings_for_board(board_id)
            if config is not None:
                data = config
            else:
                hass = request.app[KEY_HASS]
                objects = hass.data[DATA_WC_THERMOSTATS].get(board_id, [])
                for object in objects:
                    data.append({"object_id": object['OBJECT_ID'], 'master_object_id': None})

        except Exception as e:
            print("Exception WCAPIMasterSlaveConfigurationView {}".format(e))

        return self.json(data)

    async def post(self, request, board_id):
        body = await request.text()
        try:
            event_data = json.loads(body) if body else None
            if event_data is not None:
                print(event_data)
                # print("--------- WCAPIMasterSlaveConfigurationView ---------")
                # pprint(event_data)
                # masterslave_configurator = ConfiguratorHelperMasterSlave()
                # masterslave_configurator.save_thermostat_configuration(board_id, event_data)
                self.masterslaveService.save_masterslave_settings_for_board(board_id, event_data)
                # f = open(f"{self.dir_path}/{board_id}.txt", "w")
                # f.write(event_data)
                # f.close()
                # call masterslave service
                # print("calling  masterslave")
                hass = request.app[KEY_HASS]
                await hass.services.async_call(DOMAIN, "masterslave", {"board_id": board_id})
                # print("called")
        except ValueError:
            return self.json_message(
                "Event data should be valid JSON."
            )
        except Exception as e:
            print("Exception {}".format(e))
            raise Exception
        return self.json_message(f"{board_id} - {event_data}")


class WCAPIDefaultRuleConfigurationView(HomeAssistantView):
    """View to handle thermostat configuration requests."""

    url = URL_WC_CLIMATE_BOARD_DEFAULT_RULE_CONFIGURATION
    name = "api:wc:climate:default_rule:configuration"
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, scheduleService: ScheduleService) -> None:
        super().__init__()
        self.scheduleService = scheduleService

    @callback
    def get(self, request, board_id):
        data = []
        try:
            # default_configurator = ConfiguratorHelperDefaultRule()
            config = self.scheduleService.get_defaultrule_configuration()
            if config is not None:
                # json_data = json.loads(config)
                data = config
            # f = open(f"{self.dir_path}/{board_id}.txt", "r")
            # json_data = f.readline()
            # f.close()
            print("Default rule config getting ", config)

        except Exception as e:
            print("Exception {}".format(e))
        return self.json(data)

    async def post(self, request, board_id):
        body = await request.text()
        try:
            event_data = json.loads(body) if body else None
            if event_data is not None:
                print(type(event_data))
                # defaultrule_configurator = ConfiguratorHelperDefaultRule()
                self.scheduleService.save_defaultrule_configuration(event_data)
                # f = open(f"{self.dir_path}/{board_id}.txt", "w")
                # f.write(event_data)
                # f.close()
                # call masterslave service
                print("saved new default configuration")
                # hass = request.app[KEY_HASS]
                # await hass.services.async_call(DOMAIN, "masterslave", {"board_id": board_id})
                # print("called")
        except ValueError:
            return self.json_message(
                "Event data should be valid JSON."
            )
        except Exception as e:
            print("Exception {}".format(e))
            raise Exception
        return self.json_message(f"{board_id} - {event_data}")


class WCAPISensorConfigurationView(HomeAssistantView):
    """View to handle thermostat configuration requests."""

    url = URL_WC_SENSOR_BOARD_CONFIGURATION
    name = "api:wc:sensor:board:configuration"
    dir_path = os.path.dirname(os.path.realpath(__file__))

    @callback
    def get(self, request, board_id):
        json_data = []
        try:
            sensor_configurator = ConfiguratorHelperSensor()
            config = sensor_configurator.get_sensor_configuration(board_id)
            if config is not None:
                json_data = json.loads(config)
            # f = open(f"{self.dir_path}/{board_id}.txt", "r")
            # json_data = f.readline()
            # f.close()
        except Exception as e:
            print("Exception {}".format(e))
        return self.json(json_data)

    async def post(self, request, board_id):
        body = await request.text()
        try:
            event_data = json.loads(body) if body else None
            if event_data is not None:
                thermostat_configurator = ConfiguratorHelperSensor()
                thermostat_configurator.save_sensor_configuration(board_id, event_data)
                # f = open(f"{self.dir_path}/{board_id}.txt", "w")
                # f.write(event_data)
                # f.close()

        except ValueError:
            return self.json_message(
                "Event data should be valid JSON."
            )
        except Exception as e:
            print("Exception {}".format(e))
            raise Exception
        return self.json_message(f"{board_id} - {event_data}")


class WCAPIRelayConfigurationView(HomeAssistantView):
    """View to handle thermostat configuration requests."""

    url = URL_WC_RELAY_BOARD_CONFIGURATION
    name = "api:wc:realy:board:configuration"
    dir_path = os.path.dirname(os.path.realpath(__file__))

    @callback
    def get(self, request, board_id):
        json_data = []
        try:
            print("WCAPIRelayConfigurationView get")
            sensor_configurator = ConfiguratorHelperRelay()
            config = sensor_configurator.get_relay_configuration(board_id)
            if config is not None:
                json_data = json.loads(config)
            # f = open(f"{self.dir_path}/{board_id}.txt", "r")
            # json_data = f.readline()
            # f.close()
        except Exception as e:
            print("Exception {}".format(e))
        return self.json(json_data)

    async def post(self, request, board_id):
        print("WCAPIRelayConfigurationView post")
        body = await request.text()
        try:
            event_data = json.loads(body) if body else None
            print(event_data)
            if event_data is not None:
                thermostat_configurator = ConfiguratorHelperRelay()
                thermostat_configurator.save_relay_configuration(board_id, event_data)
                # f = open(f"{self.dir_path}/{board_id}.txt", "w")
                # f.write(event_data)
                # f.close()

        except ValueError:
            return self.json_message(
                "Event data should be valid JSON."
            )
        except Exception as e:
            print("Exception {}".format(e))
            raise Exception
        return self.json_message(f"{board_id} - {event_data}")