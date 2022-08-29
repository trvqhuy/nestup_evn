"""Setup and manage the EVN API."""

from dataclasses import asdict
from datetime import datetime, timedelta
from dateutil import parser
import json
import logging
import os
import ssl
from typing import Any

from bs4 import BeautifulSoup

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
    async_get_clientsession,
)

from .const import (
    CONF_ERR_CANNOT_CONNECT,
    CONF_ERR_INVALID_AUTH,
    CONF_ERR_INVALID_ID,
    CONF_ERR_NO_MONITOR,
    CONF_ERR_NOT_SUPPORTED,
    CONF_ERR_UNKNOWN,
    CONF_SUCCESS,
    ID_ECON_PER_DAY,
    ID_ECON_PER_MONTH,
    ID_ECOST_PER_DAY,
    ID_ECOST_PER_MONTH,
    ID_FROM_DATE,
    ID_LATEST_UPDATE,
    ID_TO_DATE,
    VIETNAM_ECOST_STAGES,
    VIETNAM_ECOST_VAT,
)
from .types import EVN_NAME, VIETNAM_EVN_AREA, Area

_LOGGER = logging.getLogger(__name__)


class EVNAPI:
    def __init__(self, hass: HomeAssistant, is_new_session=False):
        """Construct EVNAPI wrapper."""

        self._session = (
            async_create_clientsession(hass)
            if is_new_session
            else async_get_clientsession(hass)
        )

        self._evn_area = {}

    async def login(self, evn_area, username, password) -> str:
        """Try login into EVN corresponding with different EVN areas"""

        self._evn_area = evn_area

        if not evn_area.get("auth_needed"):
            return CONF_SUCCESS

        if (username is None) or (password is None):
            return CONF_ERR_UNKNOWN

        if evn_area.get("name") == EVN_NAME.HCMC:
            return await self.login_evnhcmc(username, password)

        elif evn_area.get("name") == EVN_NAME.HANOI:
            return await self.login_evnhanoi(username, password)

        elif evn_area.get("name") == EVN_NAME.CPC:
            return await self.login_evncpc(username, password)

        return CONF_ERR_UNKNOWN

    async def request_update(
        self, evn_area: Area, customer_id, monthly_start
    ) -> dict[str, Any]:
        """Request new update from EVN Server, corresponding with the last session"""

        self._evn_area = evn_area

        fetch_data = {}

        if evn_area.get("name") == EVN_NAME.HANOI:
            from_date, to_date = generate_datetime(monthly_start, offset=1)
            fetch_data = await self.request_update_evnhanoi(
                customer_id, from_date, to_date
            )

        elif evn_area.get("name") == EVN_NAME.SPC:
            from_date, to_date = generate_datetime(monthly_start, offset=1)
            fetch_data = await self.request_update_evnspc(
                customer_id, from_date, to_date
            )

        from_date, to_date = generate_datetime(monthly_start)

        if evn_area.get("name") == EVN_NAME.HCMC:
            fetch_data = await self.request_update_evnhcmc(
                customer_id, from_date, to_date
            )

        elif evn_area.get("name") == EVN_NAME.NPC:
            fetch_data = await self.request_update_evnnpc(
                customer_id, from_date, to_date
            )

        elif evn_area.get("name") == EVN_NAME.CPC:
            fetch_data = await self.request_update_evncpc(
                customer_id, from_date, to_date
            )

        if fetch_data["status"] == CONF_SUCCESS:
            fetch_data.update(
                {
                    ID_ECOST_PER_DAY: calc_ecost(fetch_data[ID_ECON_PER_DAY]),
                    ID_ECOST_PER_MONTH: calc_ecost(fetch_data[ID_ECON_PER_MONTH]),
                    ID_LATEST_UPDATE: datetime.now().astimezone(),
                }
            )

            if not ID_FROM_DATE in fetch_data:
                fetch_data[ID_FROM_DATE] = from_date

            if not ID_TO_DATE in fetch_data:
                fetch_data[ID_TO_DATE] = to_date
                

        return fetch_data

    async def login_evncpc(self, username, password) -> str:
        """Create EVN login session corresponding with EVNCPC Endpoint"""

        payload = {
            "username": username,
            "password": password,
            "scope": "CSKH",
            "grant_type": "password",
        }

        headers = {"Authorization": "Basic Q1NLSF9Td2FnZ2VyOjFxMnczZSo="}

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"), data=payload, headers=headers
        )

        if resp.status != 200:
            if resp.status == 400:
                _LOGGER.error(
                    "Cannot login into EVN Server: Invalid EVN Authentication"
                )
                return CONF_ERR_INVALID_AUTH

            _LOGGER.error(
                f"Cannot connect to EVN Server while loging in: status code {resp.status}"
            )
            return CONF_ERR_CANNOT_CONNECT

        try:
            res = await resp.text()
            resp_json = json.loads(res)

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while loging in: {error}"
            )
            return CONF_ERR_UNKNOWN

        if ("error" in resp_json) and (resp_json["error"] == "invalid_grant"):
            return CONF_ERR_INVALID_AUTH

        elif "access_token" in resp_json:
            self._evn_area["access_token"] = resp_json["access_token"]
            return CONF_SUCCESS

        _LOGGER.error(f"Error while logging in EVN Endpoints: {resp_json}")
        return CONF_ERR_UNKNOWN

    async def login_evnhanoi(self, username, password) -> str:
        """Create EVN login session corresponding with EVNHANOI Endpoint"""

        payload = {
            "username": username,
            "password": password,
            "client_id": "httplocalhost4500",
            "client_secret": "secret",
            "grant_type": "password",
        }

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"), 
            data=payload,
        )

        if resp.status != 200:
            if resp.status == 400:
                _LOGGER.error(
                    "Cannot login into EVN Server: Invalid EVN Authentication"
                )
                return CONF_ERR_INVALID_AUTH

            _LOGGER.error(
                f"Cannot connect to EVN Server while loging in: status code {resp.status}"
            )
            return CONF_ERR_CANNOT_CONNECT

        try:
            res = await resp.text()
            resp_json = json.loads(res)

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while loging in: {error}"
            )
            return CONF_ERR_UNKNOWN

        if ("error" in resp_json) and (resp_json["error"] == "invalid_grant"):
            return CONF_ERR_INVALID_AUTH

        elif "access_token" in resp_json:
            self._evn_area["access_token"] = resp_json["access_token"]
            return CONF_SUCCESS

        _LOGGER.error(f"Error while logging in EVN Endpoints: {resp_json}")
        return CONF_ERR_UNKNOWN

    async def login_evnhcmc(self, username, password) -> str:
        """Create EVN login session corresponding with EVNHCMC Endpoint"""

        payload = {"u": username, "p": password}

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"), data=payload, ssl=ssl_context
        )

        if resp.status != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while loging in: status code {resp.status}"
            )
            return CONF_ERR_CANNOT_CONNECT

        try:
            res = await resp.text()
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

    async def request_update_evnhanoi(
        self, customer_id, start_datetime, end_datetime, last_index="001"
    ):
        """Request new update from EVNHANOI Server"""

        headers = {
            "Authorization": f"Bearer {self._evn_area.get('access_token')}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        data = {
            "maDiemDo": f"{customer_id}{last_index}",
            "maDonVi": f"{customer_id[0:6]}",
            "maXacThuc": "EVNHN",
            "ngayDau": start_datetime,
            "ngayCuoi": end_datetime,
        }

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_data_request_url"),
            data=json.dumps(data),
            headers=headers,
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
            state = CONF_ERR_UNKNOWN if resp_json["isError"] else CONF_SUCCESS

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data: {error}"
            )
            return {"status": "error", "data": error}

        if state != CONF_SUCCESS:
            
            if resp_json["code"] == 400:

                if last_index == "001":
                    return await self.request_update_evnhanoi(
                        customer_id, start_datetime, end_datetime, "1"
                    )

                return {"status": CONF_ERR_INVALID_ID, "data": resp_json}

            _LOGGER.error(f"Cannot request new data from EVN Server for customer ID: {customer_id}\n{resp_json}")

            return {"status": state, "data": resp_json}

        last_day =  parser.parse(resp_json["data"]["tongSanLuong"]["ngayCuoiKy"]) - timedelta(days=1)

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: round(float(resp_json["data"]["chiSoNgay"][-1]["sg"])
            - float(resp_json["data"]["chiSoNgay"][-2]["sg"]), 2),
            ID_ECON_PER_MONTH: round(float(resp_json["data"]["tongSanLuong"]["sg"]), 2),
            ID_TO_DATE: last_day.strftime('%-d/%m/%Y'),
        }

    async def request_update_evncpc(self, customer_id, start_datetime, end_datetime):
        """Request new update from EVNCPC Server"""

        headers = {"Authorization": f"Bearer {self._evn_area.get('access_token')}"}

        resp = await self._session.get(
            url=f"{self._evn_area.get('evn_data_request_url')}{customer_id}",
            headers=headers,
        )

        if resp.status != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while requesting new data: status code {resp.status}"
            )
            return {"status": "error", "data": resp.status}

        try:
            res = await resp.text()

            resp_json = json.loads(res)

            state = CONF_SUCCESS if bool(resp_json) else CONF_SUCCESS

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data: {error}"
            )
            return {"status": "error", "data": error}

        if state != CONF_SUCCESS:
            _LOGGER.error(f"Cannot request new data from EVN Server for customer ID: {customer_id}\n{resp_json}")

            return {"status": state, "data": resp_json}

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(
                resp_json["electricConsumption"]["electricConsumptionToday"]
            ),
            ID_ECON_PER_MONTH: float(
                resp_json["electricConsumption"]["electricConsumptionThisMonth"]
            ),
        }

    async def request_update_evnhcmc(self, customer_id, start_datetime, end_datetime):
        """Request new update from EVNHCMC Server"""

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_data_request_url"),
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
            state = resp_json["state"]

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data: {error}"
            )
            return {"status": "error", "data": error}

        if state != CONF_SUCCESS:
            _LOGGER.error(f"Cannot request new data from EVN Server for customer ID: {customer_id}\n{resp_json}")
            return {"status": state, "data": resp_json}

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(resp_json["data"]["sanluong_tungngay"][-1]["Tong"]),
            ID_ECON_PER_MONTH: float(resp_json["data"]["sanluong_tong"]["Tong"]),
            ID_TO_DATE: resp_json["data"]["sanluong_tungngay"][-1]["ngayFull"],
        }

    async def request_update_evnspc(self, customer_id, start_datetime, end_datetime):
        """Request new update from EVNSPC Server"""

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_data_request_url"),
            data={
                "MaKhachHangChiSoChot": customer_id,
                "TuNgayChiSoChot": start_datetime.replace("/", "-"),
                "DenNgayChiSoChot": end_datetime.replace("/", "-"),
                "check": "1",
            },
            ssl=False,
        )

        if resp.status != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while requesting new data: status code {resp.status}"
            )
            return {"status": "error", "data": resp.status}

        try:
            res = await resp.text()
            
        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data: {error}"
            )
            return {"status": "error", "data": error}

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

            error = CONF_ERR_INVALID_ID

            table = soup.findAll("div", attrs={"class": "box-information"})
            for x in table:
                if (
                    x.find("p").text
                    == "Quý khách hàng hiện không có thông tin sản lượng điện tiêu thụ trong ngày."
                ):
                    error = CONF_ERR_NO_MONITOR

            _LOGGER.error(
                "Cannot request new data from EVN Server: Invalid EVN Customer ID"
            )

            return {"status": error, "data": soup}

        data_list = list(resp_json["data"])        
        last_day =  parser.parse(data_list[-1]["date"]) - timedelta(days=1)

        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(data_list[-1]["value"]),
            ID_ECON_PER_MONTH: float(resp_json["total"]),
            ID_TO_DATE: last_day.strftime('%d/%m/%Y'),
        }

    async def request_update_evnnpc(self, customer_id, start_datetime, end_datetime):
        """Request new update from EVNNPC Server"""

        try:
            ssl_context = ssl.create_default_context()
            ssl_context.set_ciphers("ALL:@SECLEVEL=1")

            resp = await self._session.get(
                url=self._evn_area.get("evn_data_request_url"),
                params={
                    "MA_DDO": f"{customer_id}001",
                    "STARTTIME": start_datetime.replace("/", "-"),
                    "STOPTIME": end_datetime.replace("/", "-"),
                },
                ssl=ssl_context,
            )

        except Exception as error:
            _LOGGER.error(
                f"Unable to fetch data from EVN Server while requesting new data: {error}"
            )
            return {"status": "error", "data": error}

        if resp.status != 200:
            _LOGGER.error(
                f"Cannot connect to EVN Server while requesting new data: status code {resp.status}"
            )
            return {"status": "error", "data": resp.status}

        try:
            res = await resp.text()
            resp_json = json.loads(res)

            info_list = []

            for each_entity in resp_json:
                if "Sản lượng điện tiêu thụ của khách hàng" in each_entity["GHI_CHU"]:
                    info_list.append(each_entity)

        except Exception as error:
            _LOGGER.error(
                f"Cannot request new data from EVN Server: Invalid EVN Customer ID\n{error}"
            )

            return {
                "status": CONF_ERR_INVALID_ID,
                "data": "Cannot request e-consumption data",
            }

        last_day =  parser.parse(info_list[0]["THOI_GIAN_BAT_DAU"])

        if info_list == []:
            return {
                "status": CONF_ERR_NO_MONITOR,
                "data": str(resp_json[0]),
            }

        elif len(info_list) == 1:
            return {
                "status": CONF_SUCCESS,
                ID_ECON_PER_DAY: float(info_list[0]["SAN_LUONG"]),
                ID_ECON_PER_MONTH: round(
                    float(info_list[0]["CHI_SO_KET_THUC"])
                    - float(info_list[0]["CHI_SO_BAT_DAU"]),
                    2,
                ),
                ID_TO_DATE: last_day.strftime('%d/%m/%Y'),
            }
        
        return {
            "status": CONF_SUCCESS,
            ID_ECON_PER_DAY: float(info_list[0]["SAN_LUONG"]),
            ID_ECON_PER_MONTH: round(
                float(info_list[0]["CHI_SO_KET_THUC"])
                - float(info_list[-1]["CHI_SO_BAT_DAU"]),
                2,
            ),
            ID_TO_DATE: last_day.strftime('%d/%m/%Y'),
        }


def get_evn_info(evn_customer_id: str):
    """Get EVN infomations based on Customer ID -> EVN Company, location, branches,..."""

    for index, each_area in enumerate(VIETNAM_EVN_AREA):
        for each_pattern in each_area.pattern:
            if each_pattern in evn_customer_id:

                evn_branch = "Unknown"

                file_path = os.path.join(os.path.dirname(__file__), "evn_branches.json")

                with open(file_path) as f:
                    evn_branches_list = json.load(f)

                    for evn_id in evn_branches_list:
                        if evn_id in evn_customer_id:
                            evn_branch = evn_branches_list[evn_id]

                status = CONF_SUCCESS

                if not VIETNAM_EVN_AREA[index].supported:
                    status = CONF_ERR_NOT_SUPPORTED

                return {
                    "status": status,
                    "customer_id": evn_customer_id,
                    "evn_area": asdict(each_area),
                    "evn_name": each_area.name,
                    "evn_location": each_area.location,
                    "evn_branch": evn_branch,
                }

    return {"status": CONF_ERR_UNKNOWN}


def generate_datetime(monthly_start: int, offset=0):
    """Generate Datetime as string for requesting data purposes"""
    time_obj = datetime.now()
    current_day = int(time_obj.strftime("%-d"))
    monthly_start_str = "{:0>2}".format(monthly_start)

    if current_day == monthly_start + 1:
        last_month = int(time_obj.strftime("%-m")) - 1

        last_month_str = "{:0>2}".format(last_month)
        start_datetime = (
            f"{monthly_start_str}/{last_month_str}/{time_obj.strftime('%Y')}"
        )
        end_datetime = (
            f"{'{:0>2}'.format(current_day - 1 + offset)}/{time_obj.strftime('%m/%Y')}"
        )

        return start_datetime, end_datetime

    start_datetime = ""
    end_datetime = (
        f"{'{:0>2}'.format(current_day - 1 + offset)}/{time_obj.strftime('%m/%Y')}"
    )

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
    """Calculate electric cost based on e-consumption"""

    total_price = 0.0

    e_stage_list = list(VIETNAM_ECOST_STAGES.keys())

    for index, e_stage in enumerate(e_stage_list):
        if kwh < e_stage:
            break

        if e_stage == e_stage_list[-1]:
            total_price += (kwh - e_stage) * VIETNAM_ECOST_STAGES[e_stage]
        else:
            next_stage = e_stage_list[index + 1]
            total_price += (
                (next_stage - e_stage) if kwh > next_stage else (kwh - e_stage)
            ) * VIETNAM_ECOST_STAGES[e_stage]

    total_price = int(round((total_price / 100) * (100 + VIETNAM_ECOST_VAT)))

    return str(total_price)
