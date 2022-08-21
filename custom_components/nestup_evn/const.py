"""Constants for the EVN Data integration."""

DOMAIN = "nestup_evn"

CONF_DEVICE_NAME = "EVN Monitor"
CONF_DEVICE_MODEL = "Vietnam EVN Monitor"
CONF_DEVICE_MANUFACTURER = "Nestup Co."
CONF_DEVICE_SW_VERSION = "1.1.8"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CUSTOMER_ID = "customer_id"
CONF_MONTHLY_START = "monthly_start"
CONF_AREA = "area"

CONF_SUCCESS = "success"
CONF_ERR_CANNOT_CONNECT = "cannot_connect"
CONF_ERR_INVALID_AUTH = "invalid_auth"
CONF_ERR_UNKNOWN = "unknown"

ID_ECON_PER_DAY = "econ_per_day"
ID_ECON_PER_MONTH = "econ_per_month"
ID_ECOST_PER_DAY = "ecost_per_day"
ID_ECOST_PER_MONTH = "ecost_per_month"
ID_LATEST_UPDATE = "latest_update"
ID_FROM_DATE = "from_date"
ID_TO_DATE = "to_date"

VIETNAM_ECOST_PARAMS = [1678, 1734, 2014, 2536, 2834, 2927]  # in VND
VIETNAM_ECOST_STAGES = [0, 138, 276, 551, 2000, 2000]  # in kWh
VIETNAM_ECOST_VAT = 8  # in %

from datetime import timedelta
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)
