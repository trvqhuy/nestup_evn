[![hacs][hacsbadge]][hacs]
[![Code Style][blackbadge]][black]
[![Project Maintenance][maintenance-shield]][maintenance]

# Công cụ lấy dữ liệu điện tiêu thụ từ EVN Việt Nam dành cho HomeAssistant

[English](https://github.com/trvqhuy/ha-evn/blob/main/README.md) | Tiếng Việt

Từ việc sử dụng các phương thức có sẵn từ module **Requests** thông qua giao thức **HTTP(S)** cơ bản, công cụ có thể theo dõi dữ liệu điện năng tiêu thụ từ [EVN](https://www.evn.com.vn) trực tiếp trong [Home Assistant](https://www.home-assistant.io), hiện tại đã hỗ trợ cho một số vùng miền cùng với chi nhánh EVN tương ứng tại Việt Nam (xem thêm danh sách phía dưới).

Công cụ hỗ trợ xem trực tiếp UI từ HomeAssistant Website, dễ dàng quản lí các thông số điện tiêu thụ thông qua các thiết bị theo dõi tập trung, và có thể cài đặt bằng UI không cần chỉnh sửa trực tiếp bằng file ‘configuration.yaml’

## Trước khi cài đặt
Bắt đầu từ phiên bản v1.0.0, công cụ đã hỗ trợ cho các vùng miền thuộc Việt Nam cùng với chi nhánh EVN tương ứng ở bảng dưới:
> Ghi chú: Có một số vùng miền **không cần** sử dụng tài khoản EVN để nhận dữ liệu điện năng tiêu thụ từ máy chủ EVN (xem rõ ở bảng dưới)

| Chi nhánh EVN | Khu vực | Cần có tài khoản EVN |
|:---:|:---:|:---:|
| EVNHCMC | TP. Hồ Chí Minh | ☑️ |
| EVNSPC | Các khu vực thuộc miền Nam |   |

## Cách cài đặt
#### Cách 1: Cài đặt thông qua [HACS](https://hacs.xyz)
- Đối với lần cài đặt đầu tiên:
    > HACS > Integrations > ➕ Explore & download repositories  > `EVN Data Fetcher` > Download this repository
- Cách cập nhật công cụ:
    > HACS > Integrations > `EVN Data Fetcher ` > Update / Redownload

#### Cách 2: Cài đặt thủ công thông qua Samba / SFTP / HTTPS
> Tải và sao chép thư mục `custom_components/ha_evn` vào thư mục `custom_components` trong đường dẫn thư mục cài đặt của Home Assistant

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/MAINTAINER-%40TRVQHUY-orange%20?style=for-the-badge
[maintenance]: https://github.com/trvqhuy
[blackbadge]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[black]: https://github.com/ambv/black
