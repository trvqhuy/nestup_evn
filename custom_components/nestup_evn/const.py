"""Constants for the EVN Data integration."""
from dataclasses import dataclass
from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_TIMESTAMP,
    ENERGY_KILO_WATT_HOUR,
)

POLLING_INTERVAL_IN_MINS = 5

DOMAIN = "nestup_evn"
CONF_COMPONENT_NAME = "EVN Data"

CONF_DEVICE_NAME = "EVN Bot"
CONF_DEVICE_MODEL = "Vietnam EVN Monitor"
CONF_DEVICE_MANUFACTURER = "Nestup Co."
CONF_DEVICE_SW_VERSION = "1.0.0"

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


@dataclass
class Entity:
    """Describe the supported areas."""

    id: str
    friendly_name: str
    entity_class: str
    unit: str
    icon: str


DEVICE_ENTITIES = [
    Entity(
        ID_ECON_PER_DAY,
        "Daily E-consump.",
        DEVICE_CLASS_ENERGY,
        ENERGY_KILO_WATT_HOUR,
        "mdi:flash-outline",
    ),
    Entity(
        ID_ECON_PER_MONTH,
        "Monthly E-consump.",
        DEVICE_CLASS_ENERGY,
        ENERGY_KILO_WATT_HOUR,
        "mdi:flash-outline",
    ),
    Entity(ID_ECOST_PER_DAY, "Daily E-cost", None, "VNĐ", "mdi:cash-multiple"),
    Entity(ID_ECOST_PER_MONTH, "Monthly E-cost", None, "VNĐ", "mdi:cash-multiple"),
    Entity(
        ID_LATEST_UPDATE,
        "Latest Update",
        DEVICE_CLASS_TIMESTAMP,
        None,
        "mdi:calendar-check",
    ),
    Entity(ID_FROM_DATE, "Date Start", None, None, "mdi:calendar-clock"),
    Entity(ID_TO_DATE, "Last Date", None, None, "mdi:calendar-clock"),
]

VIETNAM_ECOST_PARAMS = [1678, 1734, 2014, 2536, 2834, 2927]  # in VND
VIETNAM_ECOST_STAGES = [0, 50, 100, 200, 300, 400]  # in kWh
VIETNAM_ECOST_VAT = 10  # in %


@dataclass
class Area:
    """Describe the supported areas."""

    name: str
    evn_login_url: str
    evn_data_request_url: str


VIETNAM_EVN_AREA = [
    Area(
        "EVNHCMC - Ho Chi Minh City",
        "https://cskh.evnhcmc.vn/Dangnhap/checkLG",
        "https://cskh.evnhcmc.vn/Tracuu/ajax_dienNangTieuThuTheoNgay",
    ),
    Area(
        "EVNSPC - Southern Vietnam",
        "",
        "https://www.cskh.evnspc.vn/TraCuu/TraCuuSanLuongDienTieuThuTrongNgay",
    ),
]
