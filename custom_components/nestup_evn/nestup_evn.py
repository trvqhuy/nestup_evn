"""Setup and manage the EVN API."""

import base64
from dataclasses import asdict
from datetime import datetime, timedelta
import json
import logging
import os
import ssl
from typing import Any
import uuid

from dateutil import parser

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
    async_get_clientsession,
)

from .const import (
    CONF_EMPTY,
    CONF_ERR_CANNOT_CONNECT,
    CONF_ERR_INVALID_AUTH,
    CONF_ERR_INVALID_ID,
    CONF_ERR_NO_MONITOR,
    CONF_ERR_NOT_SUPPORTED,
    CONF_ERR_UNKNOWN,
    CONF_SUCCESS,
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
    STATUS_N_PAYMENT_NEEDED,
    STATUS_PAYMENT_NEEDED,
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

        if (username is None) or (password is None):
            return CONF_ERR_UNKNOWN

        if evn_area.get("name") == EVN_NAME.HCMC:
            return await self.login_evnhcmc(username, password)

        elif evn_area.get("name") == EVN_NAME.HANOI:
            return await self.login_evnhanoi(username, password)

        elif evn_area.get("name") == EVN_NAME.CPC:
            return await self.login_evncpc(username, password)

        elif evn_area.get("name") == EVN_NAME.SPC:
            return await self.login_evnspc(username, password)

        elif evn_area.get("name") == EVN_NAME.NPC:
            return await self.login_evnnpc(username, password)

        return CONF_ERR_UNKNOWN

    async def request_update(
        self, evn_area: Area, customer_id, monthly_start=None
    ) -> dict[str, Any]:
        """Request new update from EVN Server, corresponding with the last session"""

        self._evn_area = evn_area

        fetch_data = {}

        if evn_area.get("name") == EVN_NAME.CPC:
            fetch_data = await self.request_update_evncpc(customer_id)

        elif evn_area.get("name") == EVN_NAME.HANOI:
            from_date, to_date = generate_datetime(monthly_start, offset=1)
            fetch_data = await self.request_update_evnhanoi(
                customer_id, from_date, to_date
            )

        elif evn_area.get("name") == EVN_NAME.SPC:
            from_date, to_date = generate_datetime(monthly_start, offset=1)
            fetch_data = await self.request_update_evnspc(
                customer_id, from_date, to_date
            )

        elif evn_area.get("name") == EVN_NAME.NPC:
            from_date, to_date = generate_datetime(monthly_start, offset=1)
            fetch_data = await self.request_update_evnnpc(
                customer_id, from_date, to_date
            )

        elif evn_area.get("name") == EVN_NAME.HCMC:
            from_date, to_date = generate_datetime(monthly_start)
            fetch_data = await self.request_update_evnhcmc(
                customer_id, from_date, to_date
            )

        if fetch_data["status"] == CONF_SUCCESS:
            return formatted_result(fetch_data)

        return fetch_data

    async def login_evnhanoi(self, username, password) -> str:
        """Create EVN login session corresponding with EVNHANOI Endpoint"""

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Connection": "keep-alive",
        }

        payload = {
            "username": username,
            "password": password,
            "client_id": "httplocalhost4500",
            "client_secret": "secret",
            "grant_type": "password",
        }

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"), data=payload, headers=headers
        )

        status, resp_json = await json_processing(resp)
        if status != CONF_SUCCESS:
            return status

        if ("error" in resp_json) and (resp_json["error"] == "invalid_grant"):
            return CONF_ERR_INVALID_AUTH

        elif "access_token" in resp_json:
            self._evn_area["access_token"] = resp_json["access_token"]
            return CONF_SUCCESS

        _LOGGER.error(f"Error while logging in EVN Endpoints: {resp_json}")
        return CONF_ERR_UNKNOWN

    async def login_evnhcmc(self, username, password) -> str:
        """Create EVN login session corresponding with EVNHCMC Endpoint"""

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        payload = {"u": username, "p": password}

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"),
            data=payload,
            ssl=ssl_context,
            headers=headers,
        )

        status, resp_json = await json_processing(resp)
        if status != CONF_SUCCESS:
            return status

        login_state = resp_json["state"]

        if (login_state == CONF_SUCCESS) or (login_state == "login"):
            return CONF_SUCCESS

        _LOGGER.error(f"Unable to login into EVN Endpoint: {resp_json}")
        return CONF_ERR_INVALID_AUTH

    async def login_evnnpc(self, username, password) -> str:
        """Create EVN login session corresponding with EVNNPC Endpoint"""

        payload = {"username": username, "password": password}

        auth_header = base64.b64encode(
            (
                "A21FA5C-34BE-42D7-AE70-8BF03C1EE540:026A64EF-2A91-4973-AA20-6E8A2B66D560"
            ).encode()
        ).decode()

        headers = {
            "User-Agent": "NPCApp/1 CFNetwork/1240.0.4 Darwin/20.6.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Authorization": f"Basic {auth_header}",
        }

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"),
            data=payload,
            headers=headers,
            ssl=ssl_context,
        )

        status, resp_json = await json_processing(resp)
        if status != CONF_SUCCESS:
            return status

        if not (
            "message" in resp_json and resp_json["message"] == "Login successfully."
        ):
            return CONF_ERR_INVALID_AUTH

        self._evn_area["access_token"] = resp_json["access_token"]
        return CONF_SUCCESS

    async def login_evncpc(self, username, password) -> str:
        """Create EVN login session corresponding with EVNCPC Endpoint"""

        payload = {
            "username": username,
            "password": password,
            "scope": "CSKH",
            "grant_type": "password",
        }

        basic_auth = "CSKH_Swagger:1q2w3e*"
        auth_header = base64.b64encode(basic_auth.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"), data=payload, headers=headers
        )

        status, resp_json = await json_processing(resp)
        if status != CONF_SUCCESS:
            return status

        if ("error" in resp_json) and (resp_json["error"] == "invalid_grant"):
            return CONF_ERR_INVALID_AUTH

        elif "access_token" in resp_json:
            self._evn_area["access_token"] = resp_json["access_token"]
            return CONF_SUCCESS

        _LOGGER.error(f"Error while logging in EVN Endpoints: {resp_json}")
        return CONF_ERR_UNKNOWN

    async def login_evnspc(self, username, password) -> str:
        """Create EVN login session corresponding with EVNSPC Endpoint"""

        payload = {
            "strUsername": username,
            "strPassword": password,
            "strDeviceID": str(uuid.uuid4),
        }

        headers = {
            "User-Agent": "evnapp/59 CFNetwork/1240.0.4 Darwin/20.6.0",
            "Accept-Language": "vi-vn",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Content-Type": "application/json; charset=utf-8",
        }

        resp = await self._session.post(
            url=self._evn_area.get("evn_login_url"),
            data=json.dumps(payload),
            headers=headers,
            ssl=False,
        )

        status, resp_json = await json_processing(resp)

        if status != CONF_SUCCESS:
            return status

        if not ("maKH" in resp_json and "token" in resp_json):
            return CONF_ERR_UNKNOWN

        if resp_json["maKH"] == "":
            return CONF_ERR_INVALID_AUTH

        self._evn_area["access_token"] = resp_json["token"]
        return CONF_SUCCESS

    async def request_update_evnhanoi(
        self, customer_id, from_date, to_date, last_index="001"
    ):
        """Request new update from EVNHANOI Server"""

        headers = {
            "Authorization": f"Bearer {self._evn_area.get('access_token')}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
        }

        data = {
            "maDiemDo": f"{customer_id}{last_index}",
            "maDonVi": f"{customer_id[0:6]}",
            "maXacThuc": "EVNHN",
            "ngayDau": from_date,
            "ngayCuoi": to_date,
        }

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_data_url"),
            data=json.dumps(data),
            headers=headers,
            ssl=ssl_context,
        )

        status, resp_json = await json_processing(resp)

        if status != CONF_SUCCESS:
            return resp_json

        if resp_json.get("isError"):

            if resp_json.get("code") == 400:

                if last_index == "001":
                    return await self.request_update_evnhanoi(
                        customer_id, from_date, to_date, "1"
                    )

                return {"status": CONF_ERR_INVALID_ID, "data": resp_json}

            _LOGGER.error(f"Cannot request new data from EVN Server: {resp_json}")

            return {"status": resp_json.get("code"), "data": resp_json}

        sub_data = resp_json["data"]["chiSoNgay"]

        from_date = parser.parse(sub_data[0]["ngay"], dayfirst=True)
        to_date = parser.parse(
            sub_data[(-1 if len(sub_data) > 1 else 0)]["ngay"], dayfirst=True
        ) - timedelta(days=1)
        previous_date = parser.parse(
            sub_data[(-2 if len(sub_data) > 2 else 0)]["ngay"], dayfirst=True
        ) - timedelta(days=1)

        econ_total_new = round(
            float(str(sub_data[(-1 if len(sub_data) > 1 else 0)]["sg"])), 2
        )
        econ_total_old = round(float(str(sub_data[0]["sg"])), 2)

        econ_daily_new = round(
            float(sub_data[(-1 if len(sub_data) > 1 else 0)]["sg"])
            - float(sub_data[(-2 if len(sub_data) > 2 else 0)]["sg"]),
            2,
        )
        econ_daily_old = round(
            float(sub_data[(-2 if len(sub_data) > 2 else 0)]["sg"])
            - float(sub_data[(-3 if len(sub_data) > 3 else 0)]["sg"]),
            2,
        )

        fetched_data = {
            "status": CONF_SUCCESS,
            ID_ECON_TOTAL_OLD: econ_total_old,
            ID_ECON_TOTAL_NEW: econ_total_new,
            ID_ECON_DAILY_OLD: econ_daily_old,
            ID_ECON_DAILY_NEW: econ_daily_new,
            ID_ECON_MONTHLY_NEW: round(econ_total_new - econ_total_old, 2),
            "to_date": to_date.date(),
            "from_date": from_date.date(),
            "previous_date": previous_date.date(),
        }

        data = {
            "maKhachHang": customer_id,
            "maDonViQuanLy": f"{customer_id[0:6]}",
        }

        resp = await self._session.post(
            url=self._evn_area.get("evn_payment_url"),
            data=json.dumps(data),
            headers=headers,
            ssl=ssl_context,
        )
        status, resp_json = await json_processing(resp)

        payment_status = CONF_ERR_UNKNOWN
        m_payment_status = 0

        if status == CONF_SUCCESS and not resp_json["isError"]:
            if len(resp_json["data"]["listThongTinNoKhachHangVm"]):
                payment_status = STATUS_PAYMENT_NEEDED
                m_payment_status = int(
                    resp_json["data"]["listThongTinNoKhachHangVm"][0][
                        "tongTien"
                    ].replace(".", "")
                )
            else:
                payment_status = STATUS_N_PAYMENT_NEEDED

        fetched_data.update(
            {ID_PAYMENT_NEEDED: payment_status, ID_M_PAYMENT_NEEDED: m_payment_status}
        )

        return fetched_data

    async def request_update_evnhcmc(self, customer_id, from_date, to_date):
        """Request new update from EVNHCMC Server"""

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_data_url"),
            data={
                "input_makh": customer_id,
                "input_tungay": from_date,
                "input_denngay": to_date,
            },
            ssl=ssl_context,
            headers=headers,
        )
        status, resp_json = await json_processing(resp)

        if status != CONF_SUCCESS:
            return resp_json

        state = resp_json["state"]

        if state != CONF_SUCCESS:
            if state == "error_login":
                return {"status": CONF_ERR_INVALID_AUTH, "data": resp.status}

            _LOGGER.error(
                f"Cannot request new data from EVN Server for customer ID: {customer_id}\n{resp_json}"
            )
            return {"status": state, "data": resp_json}

        resp_json = resp_json["data"]["sanluong_tungngay"]

        from_date = parser.parse(resp_json[0]["ngayFull"], dayfirst=True)
        to_date = parser.parse(
            resp_json[(-1 if len(resp_json) > 1 else 0)]["ngayFull"], dayfirst=True
        )
        previous_date = parser.parse(
            resp_json[(-2 if len(resp_json) > 2 else 0)]["ngayFull"], dayfirst=True
        )

        econ_total_new = round(
            float(
                str(
                    resp_json[(-1 if len(resp_json) > 1 else 0)]["tong_p_giao"]
                ).replace(",", "")
            ),
            2,
        )
        econ_total_old = round(
            float(str(resp_json[0]["tong_p_giao"]).replace(",", "")), 2
        )

        fetched_data = {
            "status": CONF_SUCCESS,
            ID_ECON_TOTAL_OLD: econ_total_old,
            ID_ECON_TOTAL_NEW: econ_total_new,
            ID_ECON_DAILY_NEW: round(
                float(
                    str(resp_json[(-1 if len(resp_json) > 1 else 0)]["Tong"]).replace(
                        ",", ""
                    )
                ),
                2,
            ),
            ID_ECON_DAILY_OLD: round(
                float(
                    str(resp_json[(-2 if len(resp_json) > 2 else 0)]["Tong"]).replace(
                        ",", ""
                    )
                ),
                2,
            ),
            ID_ECON_MONTHLY_NEW: round(econ_total_new - econ_total_old, 2),
            "to_date": to_date.date(),
            "from_date": from_date.date(),
            "previous_date": previous_date.date(),
        }

        resp = await self._session.post(
            url=self._evn_area.get("evn_payment_url"),
            data={"input_makh": customer_id},
            ssl=ssl_context,
        )
        status, resp_json = await json_processing(resp)

        payment_status = CONF_ERR_UNKNOWN
        m_payment_status = 0

        if status == CONF_SUCCESS:
            if "isNo" in resp_json["data"]:
                if resp_json["data"].get("isNo") == 1:
                    payment_status = STATUS_PAYMENT_NEEDED

                    if "info_no" in resp_json["data"]:
                        m_payment_status = int(
                            resp_json["data"]["info_no"]
                            .get("TONG_TIEN")
                            .replace(".", "")
                        )

                elif resp_json["data"].get("isNo") == 0:
                    payment_status = STATUS_N_PAYMENT_NEEDED

        fetched_data.update(
            {ID_PAYMENT_NEEDED: payment_status, ID_M_PAYMENT_NEEDED: m_payment_status}
        )

        return fetched_data

    async def request_update_evnnpc(
        self, customer_id, from_date, to_date, last_index="001"
    ):
        """Request new update from EVNNPC Server"""

        payload = {
            "ma": f"{customer_id}{last_index}",
            "start_intime": from_date.replace("/", "-"),
            "stop_intime": to_date.replace("/", "-"),
        }

        headers = {
            "User-Agent": "NPCApp/1 CFNetwork/1240.0.4 Darwin/20.6.0",
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "Authorization": f"Bearer {self._evn_area.get('access_token')}",
        }

        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("ALL:@SECLEVEL=1")

        resp = await self._session.post(
            url=self._evn_area.get("evn_data_url"),
            data=json.dumps(payload),
            headers=headers,
            ssl=ssl_context,
        )

        status, resp_json = await json_processing(resp)
        if status != CONF_SUCCESS:
            return resp_json

        valid_info = []

        for each_entity in resp_json:
            if "GHI_CHU" in each_entity and "LOAI_CHI_SO" in each_entity:
                if (
                    each_entity.get("GHI_CHU")
                    == "Sản lượng điện tiêu thụ của khách hàng"
                    and each_entity.get("LOAI_CHI_SO") == "P"
                ):
                    valid_info.append(each_entity)

        if valid_info == []:
            return {
                "status": CONF_ERR_NO_MONITOR,
                "data": str(resp_json[0]),
            }

        from_date = parser.parse(
            valid_info[(-1 if len(valid_info) > 1 else 0)]["THOI_GIAN_BAT_DAU"]
        )
        to_date = parser.parse(valid_info[0]["THOI_GIAN_BAT_DAU"])
        previous_date = parser.parse(
            valid_info[(1 if len(valid_info) > 1 else 0)]["THOI_GIAN_BAT_DAU"]
        )

        fetched_data = {
            "status": CONF_SUCCESS,
            ID_ECON_TOTAL_NEW: round(float(valid_info[0]["CHI_SO_KET_THUC"]), 2),
            ID_ECON_TOTAL_OLD: round(
                float(valid_info[(-1 if len(valid_info) > 1 else 0)]["CHI_SO_BAT_DAU"]),
                2,
            ),
            ID_ECON_DAILY_NEW: round(float(valid_info[0]["SAN_LUONG"]), 2),
            ID_ECON_DAILY_OLD: round(
                float(valid_info[(1 if len(valid_info) > 1 else 0)]["SAN_LUONG"]), 2
            ),
            ID_ECON_MONTHLY_NEW: round(
                float(valid_info[0]["CHI_SO_KET_THUC"])
                - float(
                    valid_info[(-1 if len(valid_info) > 1 else 0)]["CHI_SO_BAT_DAU"]
                ),
                2,
            ),
            "from_date": from_date.date(),
            "to_date": to_date.date(),
            "previous_date": previous_date.date(),
        }

        resp = await self._session.get(
            url=f'{self._evn_area.get("evn_payment_url")}{customer_id}',
            headers=headers,
            ssl=ssl_context,
        )
        status, resp_json = await json_processing(resp)

        payment_status = CONF_ERR_UNKNOWN
        m_payment_status = 0

        if status == CONF_SUCCESS and "data" in resp_json:
            if "customerInfo" in resp_json["data"] and "invoice" in resp_json[
                "data"
            ].get("customerInfo"):
                if len(resp_json["data"]["customerInfo"]["invoice"]):
                    paid_status = resp_json["data"]["customerInfo"]["invoice"][0].get(
                        "paid"
                    )

                    if paid_status:
                        payment_status = STATUS_N_PAYMENT_NEEDED
                    else:
                        payment_status = STATUS_PAYMENT_NEEDED
                        m_payment_status = resp_json["data"]["customerInfo"]["invoice"][
                            0
                        ].get("paymentTotalAmount")

        fetched_data.update(
            {
                ID_PAYMENT_NEEDED: payment_status,
                ID_M_PAYMENT_NEEDED: m_payment_status,
            }
        )

        return fetched_data

    async def request_update_evncpc(self, customer_id):
        """Request new update from EVNCPC Server"""

        headers = {
            "Authorization": f"Bearer {self._evn_area.get('access_token')}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        resp = await self._session.get(
            url=f"{self._evn_area.get('evn_data_url')}{customer_id}",
            headers=headers,
        )

        status, resp_json = await json_processing(resp)

        if status != CONF_SUCCESS:
            return resp_json

        fetched_data = {
            "status": CONF_SUCCESS,
            ID_ECON_DAILY_NEW: round(
                float(resp_json["electricConsumption"]["electricConsumptionToday"]), 2
            ),
            ID_ECON_DAILY_OLD: round(
                float(resp_json["electricConsumption"]["electricConsumptionYesterday"]),
                2,
            ),
            ID_ECON_MONTHLY_NEW: round(
                float(resp_json["electricConsumption"]["electricConsumptionThisMonth"]),
                2,
            ),
        }

        resp = await self._session.get(
            url=f"{self._evn_area.get('evn_payment_url')}{customer_id}",
            headers=headers,
        )

        status, resp_json = await json_processing(resp)

        if status != CONF_SUCCESS:
            return resp_json

        m_payment_status = 0
        payment_status = CONF_ERR_UNKNOWN

        if resp_json["status"] == 0:
            if "tinhTrangThanhToan" in resp_json["response"]:
                if resp_json["response"].get("tinhTrangThanhToan") == "Đã thanh toán":
                    payment_status = STATUS_N_PAYMENT_NEEDED
                else:
                    payment_status = STATUS_PAYMENT_NEEDED

                    if "tienHoaDon" in resp_json["response"]:
                        m_payment_status = int(
                            resp_json["response"]["tienHoaDon"]
                            .replace(".", "")
                            .replace("đ", "")
                        )

        current_einfo = resp_json["response"].get("dienNangHienTai")

        try:
            to_date = datetime.strptime(
                current_einfo.get("thoiDiem"), "%Hh%M - %d/%m/%Y"
            )
        except Exception:
            to_date = datetime.now().date()

        fetched_data.update(
            {
                ID_PAYMENT_NEEDED: payment_status,
                ID_M_PAYMENT_NEEDED: m_payment_status,
                ID_ECON_TOTAL_NEW: round(
                    float(
                        current_einfo.get("chiSo").replace(".", "").replace(",", ".")
                    ),
                    2,
                ),
                ID_ECON_TOTAL_OLD: round(
                    float(
                        resp_json["response"]
                        .get("chiSoCuoiKy")
                        .replace(".", "")
                        .replace(",", ".")
                    ),
                    2,
                ),
                "to_date": to_date,
                "previous_date": to_date - timedelta(days=1),
            }
        )

        return fetched_data

    async def request_update_evnspc(
        self, customer_id, from_date, to_date, last_index="001"
    ):
        """Request new update from EVNSPC Server"""

        headers = {
            "User-Agent": "evnapp/59 CFNetwork/1240.0.4 Darwin/20.6.0",
            "Authorization": f"Bearer {self._evn_area.get('access_token')}",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "vi-vn",
            "Connection": "keep-alive",
        }

        resp = await self._session.get(
            url=self._evn_area.get("evn_data_url"),
            headers=headers,
            params={
                "strMaDiemDo": f"{customer_id}{last_index}",
                "strFromDate": from_date,
                "strToDate": to_date,
            },
            ssl=False,
        )

        status, resp_json = await json_processing(resp)

        if status != CONF_SUCCESS:
            return resp_json

        from_date = parser.parse(resp_json[0]["strTime"], dayfirst=True)
        to_date = parser.parse(
            resp_json[(-1 if len(resp_json) > 1 else 0)]["strTime"], dayfirst=True
        ) - timedelta(days=1)
        previous_date = parser.parse(
            resp_json[(-2 if len(resp_json) > 2 else 0)]["strTime"], dayfirst=True
        ) - timedelta(days=1)

        fetched_data = {
            "status": CONF_SUCCESS,
            ID_ECON_TOTAL_OLD: round(
                float(str(resp_json[0]["dGiaoTong"]).replace(",", "")), 2
            ),
            ID_ECON_TOTAL_NEW: round(
                float(
                    str(
                        resp_json[(-1 if len(resp_json) > 1 else 0)]["dGiaoTong"]
                    ).replace(",", "")
                ),
                2,
            ),
            ID_ECON_DAILY_NEW: round(
                float(
                    str(
                        resp_json[(-1 if len(resp_json) > 1 else 0)]["dSanLuongBT"]
                    ).replace(",", "")
                ),
                2,
            ),
            ID_ECON_DAILY_OLD: round(
                float(
                    str(
                        resp_json[(-2 if len(resp_json) > 2 else 0)]["dSanLuongBT"]
                    ).replace(",", "")
                ),
                2,
            ),
            ID_ECON_MONTHLY_NEW: round(
                float(
                    float(
                        str(
                            resp_json[(-1 if len(resp_json) > 1 else 0)]["dGiaoTong"]
                        ).replace(",", "")
                    )
                    - float(str(resp_json[0]["dGiaoTong"]).replace(",", ""))
                ),
                2,
            ),
            "to_date": to_date.date(),
            "from_date": from_date.date(),
            "previous_date": previous_date.date(),
        }

        resp = await self._session.get(
            url=self._evn_area.get("evn_payment_url"),
            headers=headers,
            params={
                "strMaKH": f"{customer_id}",
            },
            ssl=False,
        )

        status, resp_json = await json_processing(resp)

        if status == CONF_EMPTY:
            payment_status = STATUS_N_PAYMENT_NEEDED
            m_payment_status = 0
        elif status == CONF_SUCCESS:
            payment_status = STATUS_PAYMENT_NEEDED

            if len(resp_json) and "lThanhTien" in resp_json[0]:
                m_payment_status = int(resp_json[0].get("lThanhTien"))
        else:
            payment_status = CONF_ERR_UNKNOWN

        fetched_data.update(
            {ID_PAYMENT_NEEDED: payment_status, ID_M_PAYMENT_NEEDED: m_payment_status}
        )

        return fetched_data


async def json_processing(resp):
    resp_json: dict = {}

    if resp.status != 200:

        if resp.status == 401 or resp.status == 400:
            return CONF_ERR_INVALID_AUTH, {
                "status": CONF_ERR_INVALID_AUTH,
                "data": resp.status,
            }

        if resp.status == 405:
            return CONF_ERR_NOT_SUPPORTED, {
                "status": CONF_ERR_NOT_SUPPORTED,
                "data": resp.status,
            }

        _LOGGER.error(
            f"Cannot connect to EVN Server while requesting new data: status code {resp.status}"
        )
        return CONF_ERR_CANNOT_CONNECT, {
            "status": CONF_ERR_CANNOT_CONNECT,
            "data": resp.status,
        }

    try:
        res = await resp.text()
        resp_json = json.loads(res, strict=False)

        state = CONF_SUCCESS if bool(resp_json) else CONF_EMPTY

    except Exception as error:
        _LOGGER.error(
            f"Unable to fetch data from EVN Server while requesting new data: {error}"
        )
        return CONF_ERR_UNKNOWN, {"status": CONF_ERR_UNKNOWN, "data": error}

    if state != CONF_SUCCESS:
        return state, {"status": state, "data": resp_json}

    return CONF_SUCCESS, resp_json


def formatted_result(raw_data: dict) -> dict:
    res = {}
    time_obj = datetime.now()

    res["status"] = CONF_SUCCESS

    res[ID_ECON_TOTAL_NEW] = {
        "value": raw_data[ID_ECON_TOTAL_NEW],
        "info": raw_data["to_date"],
    }

    res[ID_ECON_TOTAL_OLD] = {
        "value": raw_data[ID_ECON_TOTAL_OLD],
    }

    if raw_data[ID_ECON_MONTHLY_NEW] is not None:
        res[ID_ECON_MONTHLY_NEW] = {
            "value": raw_data[ID_ECON_MONTHLY_NEW],
        }
        res[ID_ECOST_MONTHLY_NEW] = {
            "value": calc_ecost(raw_data[ID_ECON_MONTHLY_NEW]),
        }

    if raw_data[ID_ECON_DAILY_NEW] is not None:
        if raw_data["to_date"] == time_obj.date():
            info = "hôm nay"
        elif raw_data["to_date"] == (time_obj - timedelta(days=1)).date():
            info = "hôm qua"
        else:
            info = f'ngày {raw_data["to_date"].strftime("%d/%m")}'

        res[ID_ECON_DAILY_NEW] = {"value": raw_data[ID_ECON_DAILY_NEW], "info": info}
        res[ID_ECOST_DAILY_NEW] = {
            "value": calc_ecost(raw_data[ID_ECON_DAILY_NEW]),
            "info": info,
        }

    if raw_data[ID_ECON_DAILY_OLD] is not None:
        if raw_data["previous_date"] == (time_obj - timedelta(days=2)).date():
            info = "hôm kia"
        elif raw_data["previous_date"] == (time_obj - timedelta(days=1)).date():
            info = "hôm qua"
        else:
            info = f'ngày {raw_data["previous_date"].strftime("%d/%m")}'

        res[ID_ECON_DAILY_OLD] = {"value": raw_data[ID_ECON_DAILY_OLD], "info": info}
        res[ID_ECOST_DAILY_OLD] = {
            "value": calc_ecost(raw_data[ID_ECON_DAILY_OLD]),
            "info": info,
        }

    res[ID_PAYMENT_NEEDED] = {
        "value": (
            None
            if (
                raw_data[ID_PAYMENT_NEEDED] != STATUS_N_PAYMENT_NEEDED
                and raw_data[ID_PAYMENT_NEEDED] != STATUS_PAYMENT_NEEDED
            )
            else raw_data[ID_PAYMENT_NEEDED]
        ),
        "info": (
            "mdi:comment-alert-outline"
            if raw_data[ID_PAYMENT_NEEDED] == STATUS_PAYMENT_NEEDED
            else (
                "mdi:comment-check-outline"
                if raw_data[ID_PAYMENT_NEEDED] == STATUS_N_PAYMENT_NEEDED
                else "mdi:comment-question-outline"
            )
        ),
    }

    res[ID_M_PAYMENT_NEEDED] = {
        "value": str(raw_data[ID_M_PAYMENT_NEEDED]),
        "info": (
            "mdi:alert-circle-outline"
            if raw_data[ID_M_PAYMENT_NEEDED] > 0
            else "mdi:checkbox-marked-circle-outline"
        ),
    }

    if ID_FROM_DATE in raw_data:
        res[ID_FROM_DATE] = {"value": raw_data.get("from_date").strftime("%d/%m/%Y")}
    else:
        res[ID_FROM_DATE] = {"value": "Không hỗ trợ"}

    res[ID_TO_DATE] = {"value": raw_data.get("to_date").strftime("%d/%m/%Y")}

    res[ID_LATEST_UPDATE] = {"value": time_obj.astimezone()}

    return res


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

                return {
                    "status": CONF_SUCCESS,
                    "customer_id": evn_customer_id,
                    "evn_area": asdict(each_area),
                    "evn_name": each_area.name,
                    "evn_location": each_area.location,
                    "evn_branch": evn_branch,
                }

    return {"status": CONF_ERR_NOT_SUPPORTED}


def generate_datetime(monthly_start=1, offset=0):
    """Generate Datetime as string for requesting data purposes"""

    # Example:

    #   EVNSPC
    #   if offset == 1 means:
    #       When requesting to EVN endpoints for date 10/09/2022,
    #       the e-data returned from server would contain:
    #           - Total e-consumption data on 09/09/2022
    #           - E-monitor value at 23:59 09/09/2022

    #   if offset == 0 means:
    #       When requesting to EVN endpoints for date 10/09/2022,
    #       the e-data returned from server would contain:
    #           - Latest e-consumption data on 10/09/2022
    #           - E-monitor value at 23:59 10/09/2022

    from_date = ""
    time_obj = datetime.now()

    current_day = int(time_obj.strftime("%-d"))
    monthly_start_str = "{:0>2}".format(monthly_start - 1 + offset)

    to_date = (time_obj - timedelta(days=1 - offset)).strftime("%d/%m/%Y")

    # Example: billing start date is 08/09/2022
    #           and current date is 09/09/2022
    if current_day > monthly_start:
        from_date = f"{monthly_start_str}/{time_obj.strftime('%m/%Y')}"

    else:
        last_month = int(time_obj.strftime("%-m")) - 1

        # If current month >= 2
        if last_month:
            last_month_str = "{:0>2}".format(last_month)
            from_date = (
                f"{monthly_start_str}/{last_month_str}/{time_obj.strftime('%Y')}"
            )

        # If current month == 1
        #   last_month must be 12 and change Year to Last Year
        else:
            last_year = int(time_obj.strftime("%Y")) - 1
            from_date = f"{monthly_start_str}/12/{last_year}"

    return from_date, to_date


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
