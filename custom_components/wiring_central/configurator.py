import os
import json

from homeassistant.util.yaml import load_yaml, dump


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

    def save_thermostat_configuration(self, board, thermostat_config):
        configurations = self._read_configurations_from_file()
        if configurations is None:
            configurations = {}
        configurations[board] = thermostat_config
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
