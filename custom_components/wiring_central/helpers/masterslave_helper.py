import logging
import os
import pprint
from copy import deepcopy

from homeassistant.util.yaml import dump, load_yaml

_LOGGER = logging.getLogger(__name__)


class MasterSlaveService:
    def __init__(self) -> None:
        super().__init__()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.masterslave_filename = os.path.join(dir_path, 'masterslave.yaml')
        self.masterslave_data = self.read_masterslave_from_file()
        pprint.pp(self.masterslave_data)
        # self.topics = {}

    def read_masterslave_from_file(self):
        data = {"exclude": [], "default_rules": []}
        if not os.path.isfile(self.masterslave_filename):
            return data
        data = load_yaml(self.masterslave_filename)
        return data

    def get_masterslave_settings_for_board(self, board):
        return self.masterslave_data.get(board)

    def save_masterslave_settings_for_board(self, board, data):
        self.masterslave_data[board] = data
        self.save_mastersalve_file()

    def save_mastersalve_file(self):
        _LOGGER.info(f"save_default_rules_to_file")
        pprint.pp(self.masterslave_data)
        # Do it before opening file. If dump causes error it will now not
        # truncate the file.
        data = dump(self.masterslave_data)
        # print(data)
        with open(self.masterslave_filename, "w", encoding="utf-8") as outfile:
            outfile.write(data)
        _LOGGER.info(f"saved save_mastersalve_file")
