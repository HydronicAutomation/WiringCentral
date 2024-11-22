# import hassapi as hass
import pprint

from appdaemon.plugins.hass import hassapi as hass

DOMAIN = "wiring_central"
#
# WiringCentral App
#
# Args:
#


class WiringCentral(hass.Hass):

    def initialize(self):
        self.log("Hello from WiringCentral")

        start_time = self.parse_time("11:24:00")
        stop_time = self.parse_time("11:25:00")
        on_temp = 23
        days = "fri,sat,sun"
        entity = "climate.wc_123456_1"
        mode = "cool"

        # print(self.list_services(namespace="global"))

        self.fire_event(f"{DOMAIN}_getdata_request")
        self.listen_event(self.wc_data_event_callback, f"{DOMAIN}_data")

        # self.run_daily(self.controlThermostat, start_time, constrain_days=days, entity=entity, on_temp=on_temp, on_mode=mode)
        # self.run_daily(self.controlThermostat, stop_time, constrain_days=days, entity=entity, on_temp=on_temp, on_mode="off")
        #
        self.listen_event(self.appReload, f"{DOMAIN}_appdaemon_reload")

    def wc_data_event_callback(self, event_name, data, kwargs):
        print("event_name", event_name)
        schedules = data.get('schedules', {})
        masterslaves = data.get('masterslaves', {})
        self.setupSchedules(schedules=schedules)
        self.setupMasterSlaves(masterslaves=masterslaves)

    def appReload(self, event_name, data, kwargs):
        self.log("=============== Reloading using appReload ")
        self.call_service("app/restart", app=f"{DOMAIN}", namespace="admin")

    def controlThermostat(self, kwargs):
        self.log("In startthermostat")
        print(kwargs)
        self.call_service(
            "climate/set_temperature", entity_id=kwargs['entity'], temperature=kwargs["on_temp"],
        )
        self.call_service(
            "climate/set_hvac_mode", entity_id=kwargs['entity'], hvac_mode=kwargs["on_mode"],
        )

    def setupMasterSlaves(self, masterslaves):
        print("setupMasterSlaves ", masterslaves)
        # pprint.pp(masterslaves)
        for board in masterslaves:
            masterslave_data = masterslaves[board]
            # pprint.pp(masterslave_data)
            self.setupMasterSlavesForBoard(board=board, data=masterslave_data)

    def setupMasterSlavesForBoard(self, board, data):
        # self.log(f"Setting up masterslaves for {board}")
        for rule in data:
            # pprint.pp(rule)
            if rule['master_object_id'] is not None:
                self.setupMasterSlaveForThermostat(rule['object_id'], rule['master_object_id'])

    def setupMasterSlaveForThermostat(self, object_id, master_object_id):
        master_entity_id = self.convert_name_to_entityID(domain="climate", object_id=master_object_id)
        slave_entity_id = self.convert_name_to_entityID(domain="climate", object_id=object_id)
        self.log(f"setupMasterSlaveForThermostat Slave: {slave_entity_id}, Master: {master_entity_id}")
        self.get_entity(master_entity_id).listen_state(self.followMaster, slave_entity_id=slave_entity_id)
        self.get_entity(master_entity_id).listen_state(self.followMaster, attribute='temperature', slave_entity_id=slave_entity_id)
        self.log(f"setupMasterSlaveForThermostat Slave: {slave_entity_id}, Master: {master_entity_id} Done...")

    def followMaster(self, entity, attribute, old, new, kwargs):
        # print("=============================")
        # print(entity, attribute, old, new, kwargs)
        temperature = self.get_state(entity, attribute="temperature")
        mode = self.get_state(entity)
        # print("Temp: ", temperature)
        # self.get_entity(kwargs['slave_entity_id']).set_state(state=new)
        self.call_service(
            "climate/set_temperature", entity_id=kwargs['slave_entity_id'], temperature=temperature,
        )
        self.call_service(
            "climate/set_hvac_mode", entity_id=kwargs['slave_entity_id'], hvac_mode=mode,
        )

    def setupSchedules(self, schedules):
        print("setupSchedules ", schedules)
        for entity in schedules:
            entity_data = schedules[entity]
            # print("entity_data", entity_data)
            self.setupScheduleForEntity(entity, entity_data)

    def setupScheduleForEntity(self, entity, entity_data):
        self.log(f"setupScheduleForEntity {entity}")
        default_schedules = entity_data.get('default', [])
        custom_schedules = entity_data.get('custom', [])
        default_enabled = entity_data.get('status', False)

        if default_enabled:
            for schedule in default_schedules:
                start_time = self.format_time(schedule['starttime_default'])
                stop_time = self.format_time(schedule['endtime_default'])
                on_temp = float(schedule['target_temperature_default'])
                days = 'mon,tue,wed,thu,fri' if schedule['day_of_week_default'] == 'Mon - Fri' else 'sat,sun'
                mode = schedule['hvac_mode_default'].lower()

                self.run_daily(self.controlThermostat, start_time, constrain_days=days, entity=entity, on_temp=on_temp, on_mode=mode)
                self.run_daily(self.controlThermostat, stop_time, constrain_days=days, entity=entity, on_temp=on_temp, on_mode="off")

        for schedule in custom_schedules:
            start_time = self.format_time(schedule['starttime_custom'])
            stop_time = self.format_time(schedule['endtime_custom'])
            on_temp = float(schedule['target_temperature_custom'])
            days = schedule['day_of_week_custom'].lower()
            mode = schedule['hvac_mode_custom'].lower()

            self.run_daily(self.controlThermostat, start_time, constrain_days=days, entity=entity, on_temp=on_temp,
                           on_mode=mode)
            self.run_daily(self.controlThermostat, stop_time, constrain_days=days, entity=entity, on_temp=on_temp,
                           on_mode="off")
        self.log(f"setupScheduleForEntity {entity} done...")

    def convert_name_to_entityID(self, domain, object_id):
        return "{}.{}".format(domain, object_id.replace('-', '_').lower())

    def format_time(self, time_data):
        hour, minute = time_data.split(":")
        return self.parse_time("{}:{}:00".format(hour, minute))