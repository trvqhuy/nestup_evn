"""Constants for the EVN Data integration."""

from datetime import timedelta

DEFAULT_SCAN_INTERVAL = timedelta(hours=6)

DOMAIN = "nestup_evn"

CONF_DEVICE_NAME = "EVN Monitor"
CONF_DEVICE_MODEL = "Vietnam EVN Monitor"
CONF_DEVICE_MANUFACTURER = "Nestup Co."
CONF_DEVICE_SW_VERSION = "2.1.0"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CUSTOMER_ID = "customer_id"
CONF_MONTHLY_START = "monthly_start"
CONF_AREA = "area"
CONF_EVN_INFO = "evn_info"

CONF_SUCCESS = "success"
CONF_EMPTY = "empty"
CONF_ERR_CANNOT_CONNECT = "cannot_connect"
CONF_ERR_INVALID_AUTH = "invalid_auth"
CONF_ERR_UNKNOWN = "unknown"
CONF_ERR_NOT_SUPPORTED = "not_supported"
CONF_ERR_NO_MONITOR = "no_monitor"
CONF_ERR_INVALID_ID = "error_ma_kh_deny"

ID_ECON_TOTAL_NEW = "econ_total_new"
ID_ECON_TOTAL_OLD = "econ_total_old"
ID_ECON_DAILY_NEW = "econ_daily_new"
ID_ECON_DAILY_OLD = "econ_daily_old"
ID_ECON_MONTHLY_NEW = "econ_monthly_new"
ID_ECOST_DAILY_NEW = "ecost_daily_new"
ID_ECOST_DAILY_OLD = "ecost_daily_old"
ID_ECOST_MONTHLY_NEW = "ecost_monthly_new"
ID_PAYMENT_NEEDED = "payment_needed"
ID_M_PAYMENT_NEEDED = "m_payment_needed"
ID_FROM_DATE = "from_date"
ID_TO_DATE = "to_date"
ID_LATEST_UPDATE = "latest_update"

STATUS_N_PAYMENT_NEEDED = "Đã thanh toán"
STATUS_PAYMENT_NEEDED = "Chưa thanh toán"

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
