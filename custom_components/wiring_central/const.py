from datetime import timedelta
DOMAIN = 'wiring_central'

ATTR_MIN_TEMP = "min_temp"
ATTR_MAX_TEMP = "max_temp"
ATTR_MOVING_AVERAGE_LENGTH = "moving_avg_length"
ATTR_ROUND_VALUE = "round_value"
ATTR_WINDOW_METHOD = "window_method"
ATTR_HOT_TOLERANCE = "hot_tolerance"
ATTR_COLD_TOLERANCE = "cold_tolerance"


# Placeholder values for the integration flow
MIN_TEMP = 0
MAX_TEMP = 50
MOVING_AVERAGE_LENGTH = 0
ROUND_VALUE = 0.5
WINDOW_METHOD_ENABLE = False
HOT_TOLERANCE = 0.5
COLD_TOLERANCE = 0.5

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)