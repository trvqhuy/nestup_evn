[![hacs][hacsbadge]][hacs]
[![Code Style][blackbadge]][black]
[![Project Maintenance][maintenance-shield]][maintenance]

# Vietnam EVN Data Fetcher for HA

English | [Tiếng Việt](https://github.com/trvqhuy/ha-evn/blob/main/README_vn.md)

This component uses the simple yet powerful **HTTP(S)** protocol to periodically fetch the latest e-consumption data from [EVN Endpoint](https://www.evn.com.vn) into [Home Assistant](https://www.home-assistant.io) with **Requests** module, and currently supports few regions in Vietnam (see the supported areas below). 

Hence, it supports HA Web UI, and you can easily integrate monitoring devices into HA without configuring yaml.

## Before Installation
Starting from the v1.0.0 version, the component has added support for the areas listed below:
> Note: There are some EVN Branches (with corresponding areas) that **do not** need Authentication / EVN Credential to get the E-data from EVN Servers.

| EVN Branch | Vietnam Area | EVN Account Required |  Account Support |
|:---:|:---:|:---:|:---:|
| EVNHCMC | Ho Chi Minh City | ☑️ | [Link](https://cskh.evnhcmc.vn/lienhe)
| EVNSPC | Southern Vietnam |   | [Link](https://cskh.evnspc.vn/LienHe/CacKenhTrucTuyen)

## Installation
### Method 1: Installation via [HACS](https://hacs.xyz)
- First installation
    > HACS > Integrations > ➕ Explore & download repositories  > `EVN Data Fetcher` > Download this repository
- Update component
    > HACS > Integrations > `EVN Data Fetcher ` > Update / Redownload

### Method 2: Manual installation via Samba / SFTP
> Download and copy `custom_components/nestup_evn` folder to `custom_components` folder in your HomeAssistant config folder

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/MAINTAINER-%40TRVQHUY-orange%20?style=for-the-badge
[maintenance]: https://github.com/trvqhuy
[blackbadge]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[black]: https://github.com/ambv/black
