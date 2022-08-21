import json
from datetime import datetime
from typing import Any
from bs4 import BeautifulSoup
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
    async_get_clientsession,
)

import ssl

import logging

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_ERR_CANNOT_CONNECT,
    CONF_ERR_INVALID_AUTH,
    CONF_ERR_UNKNOWN,
    CONF_SUCCESS,
    ID_ECON_PER_DAY,
    ID_ECON_PER_MONTH,
    ID_ECOST_PER_DAY,
    ID_ECOST_PER_MONTH,
    ID_FROM_DATE,
    ID_LATEST_UPDATE,
    ID_TO_DATE,
    VIETNAM_ECOST_PARAMS,
    VIETNAM_ECOST_STAGES,
    VIETNAM_ECOST_VAT,
)

from .types import VIETNAM_EVN_AREA


class EVNAPI:
    def __init__(self, hass: HomeAssistant, is_new_session=False):

        self._session = (
            async_create_clientsession(hass)
            if is_new_session
            else async_get_clientsession(hass)
        )

        self._area_name = ""

    async def login(self, area_name, username, password) -> str:
        """Create EVN login session corresponding with a specific area"""
        self._area_name = [area for area in VIETNAM_EVN_AREA if area.name == area_name][
            0
        ]

        payload = {"u": username, "p": password}

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._area_name.evn_login_url, data=payload, ssl=ssl_context
        )

        if resp.status != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while loging in: status code {resp.status}"
            )
            return CONF_ERR_CANNOT_CONNECT

        res = await resp.text()

        try:
            resp_json = json.loads(res)
        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while loging in: {error}"
            )
            return CONF_ERR_UNKNOWN

        login_state = resp_json["state"]

        if (login_state == CONF_SUCCESS) or (login_state == "login"):
            return CONF_SUCCESS

        _LOGGER.error(f"Unable to login into EVN Endpoint: {resp_json}")
        return CONF_ERR_INVALID_AUTH

    async def request_update_evnhcmc(self, customer_id, start_datetime, end_datetime):

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._area_name.evn_data_request_url,
            data={
                "input_makh": customer_id,
                "input_tungay": start_datetime,
                "input_denngay": end_datetime,
            },
            ssl=ssl_context,
        )

        if resp.status != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while requesting new data: status code {resp.status}"
            )
            return {"status": "error", "data": resp.status}

        try:
            res = await resp.text()
            resp_json = json.loads(res)

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data: {error}"
            )
            return {"status": "error", "data": error}

        state = resp_json["state"]

        if state != CONF_SUCCESS:
            _LOGGER.error(f"Cannot request new data from EVN Server: {resp_json}")
            return {"status": state, "data": resp_json}

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(resp_json["data"]["sanluong_tungngay"][-1]["Tong"]),
            ID_ECON_PER_MONTH: float(resp_json["data"]["sanluong_tong"]["Tong"]),
        }

    async def request_update_evnspc(self, customer_id, start_datetime, end_datetime):

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._area_name.evn_data_request_url,
            data={
                "MaKhachHangChiSoChot": customer_id,
                "TuNgayChiSoChot": start_datetime.replace("/", "-"),
                "DenNgayChiSoChot": end_datetime.replace("/", "-"),
                "check": "1",
            },
            ssl=False,
        )

        try:
            res = await resp.text()

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data: {error}"
            )
            return {"status": "error", "data": error}

        if resp.status != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while requesting new data: status code {resp.status}"
            )
            return {"status": "error", "data": res}

        resp_json = {}

        try:
            soup = BeautifulSoup(res, "html.parser")
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

        if resp_json == {}:
            _LOGGER.error(
                f"Cannot request new data from EVN Server: Invalid EVN Customer ID"
            )
            return {"status": "error_ma_kh_deny", "data": resp_json}

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(resp_json["data"][-1]["value"]),
            ID_ECON_PER_MONTH: float(resp_json["total"]),
        }

    async def request_update(
        self, area_name, customer_id, monthly_start
    ) -> dict[str, Any]:
        """Request new update from EVN Server, corresponding with the last session"""

        fetch_data = {}
        from_date, to_date = "", ""

        if area_name == VIETNAM_EVN_AREA[0].name:
            from_date, to_date = generate_datetime(monthly_start)
            fetch_data = await self.request_update_evnhcmc(
                customer_id, from_date, to_date
            )

        elif area_name == VIETNAM_EVN_AREA[1].name:
            from_date, to_date = generate_datetime(monthly_start)
            self._area_name = [
                area for area in VIETNAM_EVN_AREA if area.name == area_name
            ][0]
            fetch_data = await self.request_update_evnspc(
                customer_id, from_date, to_date
            )

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
