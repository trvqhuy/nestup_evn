[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

# Vietnam EVN Data Fetcher for HomeAssistant

English | [Tiếng Việt](https://github.com/trvqhuy/ha-evn/blob/main/README_vn.md)

This component uses the simple yet powerful **HTTP(S)** protocol to periodically fetch the latest e-consumption data from [EVN Endpoint](https://www.evn.com.vn) into [Home Assistant](https://www.home-assistant.io) using **requests** module, and currently supports few regions in Vietnam (see the supported areas below). Hence, it supports HA Web UI, and you can easily integrate monitoring devices into HA without configuring yaml.

## Before Installation
### Supported Areas:
Starting from the v1.0.0 version, the component has added support for the areas listed below:
> Note: There are some EVN Branches (with corresponding areas) that **do not** need authentication/EVN credential to get the e-data from EVN Servers.

| EVN Branch | Vietnam Area | EVN Account Required |
|:---:|:---:|:---:|
| EVNHCMC | Ho Chi Minh City | ☑️ |
| EVNSPC | Southern Vietnam |   |

## Installation
#### Method 1: Installation via [HACS](https://hacs.xyz)
- First installation
    > HACS > Integrations > ➕ Explore & download repositories  > `EVN Data Fetcher` > Download this repository
- Update component
    > HACS > Integrations > `EVN Data Fetcher ` > Update / Redownload

#### Method 2: Manual installation via Samba / SFTP
> Download and copy `custom_components/ha_evn` folder to `custom_components` folder in your HomeAssistant config folder
