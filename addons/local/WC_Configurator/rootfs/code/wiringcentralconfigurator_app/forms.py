from django import forms
from django.forms import formset_factory, BaseFormSet
from tempus_dominus.widgets import TimePicker


class TokenAddEditForm(forms.Form):
    token = forms.CharField(required=True, max_length=512)


class ConfigurationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            if key.startswith('name'):
                self.fields[key].widget.attrs.update({'class': 'form-control', 'readonly': True})
            elif key.startswith('type'):
                self.fields[key].widget.attrs.update({'class': 'custom-select d-block w-100'})
            elif key.startswith('feed') or key.startswith('multiplier') or key.startswith('summer'):
                self.fields[key].widget.attrs.update({'class': 'form-control'})

    choice = [("", ""), ("NTC", "NTC"), ("DS18B20", "DS18B20"), ("SHTC3-TEMP", "SHTC3-TEMP"), ("MQTT", "MQTT")]

    name_1 = forms.CharField(required=True)
    type_1 = forms.ChoiceField(choices=choice, required=True)
    feed_1 = forms.CharField(required=True)
    multiplier_1 = forms.FloatField(required=True)
    summer_1 = forms.FloatField(required=True)

    name_2 = forms.CharField(required=True)
    type_2 = forms.ChoiceField(choices=choice, required=True)
    feed_2 = forms.CharField(required=True)
    multiplier_2 = forms.FloatField(required=True)
    summer_2 = forms.FloatField(required=True)

    name_3 = forms.CharField(required=True)
    type_3 = forms.ChoiceField(choices=choice, required=True)
    feed_3 = forms.CharField(required=True)
    multiplier_3 = forms.FloatField(required=True)
    summer_3 = forms.FloatField(required=True)

    name_4 = forms.CharField(required=True)
    type_4 = forms.ChoiceField(choices=choice, required=True)
    feed_4 = forms.CharField(required=True)
    multiplier_4 = forms.FloatField(required=True)
    summer_4 = forms.FloatField(required=True)

    name_5 = forms.CharField(required=True)
    type_5 = forms.ChoiceField(choices=choice, required=True)
    feed_5 = forms.CharField(required=True)
    multiplier_5 = forms.FloatField(required=True)
    summer_5 = forms.FloatField(required=True)

    name_6 = forms.CharField(required=True)
    type_6 = forms.ChoiceField(choices=choice, required=True)
    feed_6 = forms.CharField(required=True)
    multiplier_6 = forms.FloatField(required=True)
    summer_6 = forms.FloatField(required=True)

    name_7 = forms.CharField(required=True)
    type_7 = forms.ChoiceField(choices=choice, required=True)
    feed_7 = forms.CharField(required=True)
    multiplier_7 = forms.FloatField(required=True)
    summer_7 = forms.FloatField(required=True)

    name_8 = forms.CharField(required=True)
    type_8 = forms.ChoiceField(choices=choice, required=True)
    feed_8 = forms.CharField(required=True)
    multiplier_8 = forms.FloatField(required=True)
    summer_8 = forms.FloatField(required=True)


class ConfigurationMasterSlaveForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # print(args, kwargs)
        self.choices = kwargs.pop('board_choices', [("", "")])
        # print(self.choices)
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            # print(key, type(key))
            if key == 'name':
                self.fields[key].widget.attrs.update({'class': 'form-control', 'readonly': True})
            if key == 'type':
                self.fields[key].widget.attrs.update({'class': 'custom-select d-block w-100'})
                self.fields[key].choices = self.choices

    # choice = [("", ""), ("THERMOSTAT-1", "1"), ("THERMOSTAT-2", "2"), ("THERMOSTAT-3", "3"), ("THERMOSTAT-4", "4"),
    #           ("THERMOSTAT-5", "5"), ("THERMOSTAT-6", "6"), ("THERMOSTAT-7", "7"), ("THERMOSTAT-8", "8")]
    choice = [("", "")]

    name = forms.CharField(required=True)
    type = forms.ChoiceField(choices=choice, required=True)


class BaseMasterSlaveFormSet(BaseFormSet):

    def clean(self):
        super().clean()


ConfigurationMasterSlaveFormSet = formset_factory(ConfigurationMasterSlaveForm, formset=BaseMasterSlaveFormSet,
                                                  can_delete=True, extra=0)


class ConfigurationMasterSlaveFormOld(forms.Form):
    def __init__(self, *args, **kwargs):
        # print(args, kwargs)
        self.choices = kwargs.pop('board_choices', [("", "")])
        # print(self.choices)
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            # print(key, type(key))
            if key[0:4] == 'name':
                self.fields[key].widget.attrs.update({'class': 'form-control', 'readonly': True})
            if key[0:4] == 'type':
                self.fields[key].widget.attrs.update({'class': 'custom-select d-block w-100'})
                self.fields[key].choices = self.choices

    # choice = [("", ""), ("THERMOSTAT-1", "1"), ("THERMOSTAT-2", "2"), ("THERMOSTAT-3", "3"), ("THERMOSTAT-4", "4"),
    #           ("THERMOSTAT-5", "5"), ("THERMOSTAT-6", "6"), ("THERMOSTAT-7", "7"), ("THERMOSTAT-8", "8")]
    choice = [("", "")]

    name_1 = forms.CharField(required=True)
    type_1 = forms.ChoiceField(choices=choice, required=True)

    name_2 = forms.CharField(required=True)
    type_2 = forms.ChoiceField(choices=choice, required=True)

    name_3 = forms.CharField(required=True)
    type_3 = forms.ChoiceField(choices=choice, required=True)

    name_4 = forms.CharField(required=True)
    type_4 = forms.ChoiceField(choices=choice, required=True)

    name_5 = forms.CharField(required=True)
    type_5 = forms.ChoiceField(choices=choice, required=True)

    name_6 = forms.CharField(required=True)
    type_6 = forms.ChoiceField(choices=choice, required=True)

    name_7 = forms.CharField(required=True)
    type_7 = forms.ChoiceField(choices=choice, required=True)

    name_8 = forms.CharField(required=True)
    type_8 = forms.ChoiceField(choices=choice, required=True)


class MyTimePicker(TimePicker):

    def get_js_format(self):
        js_format = "H:m"
        return js_format


class ConfigurationDefaultRuleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['starttime', 'endtime']:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                pass
                field.widget.attrs.update({'append': 'fa fa-clock-o', 'icon_toggle': True, 'autocomplete': 'off'})

    choice = [("", "")]
    day_of_week_choices = [("Mon - Fri", "Mon - Fri"), ("Sat - Sun", "Sat - Sun")]
    hvac_mode_choices = [("Heat", "Heat"), ("Cool", "Cool"), ("Off", "Off")]

    starttime = forms.TimeField(required=True, widget=MyTimePicker())
    endtime = forms.TimeField(required=True, widget=MyTimePicker())
    target_temperature = forms.FloatField(required=True)
    day_of_week = forms.ChoiceField(choices=day_of_week_choices, required=True)
    hvac_mode = forms.ChoiceField(choices=hvac_mode_choices, required=True)


class BaseConfigurationDefaultRuleSet(BaseFormSet):

    def clean(self):
        super().clean()


ConfigurationDefaultRuleFormSet = formset_factory(ConfigurationDefaultRuleForm, formset=BaseConfigurationDefaultRuleSet,
                                                  can_delete=True)


class RelayConfigurationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in self.fields.keys():
            if key[0:4] == 'name':
                self.fields[key].widget.attrs.update({'class': 'form-control', 'readonly': True})
            if key[0:4] == 'type':
                self.fields[key].widget.attrs.update({'class': 'custom-select d-block w-100'})
            if key[0:4] == 'feed':
                self.fields[key].widget.attrs.update({'class': 'form-control'})
            if key[0:6] == 'enable':
                self.fields[key].widget.attrs.update({'class': 'form-check-input'})

    choice = [("", ""), ("BUILTIN", "BUILTIN"), ("RL-BOARD", "RL-BOARD")]

    name_1 = forms.CharField(required=True)
    type_1 = forms.ChoiceField(choices=choice, required=True)
    feed_1 = forms.CharField(required=True)
    enable_1 = forms.BooleanField(initial=True, required=False)

    name_2 = forms.CharField(required=True)
    type_2 = forms.ChoiceField(choices=choice, required=True)
    feed_2 = forms.CharField(required=True)
    enable_2 = forms.BooleanField(initial=True, required=False)

    name_3 = forms.CharField(required=True)
    type_3 = forms.ChoiceField(choices=choice, required=True)
    feed_3 = forms.CharField(required=True)
    enable_3 = forms.BooleanField(initial=True, required=False)

    name_4 = forms.CharField(required=True)
    type_4 = forms.ChoiceField(choices=choice, required=True)
    feed_4 = forms.CharField(required=True)
    enable_4 = forms.BooleanField(initial=True, required=False)

    name_5 = forms.CharField(required=True)
    type_5 = forms.ChoiceField(choices=choice, required=True)
    feed_5 = forms.CharField(required=True)
    enable_5 = forms.BooleanField(initial=True, required=False)

    name_6 = forms.CharField(required=True)
    type_6 = forms.ChoiceField(choices=choice, required=True)
    feed_6 = forms.CharField(required=True)
    enable_6 = forms.BooleanField(initial=True, required=False)

    name_7 = forms.CharField(required=True)
    type_7 = forms.ChoiceField(choices=choice, required=True)
    feed_7 = forms.CharField(required=True)
    enable_7 = forms.BooleanField(initial=True, required=False)

    name_8 = forms.CharField(required=True)
    type_8 = forms.ChoiceField(choices=choice, required=True)
    feed_8 = forms.CharField(required=True)
    enable_8 = forms.BooleanField(initial=True, required=False)


class SensorConfigurationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    ntc_1 = forms.BooleanField(initial=True, required=False)
    ntc_2 = forms.BooleanField(initial=True, required=False)
    ntc_3 = forms.BooleanField(initial=True, required=False)
    ntc_4 = forms.BooleanField(initial=True, required=False)
    ntc_5 = forms.BooleanField(initial=True, required=False)
    ntc_6 = forms.BooleanField(initial=True, required=False)
    ntc_7 = forms.BooleanField(initial=True, required=False)
    ntc_8 = forms.BooleanField(initial=True, required=False)


"""
  enable_cooler_heater_control: 1
  enable_transformer_control: 1

"""

class ConfigurationBoardStateManagerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    enable_cooler_heater_control = forms.BooleanField(initial=False, required=False)
    enable_transformer_control = forms.BooleanField(initial=False, required=False)



