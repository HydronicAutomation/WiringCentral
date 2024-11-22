import requests
import json
from wiringcentralconfigurator_app.models import LongLivedAccessToken
import os

# TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJmNTA2NWJhY2EwMmY0ZmRhYjMxNzBhYzgxOTZiM2YwMyIsImlhdCI6MTU5MDMwODE3MiwiZXhwIjoxOTA1NjY4MTcyfQ.3Aynyz4viy-fb04ZLTYECGOxYzyU-tQ8zvkbKrXEX1o"
token_object = LongLivedAccessToken.objects.last()
TOKEN = ''
if token_object is not None:
    TOKEN = token_object.token

# Uncomment for non addon testing
BASE_URL = "http://localhost:8123"

# change the BASE_URL to below when running in docker addon
# https://developers.home-assistant.io/docs/add-ons/communication#home-assistant-core
if os.getenv("SUPERVISOR_TOKEN") is not None:
    BASE_URL = "http://supervisor/core"

URL_WC_CLIMATE_API = "/api/wc/climate/status"
URL_WC_CLIMATE_ENTITIES = "/api/wc/climate/entities"

URL_WC_SENSOR_API = "/api/wc/sensor/status"
URL_WC_SENSOR_ENTITIES = "/api/wc/sensor/entities"
URL_WC_SENSOR_BOARDS = "/api/wc/sensor/boards"
URL_WC_SENSOR_ENTITY_DETAILS = "/api/wc/sensor/entity/details"
URL_WC_SENSOR_BOARD_DETAILS = "/api/wc/sensor/board/{board_id}"

URL_WC_RELAY_API = "/api/wc/relay/status"
URL_WC_RELAY_ENTITIES = "/api/wc/relay/entities"
URL_WC_RELAY_ENTITY_DETAILS = "/api/wc/relay/entity/details"

URL_WC_CLIMATE_BOARD_MASTERSLAVE_CONFIGURATION = "/api/wc/climate/board_masterslave/configuration/{board_id}"
URL_WC_CLIMATE_BOARD_DEFAULT_RULE_CONFIGURATION = "/api/wc/climate/default_rule/configuration/{board_id}"
URL_WC_CLIMATE_BOARD_CONFIGURATION = "/api/wc/climate/board/configuration/{board_id}"
URL_WC_SENSOR_BOARD_CONFIGURATION = "/api/wc/sensor/board/configuration/{board_id}"
URL_WC_RELAY_BOARD_CONFIGURATION = "/api/wc/relay/board/configuration/{board_id}"


def get_token(token):
    if os.getenv("SUPERVISOR_TOKEN") is not None:
        token = os.getenv("SUPERVISOR_TOKEN")
    return token

def get_climate_api_status(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_API)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_climate_entities(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_ENTITIES)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_sensor_api_status(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL,URL_WC_SENSOR_API)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_sensor_entities(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL,URL_WC_SENSOR_ENTITIES)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_relay_api_status(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL,URL_WC_RELAY_API)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_relay_entities(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL,URL_WC_RELAY_ENTITIES)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_relay_entity_details(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL,URL_WC_RELAY_ENTITY_DETAILS)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text



def get_boards(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_SENSOR_BOARDS)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_sensor_entity_details(token):
    token = get_token(token)
    url = "{}{}".format(BASE_URL,URL_WC_SENSOR_ENTITY_DETAILS)
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_board_details(token, board_id):
    token = get_token(token)
    url = "{}{}".format(BASE_URL,URL_WC_SENSOR_BOARD_DETAILS.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def post_board_configuration(token, board_id, data):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_BOARD_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }
    response = requests.post(url, json=json.dumps(data), headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def post_board_masterslave_configuration(token, board_id, data):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_BOARD_MASTERSLAVE_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def post_board_default_rule_configuration(token, board_id, data):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_BOARD_DEFAULT_RULE_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_board_configuration(token, board_id):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_BOARD_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_board_masterslave_configuration(token, board_id):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_BOARD_MASTERSLAVE_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_board_defaultrule_configuration(token, board_id):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_CLIMATE_BOARD_DEFAULT_RULE_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def post_board_sensor_configuration(token, board_id, data):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_SENSOR_BOARD_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }
    response = requests.post(url, json=json.dumps(data), headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_board_sensor_configuration(token, board_id):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_SENSOR_BOARD_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def post_board_relay_configuration(token, board_id, data):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_RELAY_BOARD_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }
    response = requests.post(url, json=json.dumps(data), headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text


def get_board_relay_configuration(token, board_id):
    token = get_token(token)
    url = "{}{}".format(BASE_URL, URL_WC_RELAY_BOARD_CONFIGURATION.format(board_id=board_id))
    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True, json.loads(response.text)
    elif response.status_code == 401:
        return False, response.text
    else:
        return False, response.text

if __name__ == "__main__":
    print(get_climate_api_status(TOKEN))
    print(get_climate_entities(TOKEN))
    print(get_sensor_api_status(TOKEN))
    print(get_sensor_entities(TOKEN))
    print(get_sensor_entity_details(TOKEN))
    print(get_boards(TOKEN))
    print(get_board_details(TOKEN, "thermostat"))