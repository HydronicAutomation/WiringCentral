import asyncio
import os
import logging

from homeassistant.util.yaml import load_yaml, dump
_LOGGER = logging.getLogger(__name__)


class ConfiguratorHelperBoard:
    def __init__(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.boards_filename = os.path.join(dir_path, 'configuration_boards.yaml')

    def read_boards_configuration_from_file(self):
        data = {}
        if not os.path.isfile(self.boards_filename):
            return data
        data = load_yaml(self.boards_filename)
        return data

    def save_boards_configuration_to_file(self, data):
        data = dump(data)
        with open(self.boards_filename, 'w', encoding="utf-8") as file:
            file.write(data)

    def get_thermostat_board_configuration(self, board):
        configurations = self.read_boards_configuration_from_file()
        if configurations is None:
            return None
        else:
            return configurations.get(board)

    def save_thermostat_board_configuration(self, board, board_config):
        configurations = self.read_boards_configuration_from_file()
        if configurations is None:
            configurations = {}
        configurations[board] = board_config
        self.save_boards_configuration_to_file(configurations)


    def async_save_thermostat_board_configuration(self, board, board_config):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.save_thermostat_board_configuration, board, board_config)


class ConfiguratorHelperThermostat:
    def __init__(self) -> None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.configuration_file = os.path.join(dir_path, "configuration_thermostats.yaml")

    def get_thermostat_configuration(self, board):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            return None
        else:
            return configurations.get(board)
        
    def async_get_thermostat_configuration(self, board):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.get_thermostat_configuration, board)

    def save_thermostat_configuration(self, board, thermostat_config):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            configurations = {}
        configurations[board] = thermostat_config
        self._write_configurations_to_file(configurations)

    def async_save_thermostat_configuration(self, board, thermostat_config):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.save_thermostat_configuration, board, thermostat_config)

    def _read_configurations_from_file(self):
        """Read YAML helper."""
        if not os.path.isfile(self.configuration_file):
            return None
        return load_yaml(self.configuration_file)

    def _write_configurations_to_file(self, configurations):
        """Write YAML helper."""
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(configurations)
        print(data)
        with open(self.configuration_file, "w", encoding="utf-8") as outfile:
            outfile.write(data)


class ConfiguratorHelperDefaultRule:
    def __init__(self) -> None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.configuration_file = os.path.join(dir_path, "configuration_default_rules.yaml")

    def get_defaultrule_configuration(self, board):
        configurations = self._read_configurations_from_file()
        print("default_rules ", configurations.get('default_rules'))
        if configurations is None:
            return None
        else:
            return configurations.get('default_rules')

    def get_exclusion_list_configuration(self, board):
        configurations = self._read_configurations_from_file()
        print("exclude ", configurations.get('exclude'))
        if configurations is None:
            return None
        else:
            return configurations.get('exclude')

    def save_defaultrule_configuration(self, board, defaultrule_config):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            configurations = {}
        configurations['default_rules'] = defaultrule_config
        self._write_configurations_to_file(configurations)

    def save_exclusion_list_configuration(self, board, exclusion_list):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            configurations = {}
        configurations['exclude'] = exclusion_list
        self._write_configurations_to_file(configurations)

    def _read_configurations_from_file(self):
        """Read YAML helper."""
        if not os.path.isfile(self.configuration_file):
            return None
        return load_yaml(self.configuration_file)

    def _write_configurations_to_file(self, configurations):
        """Write YAML helper."""
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(configurations)
        print(data)
        with open(self.configuration_file, "w", encoding="utf-8") as outfile:
            outfile.write(data)


class ConfiguratorHelperMasterSlave:
    def __init__(self) -> None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.configuration_file = os.path.join(dir_path, "configuration_masterslave.yaml")

    def get_thermostat_configuration(self, board):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            return None
        else:
            return configurations.get(board)

    def save_thermostat_configuration(self, board, masterslave_config):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            configurations = {}
        configurations[board] = masterslave_config
        self._write_configurations_to_file(configurations)

    def _read_configurations_from_file(self):
        """Read YAML helper."""
        if not os.path.isfile(self.configuration_file):
            return None
        return load_yaml(self.configuration_file)

    def _write_configurations_to_file(self, configurations):
        """Write YAML helper."""
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(configurations)
        print(data)
        with open(self.configuration_file, "w", encoding="utf-8") as outfile:
            outfile.write(data)


class ConfiguratorHelperSensor:
    def __init__(self) -> None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.configuration_file = os.path.join(dir_path, "configuration_sensors.yaml")

    def get_sensor_configuration(self, board):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            return None
        else:
            return configurations.get(board)
        
    def async_get_sensor_configuration(self, board):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.get_sensor_configuration, board)

    def async_save_sensor_configuration(self, board, sensor_config):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.save_sensor_configuration, board, sensor_config)

    def save_sensor_configuration(self, board, sensor_config):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            configurations = {}
        configurations[board] = sensor_config
        self._write_configurations_to_file(configurations)

    def _read_configurations_from_file(self):
        """Read YAML helper."""
        if not os.path.isfile(self.configuration_file):
            return None
        return load_yaml(self.configuration_file)

    def _write_configurations_to_file(self, configurations):
        """Write YAML helper."""
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(configurations)
        print(data)
        with open(self.configuration_file, "w", encoding="utf-8") as outfile:
            outfile.write(data)


class ConfiguratorHelperRelay:
    def __init__(self) -> None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.configuration_file = os.path.join(dir_path, "configuration_relays.yaml")

    def get_relay_configuration(self, board):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            return None
        else:
            return configurations.get(board)
        
    def async_get_relay_configuration(self, board):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.get_relay_configuration, board)

    def async_save_sensor_configuration(self, board, relay_config):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.save_relay_configuration, board, relay_config)

    def save_relay_configuration(self, board, relay_config):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            configurations = {}
        configurations[board] = relay_config
        self._write_configurations_to_file(configurations)

    def _read_configurations_from_file(self):
        """Read YAML helper."""
        if not os.path.isfile(self.configuration_file):
            return None
        return load_yaml(self.configuration_file)

    def _write_configurations_to_file(self, configurations):
        """Write YAML helper."""
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(configurations)
        print(data)
        with open(self.configuration_file, "w", encoding="utf-8") as outfile:
            outfile.write(data)
