"""Constants for the EVN Data integration."""

from datetime import timedelta

DEFAULT_SCAN_INTERVAL = timedelta(hours=6)

DOMAIN = "nestup_evn"

CONF_DEVICE_NAME = "EVN Monitor"
CONF_DEVICE_MODEL = "Vietnam EVN Monitor"
CONF_DEVICE_MANUFACTURER = "Nestup Co."
CONF_DEVICE_SW_VERSION = "1.2.9"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CUSTOMER_ID = "customer_id"
CONF_MONTHLY_START = "monthly_start"
CONF_AREA = "area"
CONF_EVN_INFO = "evn_info"

CONF_SUCCESS = "success"
CONF_ERR_CANNOT_CONNECT = "cannot_connect"
CONF_ERR_INVALID_AUTH = "invalid_auth"
CONF_ERR_UNKNOWN = "unknown"
CONF_ERR_NOT_SUPPORTED = "not_supported"
CONF_ERR_NO_MONITOR = "no_monitor"
CONF_ERR_INVALID_ID = "error_ma_kh_deny"

ID_ECON_PER_DAY = "econ_per_day"
ID_ECON_PER_MONTH = "econ_per_month"
ID_ECOST_PER_DAY = "ecost_per_day"
ID_ECOST_PER_MONTH = "ecost_per_month"
ID_LATEST_UPDATE = "latest_update"
ID_FROM_DATE = "from_date"
ID_TO_DATE = "to_date"

VIETNAM_ECOST_VAT = 8  # in %
VIETNAM_ECOST_STAGES = {
    # kWh : VND
    0: 1678,
    50: 1734,
    100: 2014,
    200: 2536,
    300: 2834,
    400: 2927,
}
