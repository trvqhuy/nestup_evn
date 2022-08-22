[![hacs][hacsbadge]][hacs]
[![Code Style][blackbadge]][black]
[![Project Maintenance][maintenance-shield]][maintenance]

# Vietnam EVN Data Fetcher for HA

English | [Tiếng Việt](https://github.com/trvqhuy/ha-evn/blob/main/README_vn.md)

This component uses the simple yet powerful **HTTP(S)** protocol to periodically fetch the latest e-consumption data from [EVN Endpoint](https://www.evn.com.vn) into [Home Assistant](https://www.home-assistant.io) with **AIOHTTP** module (and the **BeautifulSoup** brilliant assist for scaping useful data). 

Hence, it supports installation through UI, and can easily integrate monitoring devices into HA without configuring yaml.

## Before Installation
There are some EVN branches that require authentication to fetch the daily electric consumption data, but orthers do not need this field.

A qualified EVN account will consist of:

1. A username (usually your **EVN Customer ID** or **Phone Number**).

2. A password.

**Note**: Check the table below, if your area needed EVN Account to setup the component, please contact the corresponding support center link to get the required credentials.

Starting from the v1.1.0 version, the component has successfully provided support for the areas listed below:

| EVN Branch | Vietnam Area | Component Supported  | EVN Account Required | Support Center |
|:---:|:---:|:---:|:---:|:---:|
| EVNHCMC | Ho Chi Minh City | ☑️ | ☑️ | [Link](https://cskh.evnhcmc.vn/lienhe)
| EVNSPC | Southern Vietnam | ☑ |   | [Link](https://cskh.evnspc.vn/LienHe/CacKenhTrucTuyen)
| EVNHANOI | Ha Noi Capital | (not yet) | ? | [Link](https://evnhanoi.vn/infomation/lien-he)
| EVNNPC | Northern Vietnam | (not yet) | ? | [Link](https://cskh.npc.com.vn/Home/LienHeNPC)
| EVNCPC | Central Vietnam | (not yet) | ? | [Link](https://cskh.cpc.vn/lien-he)

> If your area were not yet supported, feel free to [contact me][maintenance], we could make it happen. 
    
## Installation
### Method 1: Installation via [HACS](https://hacs.xyz)
- First installation

    > HACS > Integrations > ➕ Explore & download repositories  > `EVN Data Fetcher` > Download this repository
    
- Update component

    > HACS > Integrations > `EVN Data Fetcher` > Update / Redownload

### Method 2: Manual installation via Samba / SFTP
1. Clone/download the latest release (or the repos. master branch).

2. Unzip/copy the `custom_components/nestup_evn` folder to the `custom_components` directory of your HomeAssistant installation.
    - The `custom_components` directory depends on your HomeAssistant **configuration directory**. 
    - Usually, the **configuration directory** is within your OS Home Directory `~/homeassistant/`.
    - In other words, the **configuration directory** of HomeAssistant is where the `configuration.yaml` file is located.
    - After a correct installation, your configuration directory should look like the following.
    
        ```
        └── ...
        └── configuration.yaml
        └── secrets.yaml
        └── custom_components
            └── nestup_evn
                └── __init__.py
                └── sensor.py
                └── nestup_evn.py
                └── ...
        ```
    **Note**: if the `custom_components` directory does not exist, you need to create it manually.


[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/MAINTAINER-%40TRVQHUY-orange%20?style=for-the-badge
[maintenance]: https://github.com/trvqhuy
[blackbadge]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[black]: https://github.com/ambv/black
