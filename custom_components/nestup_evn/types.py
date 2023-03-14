from array import ArrayType
from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import ENERGY_KILO_WATT_HOUR

from .const import (
    ID_ECON_DAILY_NEW,
    ID_ECON_DAILY_OLD,
    ID_ECON_MONTHLY_NEW,
    ID_ECON_TOTAL_NEW,
    ID_ECON_TOTAL_OLD,
    ID_ECOST_DAILY_NEW,
    ID_ECOST_DAILY_OLD,
    ID_ECOST_MONTHLY_NEW,
    ID_FROM_DATE,
    ID_LATEST_UPDATE,
    ID_M_PAYMENT_NEEDED,
    ID_PAYMENT_NEEDED,
    ID_TO_DATE,
)


@dataclass
class Entity:
    """Describe the sensor entities."""

    id: str
    friendly_name: str
    entity_class: str
    unit: str
    icon: str
    state_class: SensorStateClass or None


@dataclass
class Area:
    """Describe the supported areas."""

    name: str
    key: str | None = None
    location: str | None = None
    evn_login_url: str | None = None
    evn_data_url: str | None = None
    evn_payment_url: str | None = None
    supported: bool = True
    date_needed: bool = True
    pattern: ArrayType | None = None


@dataclass
class EVN_NAME:
    """Describe the EVN names."""

    HANOI = "EVNHANOI"
    HCMC = "EVNHCMC"
    NPC = "EVNNPC"
    CPC = "EVNCPC"
    SPC = "EVNSPC"


@dataclass
class EVNRequiredKeysMixin:
    """Mixin for required keys."""

    value_fn: Callable[[Any], float]


@dataclass
class EVNSensorEntityDescription(SensorEntityDescription, EVNRequiredKeysMixin):
    """Describes EVN sensor entity."""

    dynamic_name: None | bool = False
    dynamic_icon: None | bool = False


VIETNAM_EVN_AREA = [
    Area(
        name=EVN_NAME.HANOI,
        location="Thủ đô Hà Nội",
        evn_login_url="https://apicskh.evnhanoi.com.vn/connect/token",
        evn_data_url="https://evnhanoi.vn/api/TraCuu/LayChiSoDoXa",
        evn_payment_url="https://evnhanoi.vn/api/TraCuu/GetListThongTinNoKhachHang",
        pattern=["PD"],
    ),
    Area(
        name=EVN_NAME.HCMC,
        location="Thành phố Hồ Chí Minh",
        evn_login_url="https://cskh.evnhcmc.vn/Dangnhap/checkLG",
        evn_data_url="https://cskh.evnhcmc.vn/Tracuu/ajax_dienNangTieuThuTheoNgay",
        evn_payment_url="https://cskh.evnhcmc.vn/Tracuu/kiemTraNo",
        pattern=["PE"],
    ),
    Area(
        name=EVN_NAME.NPC,
        location="Khu vực miền Bắc",
        evn_login_url="https://billnpccc.enterhub.asia/login",
        evn_data_url="https://billnpccc.enterhub.asia/dailyconsump",
        evn_payment_url="https://billnpccc.enterhub.asia/mobileapi/home/",
        pattern=["PA", "PH", "PM", "PN"],
    ),
    Area(
        name=EVN_NAME.CPC,
        location="Khu vực miền Trung",
        evn_login_url="https://cskh-api.cpc.vn/connect/token",
        evn_data_url="https://cskh-api.cpc.vn/api/cskh/power-consumption-alerts/by-customer-code/",
        evn_payment_url="https://appcskh.cpc.vn:4433/api/v4/customer/home/",
        date_needed=False,
        pattern=["PQ", "PC", "PP"],
    ),
    Area(
        name=EVN_NAME.SPC,
        location="Khu vực miền Nam",
        evn_login_url="https://api.cskh.evnspc.vn/api/user/authenticate",
        evn_data_url="https://api.cskh.evnspc.vn/api/NghiepVu/LayThongTinSanLuongTheoNgay",
        evn_payment_url="https://api.cskh.evnspc.vn/api/NghiepVu/TraCuuNoHoaDon",
        pattern=["PB", "PK"],
    ),
]

EVN_SENSORS: tuple[EVNSensorEntityDescription, ...] = (
    # Current day
    EVNSensorEntityDescription(
        key=ID_ECON_DAILY_NEW,
        name="Sản lượng",
        icon="mdi:flash-outline",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_DAILY_NEW],
        dynamic_name=True,
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_DAILY_NEW,
        name="Tiền điện",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_ECOST_DAILY_NEW],
        dynamic_name=True,
    ),
    # Previous day
    EVNSensorEntityDescription(
        key=ID_ECON_DAILY_OLD,
        name="Sản lượng",
        icon="mdi:flash-outline",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_DAILY_OLD],
        dynamic_name=True,
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_DAILY_OLD,
        name="Tiền điện",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_ECOST_DAILY_OLD],
        dynamic_name=True,
    ),
    # Current month
    EVNSensorEntityDescription(
        key=ID_ECON_MONTHLY_NEW,
        name="Sản lượng tháng này",
        icon="mdi:flash-outline",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_MONTHLY_NEW],
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_MONTHLY_NEW,
        name="Tiền điện tháng này",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_ECOST_MONTHLY_NEW],
    ),
    # Total e-consumption
    EVNSensorEntityDescription(
        key=ID_ECON_TOTAL_NEW,
        name="Chỉ số tạm chốt",
        icon="mdi:arrow-up-bold-box-outline",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_TOTAL_NEW],
    ),
    EVNSensorEntityDescription(
        key=ID_ECON_TOTAL_OLD,
        name="Chỉ số đầu kì",
        icon="mdi:arrow-down-bold-box-outline",
        native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_TOTAL_OLD],
    ),
    # Dates
    EVNSensorEntityDescription(
        key=ID_TO_DATE,
        name="Ngày tạm chốt",
        icon="mdi:calendar-clock",
        value_fn=lambda data: data[ID_TO_DATE],
    ),
    EVNSensorEntityDescription(
        key=ID_FROM_DATE,
        name="Ngày đầu kì",
        icon="mdi:calendar-clock",
        value_fn=lambda data: data[ID_FROM_DATE],
    ),
    EVNSensorEntityDescription(
        key=ID_LATEST_UPDATE,
        name="Lần cập nhật cuối",
        icon="mdi:calendar-check",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data[ID_LATEST_UPDATE],
    ),
    # Previous bill
    EVNSensorEntityDescription(
        key=ID_PAYMENT_NEEDED,
        name="Hóa đơn cũ",
        icon="mdi:comment-question-outline",
        value_fn=lambda data: data[ID_PAYMENT_NEEDED],
        dynamic_icon=True,
    ),
    EVNSensorEntityDescription(
        key=ID_M_PAYMENT_NEEDED,
        name="Tiền nợ",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_M_PAYMENT_NEEDED],
        dynamic_icon=True,
    ),
)
