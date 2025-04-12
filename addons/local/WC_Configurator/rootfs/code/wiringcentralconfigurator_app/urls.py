from django.conf.urls import url
from .views import SaveLongLivedAccessTokenView, ListBoardView, ConfigurationThermostatView, configuration_ajax_view, \
    ConfigurationSensorView, ConfigurationRelayView, configuration_relay_ajax_view, ConfigurationMasterSlaveView, \
    ConfigurationOptionsView, ConfigurationDefaultRulesView, ListBoardMinimalView, \
    ConfigurationBoardStateManagerView

urlpatterns = [
    url(r'^save_access_token/$', SaveLongLivedAccessTokenView.as_view(), name='save_access_token_view'),
    url(r'^list_board_view/$', ListBoardView.as_view(), name='list_board_view'),
    url(r'^list_board__mininal_view/$', ListBoardMinimalView.as_view(), name='list_board_minimal_view'),

    url(r'^configuration_thermostat_view/(?P<board>[-\w]+)/$', ConfigurationThermostatView.as_view(),
        name='configuration_thermostat_view'),
    url(r'^configuration_ajax_view/$', configuration_ajax_view, name='configuration_ajax_view'),

    url(r'^configuration_relay_ajax_view/$', configuration_relay_ajax_view, name='configuration_relay_ajax_view'),

    url(r'^configuration_sensor_view/(?P<board>[-\w]+)/$', ConfigurationSensorView.as_view(),
        name='configuration_sensor_view'),

    url(r'^configuration_masterslave_view/(?P<board>[-\w]+)/$', ConfigurationMasterSlaveView.as_view(),
        name='configuration_masterslave_view'),

    url(r'^configuration_board_state_manager_view/(?P<board>[-\w]+)/$',
        ConfigurationBoardStateManagerView.as_view(),
        name='configuration_board_state_manager_view'),

    url(r'^configuration_default_rules_view/(?P<board>[-\w]+)/$', ConfigurationDefaultRulesView.as_view(),
        name='configuration_default_rules_view'),

    url(r'^configuration_options_view/(?P<board>[-\w]+)/$', ConfigurationOptionsView.as_view(),
        name='configuration_options_view'),

    url(r'^configuration_relay_view/(?P<board>[-\w]+)/$', ConfigurationRelayView.as_view(),
        name='configuration_relay_view'),
]
