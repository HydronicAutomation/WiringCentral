import logging
import os
import pprint
from copy import deepcopy

from homeassistant.util.yaml import dump, load_yaml

_LOGGER = logging.getLogger(__name__)


class ScheduleService:
    def __init__(self) -> None:
        super().__init__()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.schedule_filename = os.path.join(dir_path, 'schedules.yaml')
        self.schedule_defaults_filename = os.path.join(dir_path, 'schedule_defaults.yaml')
        self.data_schedule_defaults = self.read_schedule_defaults_from_file()
        pprint.pp(self.data_schedule_defaults)
        self.data = self.read_schedules_from_file()
        # self.topics = {}

    def add_service_data(self, entity_id, data):
        _LOGGER.info(f"add_service_data for {entity_id}")
        print("add_service_data data: ")
        pprint.pprint(data)
        self.data[entity_id] = data
        if entity_id not in self.data_schedule_defaults.get('exclude', []):
            self.data_schedule_defaults['exclude'].append(entity_id)
        self.save_schedules_to_file()
        self.save_default_rules_to_file()   # Needed for update the exclude list

    def clear_service_data(self, entity_id):
        _LOGGER.info(f"clear_service_data {entity_id}")
        if entity_id in self.data_schedule_defaults.get('exclude', []):
            self.data_schedule_defaults.get('exclude').remove(entity_id)
        if self.data.get(entity_id) is not None:
            self.data.pop(entity_id)
        self.save_schedules_to_file()
        self.save_default_rules_to_file()    # Needed for update the exclude list

    # def add_service_topic(self, entity_id, service_command_topic):
    #     _LOGGER.info(f"add_service_topic for {entity_id}")
    #     print("add_service_topic service_command_topic:", service_command_topic)
    #     self.topics[entity_id] = service_command_topic

    def get_service_data(self, entity_id):
        _LOGGER.debug(f"get_service_data for {entity_id}")
        data = {"default": [], "custom": [], "status": False}
        data = deepcopy(self.data.get(entity_id, data))
        if entity_id not in self.data_schedule_defaults.get('exclude', []):
            data['default'] = self.data_schedule_defaults.get('default_rules', [])
            data['status'] = False
        return data

    def get_defaultrule_configuration(self):
        return self.data_schedule_defaults.get("default_rules", [])

    def save_schedules_to_file(self):
        _LOGGER.info(f"save_schedules_to_file")
        pprint.pp(self.data)
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(self.data)
        # print(data)
        with open(self.schedule_filename, "w", encoding="utf-8") as outfile:
            outfile.write(data)
        _LOGGER.info(f"saved _schedules_to_file")

    def save_default_rules_to_file(self):
        _LOGGER.info(f"save_default_rules_to_file")
        pprint.pp(self.data_schedule_defaults)
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(self.data_schedule_defaults)
        # print(data)
        with open(self.schedule_defaults_filename, "w", encoding="utf-8") as outfile:
            outfile.write(data)
        _LOGGER.info(f"saved save_default_rules_to_file")

    def read_schedules_from_file(self):
        if not os.path.isfile(self.schedule_filename):
            return {}
        return load_yaml(self.schedule_filename)

    def read_schedule_defaults_from_file(self):
        data = {"exclude": [], "default_rules": []}
        if not os.path.isfile(self.schedule_defaults_filename):
            return data
        data = load_yaml(self.schedule_defaults_filename)
        data = {"exclude": data.get("exclude", []) or [], "default_rules": data.get("default_rules", []) or []}
        return data
    # def push_service_data(self, hass, entity_id, schedule_data):
    #     _LOGGER.info(f"get_service_data for {entity_id}")
    #     print("push_service_data schedule_data:", schedule_data)

    def save_defaultrule_configuration(self, event_data):
        if event_data is None:
            return
        self.data_schedule_defaults["default_rules"] = event_data
        self.save_default_rules_to_file()
