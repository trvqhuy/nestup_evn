import json, requests
from datetime import datetime
from typing import Any
from bs4 import BeautifulSoup
from homeassistant.util import Throttle

from datetime import timedelta
from homeassistant.util import Throttle

SCAN_INTERVAL = timedelta(minutes=POLLING_INTERVAL_IN_MINS)

import logging

_LOGGER = logging.getLogger(__name__)

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .const import (
    CONF_AREA,
    CONF_CUSTOMER_ID,
    CONF_ERR_CANNOT_CONNECT,
    CONF_ERR_INVALID_AUTH,
    CONF_ERR_UNKNOWN,
    CONF_MONTHLY_START,
    CONF_PASSWORD,
    CONF_SUCCESS,
    CONF_USERNAME,
    ID_ECON_PER_DAY,
    ID_ECON_PER_MONTH,
    ID_ECOST_PER_DAY,
    ID_ECOST_PER_MONTH,
    ID_FROM_DATE,
    ID_LATEST_UPDATE,
    ID_TO_DATE,
    POLLING_INTERVAL_IN_MINS,
    VIETNAM_ECOST_PARAMS,
    VIETNAM_ECOST_STAGES,
    VIETNAM_ECOST_VAT,
    VIETNAM_EVN_AREA,
)


class EVNData:
    def __init__(self, dataset, api):

        if CONF_USERNAME in dataset:
            self._username = dataset[CONF_USERNAME]
            self._password = dataset[CONF_PASSWORD]
        else:
            self._username = None
            self._password = None

        self._area_name = dataset[CONF_AREA]
        self._customer_id = dataset[CONF_CUSTOMER_ID]
        self._monthly_start = dataset[CONF_MONTHLY_START]

        self._api = api
        self._data = {}

    @Throttle(SCAN_INTERVAL)
    def update(self):
        if self._area_name == VIETNAM_EVN_AREA[0].name:
            if (
                self._api.login(self._area_name, self._username, self._password)
                != CONF_SUCCESS
            ):
                return

        _LOGGER.debug(
            "[HA EVN Monitor] Updating data for ID %s (Username %s)", self._customer_id
        )

        self._data = self._api.request_update(
            self._area_name, self._customer_id, self._monthly_start
        )

    def get_data(self, variable: Any) -> Any:
        """Get saved EVN data with specific variable"""
        return self._data.get(variable)


class EVNAPI:
    def __init__(self):
        self._session = requests.Session()
        self._area_name = ""
        self._test = 0

    def login(self, area_name, username, password) -> str:
        """Create EVN login session corresponding with a specific area"""
        self._area_name = [area for area in VIETNAM_EVN_AREA if area.name == area_name][
            0
        ]

        payload = {"u": username, "p": password}

        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"

        resp = self._session.post(
            url=self._area_name.evn_login_url, data=payload, verify=True
        )

        if resp.status_code != 200:
            _LOGGER.error(f"Cannot connect to EVN Server while loging in - {resp.text}")
            return CONF_ERR_CANNOT_CONNECT

        try:
            resp_json = json.loads(resp.text)
        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while loging in - {error}"
            )
            return CONF_ERR_UNKNOWN

        login_state = resp_json["state"]

        if (login_state == CONF_SUCCESS) or (login_state == "login"):
            return CONF_SUCCESS

        _LOGGER.error(f"Unable to login into EVN Endpoint - {resp.text}")
        return CONF_ERR_INVALID_AUTH

    def request_update_evnhcmc(self, customer_id, start_datetime, end_datetime):

        resp = self._session.post(
            url=self._area_name.evn_data_request_url,
            data={
                "input_makh": customer_id,
                "input_tungay": start_datetime,
                "input_denngay": end_datetime,
            },
            verify=True,
        )

        if resp.status_code != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while requesting new data - {resp.text}"
            )
            return {"status": "error", "data": resp.text}

        try:
            resp_json = json.loads(resp.text)
        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data - {error}"
            )
            return {"status": "error", "data": error}

        state = resp_json["state"]

        if state != CONF_SUCCESS:
            _LOGGER.error(f"Cannot request new data from EVN Server - {resp.text}")
            return {"status": "error", "data": resp.text}

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(resp_json["data"]["sanluong_tungngay"][-1]["Tong"]),
            ID_ECON_PER_MONTH: float(resp_json["data"]["sanluong_tong"]["Tong"]),
        }

    def request_update_evnspc(self, customer_id, start_datetime, end_datetime):

        resp = self._session.post(
            url=self._area_name.evn_data_request_url,
            data={
                "MaKhachHangChiSoChot": customer_id,
                "TuNgayChiSoChot": start_datetime.replace("/", "-"),
                "DenNgayChiSoChot": end_datetime.replace("/", "-"),
                "check": "1",
            },
            verify=False,
        )

        if resp.status_code != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while requesting new data - {resp.text}"
            )
            return {"status": "error", "data": resp.text}

        resp_json = {}

        try:
            soup = BeautifulSoup(resp.content, "html.parser")
            json_data = {}

            for index, data in enumerate(soup.find_all("td")):
                item = data.text

                if index == 1:
                    resp_json = {"total": float(item), "data": []}
                elif index > 1:
                    if not ((index - 1) % 3):
                        json_data["value"] = float(item)
                        resp_json["data"].append(json_data)
                    elif not (index % 3):
                        json_data = {}
                        json_data["date"] = item

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data - {error}"
            )
            return {"status": "error", "data": error}

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(resp_json["data"][-1]["value"]),
            ID_ECON_PER_MONTH: float(resp_json["total"]),
        }

    def request_update(self, area_name, customer_id, monthly_start) -> dict[str, Any]:
        """Request new update from EVN Server, corresponding with the last session"""

        fetch_data = {}
        from_date, to_date = "", ""

        if area_name == VIETNAM_EVN_AREA[0].name:
            from_date, to_date = generate_datetime(monthly_start)
            fetch_data = self.request_update_evnhcmc(customer_id, from_date, to_date)

        elif area_name == VIETNAM_EVN_AREA[1].name:
            from_date, to_date = generate_datetime(monthly_start)
            self._area_name = [
                area for area in VIETNAM_EVN_AREA if area.name == area_name
            ][0]
            fetch_data = self.request_update_evnspc(customer_id, from_date, to_date)

        if fetch_data["status"] == CONF_SUCCESS:
            fetch_data.update(
                {
                    ID_ECOST_PER_DAY: calc_ecost(fetch_data[ID_ECON_PER_DAY]),
                    ID_ECOST_PER_MONTH: calc_ecost(fetch_data[ID_ECON_PER_MONTH]),
                    ID_FROM_DATE: from_date,
                    ID_TO_DATE: to_date,
                    ID_LATEST_UPDATE: datetime.now().astimezone(),
                }
            )

        return fetch_data


def generate_datetime(monthly_start: int):
    time_obj = datetime.now()
    current_day = int(time_obj.strftime("%-d"))
    monthly_start_str = "{:0>2}".format(monthly_start)

    start_datetime = ""
    end_datetime = f"{'{:0>2}'.format(current_day - 1)}/{time_obj.strftime('%m/%Y')}"
    if current_day > monthly_start:
        start_datetime = f"{monthly_start_str}/{time_obj.strftime('%m/%Y')}"
    else:
        last_month = int(time_obj.strftime("%-m")) - 1

        if last_month:
            last_month_str = "{:0>2}".format(last_month)
            start_datetime = (
                f"{monthly_start_str}/{last_month_str}/{time_obj.strftime('%Y')}"
            )
        else:
            last_year = int(time_obj.strftime("%Y")) - 1
            start_datetime = f"{monthly_start_str}/12/{last_year}"

    return start_datetime, end_datetime


def calc_ecost(kwh: float) -> str:
    price = 0.0

    for i in range(len(VIETNAM_ECOST_STAGES)):
        if kwh > VIETNAM_ECOST_STAGES[i]:
            if i == (len(VIETNAM_ECOST_STAGES) - 1):
                price += (kwh - VIETNAM_ECOST_STAGES[i]) * VIETNAM_ECOST_PARAMS[i]
            else:
                price += (
                    (VIETNAM_ECOST_STAGES[i + 1] - VIETNAM_ECOST_STAGES[i])
                    if kwh > VIETNAM_ECOST_STAGES[i + 1]
                    else (kwh - VIETNAM_ECOST_STAGES[i])
                ) * VIETNAM_ECOST_PARAMS[i]

    result = int(round(price * (100 + VIETNAM_ECOST_VAT) / 100))

    return str(result)
