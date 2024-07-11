# THÔNG TIN VỀ BACKEND TIMECHECKING
> Link ý tưởng: https://chamcongd6.atlassian.net/wiki/spaces/SD/pages/262145/Ch+m+c+ng 
+ Ngôn ngữ: Python
+ Database: SQLite
+ Framework: FastAPI
+ Công cụ: Postman, DBeaver
---

### 1. Model User: 
| Column             | Type      | Note                        | Status            |
|--------------------|-----------|-----------------------------|-------------------|
| `username`         | String    | Mã nhân viên                | Primary Key       |
| `fullname`         | String    | Họ và tên đầy đủ            |                   |
| `email`            | String    |                             |                   |
| `password`         | String    | Mật khẩu                    | Mã hóa            |
| `manager_by`       | String    | Quản lý bởi ai              | Dựa theo id       |
| `number_of_day`    | Integer   | Số ngày nghỉ phép còn lại   | Mặc định 20       |
| `role`             | Integer   | Phân quyền                  | 2 - 1 - 0         |
| `check_announcement`| Boolean  | Bật/Tắt thông báo           | True - Bật, False - Tắt |
| `delete_flag`      | Boolean   | Xóa tài khoản               | True - Đã xóa, False - Không xóa |

+ Chức năng: 
    + Đăng ký và Đăng nhập tài khoản
    + Hiển thị danh sách các User
    + Phân quyền Admin (tìm nhân viên muốn phân quyền) → chỉ với role = 2 
    + Manager for Admin or User (tìm nhân viên cho mình) → chỉ với role = 1 và role = 2
    + Avatar Account (edit, delete): sửa fullname và email, xóa tài khoản theo username
    + Thông báo bật/tắt 
+ Token: username, password
---

### 2. Model TimeCheck:
| Column               | Type     | Note                | Status         |
|----------------------|----------|---------------------|----------------|
| `id`                 | Integer  | Số thứ tự           |                |
| `username`           | String   | Mã nhân viên        | Foreign Key    |
| `check_announcement` | Boolean  | Bật/Tắt thông báo   |                |
| `checkin_time`       | Date     | Chấm công lúc đến   |                |
| `checkout_time`      | Date     | Chấm công lúc về    |                |
| `total_hours_of_day` | Integer  | Tổng giờ trong ngày |                |
| `note`               | String   | Ghi chú             |                |

+ Chức năng:
    + Checkin, Checkout: (dạng button)
        + Tìm trong bảng tổng TimeCheck, lấy theo username sao cho cùng ngày - tháng - năm
        + Logic chấm công chia thành các giai đoạn: 8h00 - 12h00, 12h00 - 13h00, 13h00 - 17h00, 17h00 - 23h59 cùng ngày
        + Tổng thời gian làm việc không tính thời gian nghỉ trưa 12h00 - 13h00
    + Lọc lịch sử chấm công của User theo tháng:
        + role = 2 xem được tất cả
        + role = 1 xem được tất cả role = 0 mà nó quản lý và chính nó
        + role = 0 xem được chính nó
    + Danh sách các User không chấm công (checkin, checkout) → role = 2

+ Token: username, password
---

### 3. Thể loại yêu cầu - Type:
| Column       | Type      | Note                     | Status       |
|--------------|-----------|--------------------------|--------------|
| `type_id`    | String    | ID yêu cầu               | Primary Key  |
| `type_name`  | String    | Tên thể loại             |              |
| `inserted_at`| DateTime  | Thời gian thêm thể loại  |              |
| `edited_at`  | DateTime  | Thời gian sửa thể loại   |              |
| `deleted_at` | DateTime  | Thời gian xóa thể loại   |              |
| `deleted_flag`| DateTime  | Xóa thể loại (True/False)|              |

+ Chức năng: Thêm - Sửa - Xóa thể loại yêu cầu (role = 2)
+ Token: username, password
---

### 4. Tạo List các yêu cầu;
| Column                | Type      | Note                         | Status       |
|-----------------------|-----------|------------------------------|--------------|
| `id`                  | Integer   | Số thứ tự                    | Primary Key  |
| `username`            | String    | Tên người yêu cầu (User)     | Foreign Key  |
| `type_requirement`    | String    | Tên yêu cầu (TypeRequest)    | Foreign Key  |
| `inserted_at`         | DateTime  | Thời gian tạo yêu cầu        |              |
| `deleted_at`          | DateTime  | Thời gian xóa yêu cầu        |              |
| `delete_flag`         | Boolean   | Xóa yêu cầu                  |              |
| `note_requirement`    | String    | Thông tin tạo yêu cầu        |              |
| `time_requirement_start` | DateTime  | Thời gian yêu cầu start   |              |
| `time_requirement_end`   | DateTime  | Thời gian yêu cầu end     |              |
| `stt_this_type`       | Integer   | STT cho this_type trong table |              |
| `browser_manager`     | String    | Người quản lý duyệt yêu cầu  |              |

+ Token: username, password
+ Chức năng chính: User Panel + Admin Panel

a) Dành cho User:
+ Tạo yêu cầu: lựa chọn loại yêu cầu và ghi thông tin muốn gửi (thứ tự yêu cầu dựa vào stt_this_type của mỗi loại yêu cầu tương ứng)
+ Xóa yêu cầu: xóa thể loại và choice_stt muốn xóa của loại yêu cầu đó
+ Xem lịch sử yêu cầu:
    + role = 2 xem được tất cả
    + role = 1 xem được role = 0 và chính nó
    + role = 0 xem được chính mình
+ Lọc yêu cầu theo loại (kết nối tới xem lịch sử)

b) Dành cho Admin: (duyệt yêu cầu theo từng thể loại)
+ role = 0 không có quyền duyệt yêu cầu
+ role = 1 và role = 2 sẽ có quyền duyệt yêu cầu của các nhân viên mình quản lý (nếu có nhân viên mình đang yêu cầu):
    + Nếu type = NP thì kiểm tra xem còn số ngày phép không, nếu hết ngày phép thì sẽ bị tính là nghỉ không phép hôm đó
    + Nếu type = CCB thì sửa lại và thêm dữ liệu vào bảng TimeCheck cho nhân viên đó
    + Nếu type = XDM thì cho phép tạo trước dữ liệu trong bàng TimeCheck (chấm công trước) cho nhân viên đó
    + Nếu type = XVS (ngày XVS = ngày Checkin) thì sẽ chấp thuận đơn xin về sớm của nhân viên đó (checkout sớm)
    + Nếu type = XRN thì cần kiểm tra xem thời gian ra ngoài có nhiều hơn 2 tiếng không, nếu nhiều hơn thì yêu cầu không được chấp nhận và ngược lại
    + Nếu type = OT thì yêu cầu thời gian OT thuộc khoảng [18, 22] là thỏa mãn
