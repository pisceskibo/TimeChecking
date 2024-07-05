# Thư viện Backend Python
from fastapi import FastAPI, Depends, Form
from sqlalchemy.orm import Session
import models
from passlib.context import CryptContext
import jwt
from datetime import datetime, time
from sqlalchemy import extract


# Cài đặt setting cho program
app = FastAPI()



## 0. KHỞI TẠO CÁC HÀM CHỨC NĂNG
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

# Mã hóa mật khẩu
def get_password_hash(password):
    return pwd_context.hash(password)



## 1. ĐĂNG KÝ VÀ ĐĂNG NHẬP
# Tạo tài khoản cho User
@app.post("/create_account")
async def create_account(username: str = Form(), fullname: str = Form(), email: str = Form(), password: str = Form(), db: Session = Depends(models.get_db)):
    # Kiểm tra có trùng username không?
    user = get_user(db, username)

    if user:
        # Username đã tồn tại
        return f"{username} đã tồn tại, yêu cầu chọn Username khác!"
    else:
        passwordHash = get_password_hash(password)
        new_user = models.User(username=username, fullname=fullname, email=email, password=passwordHash, manager_by=None, num_of_day=20, role=0, check_announcement=True, delete_flag=False)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user


# Chức năng login để lấy token
@app.get("/login")
async def login_account(username: str = Form(), password: str = Form(), db: Session = Depends(models.get_db)):
    user = get_user(db, username)
    passwordCheck = verify_password(password, user.password)

    # Nếu đăng nhập thành công
    if user and passwordCheck:
        encoded_jwt = jwt.encode({"username": username, 
                                  "password": passwordCheck}, "secret", algorithm="HS256")
        
        return encoded_jwt
    else:
        return ""


# Hiển thị tất cả các nhân viên
@app.get("/users")
async def show_all_users(db: Session = Depends(models.get_db)):
    all_users = db.query(models.User).filter(models.User.delete_flag == False).all()
    return all_users


# Đổi người quản lý cho user (chỉ user.role != 0 mới thêm được nhân viên của mình)
@app.put("/users/choiced_manager")
async def choiced_manager(token: str, new_employee: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        # Decode
        decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
        username = decodeJSON["username"]
        user = get_user(db, username)

        if user.role == 0:
            return f"{username} không có quyền chọn người quản lý"
        else:
            your_employee = db.query(models.User).filter(models.User.username == new_employee, models.User.role == 0, models.User.delete_flag == False).first()
            
            if your_employee:
                your_employee.manager_by = username

                db.commit()
                db.refresh(your_employee)
                return f"Đã đổi người quản lý cho {new_employee} thành công"
            else:
                return f"Không thể tìm thấy nhân viên {username}"
    else:
        return "Chưa đăng nhập tài khoản"


# Chỉnh sửa lại trang cá nhân
@app.put("/users/account")
async def edit_account(token: str, edit_name: str = Form(), edit_email: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            # Decode
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)

            # Update lại thông tin người dùng
            user.fullname = edit_name
            user.email = edit_email

            db.commit()
            db.refresh(user)

            return f"{username} đã cập nhật thông tin thành công"
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"
    

# Chức năng xóa tài khoản
@app.delete("/users/delete_account")
async def delete_account(token: str, username_again: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            # Decode
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)

            # SuperAdmin có thể tìm User cần xóa tài khoản
            if user.role == 2:
                searching_user = db.query(models.User).filter(models.User.username == username_again, models.User == False).first()

                if searching_user:
                    searching_user.delete_flag = True

                    db.commit()
                    db.refresh(searching_user)

                    return f"Đã xóa tài khoản {username_again}"
                else:
                    return "Không tìm thấy tài khoản cần xóa"
            else:
                user.delete_flag = True

                db.commit()
                db.refresh(searching_user)

                return f"Đã xóa tài khoản {username_again}"
        except:
            return "Đăng nhập bị sai"

    else:
        return "Chưa đăng nhập tài khoản"


# Bật/Tắt thông báo
@app.post("/users/announcement")
async def get_announcement(token: str, get_announce: bool = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            # Decode
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]

            user = get_user(db, username)
            user.check_announcement = get_announce

            db.commit()
            db.refresh(user)

            return f"Thay đổi thông báo cho {username} thành công"    
        except:
            return "Đăng nhập chưa đúng"

    else:
        return "Chưa đăng nhập tài khoản"
    


## 2. Chức năng phân quyền
# Thêm admin quản lý (chỉ user.role == 2 mới thêm được quyền)
@app.put('/users/set_admin')
async def update_role(token: str, finded_username: str = Form(), new_role: int = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        # Decode
        decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
        username = decodeJSON["username"]
        user = get_user(db, username)

        if user.role != 2:
            return f"Không có quyền thay đổi Admin cho {finded_username}"
        else:
            user_update = db.query(models.User).filter(models.User.username == finded_username, models.User.delete_flag == False).first()

            if user_update:
                user_update.role = new_role
                user_update.manager_by = username       # Sau khi thay đổi thì người quản lý luôn là user.role=2

                db.commit()
                db.refresh(user_update)
                return f"Thay đổi quyền cho {finded_username} thành công"
            else:
                return f"Không tìm thấy {finded_username} để thay đổi quyền"
    else:
        return "Chưa đăng nhập tài khoản"



## 3. CHECKIN VÀ CHECKOUT
# Chấm công lúc đến
@app.post("/users/checkin")
async def user_checkin(token: str, db: Session = Depends(models.get_db)):
    if token != "":
        # Decode
        decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
        username = decodeJSON["username"]

        # Ngày, tháng, năm hiện tại
        current_time_date = datetime.now().date()

        # Ngày, tháng, năm cần tham chiếu
        search_user_in_day = db.query(models.TimeCheck).filter(models.TimeCheck.username == username,
            extract('year', models.TimeCheck.check_in) == current_time_date.year,
            extract('month', models.TimeCheck.check_in) == current_time_date.month,
            extract('day', models.TimeCheck.check_in) == current_time_date.day).first()

    
        if search_user_in_day == None:
            user_in_that_day = models.TimeCheck(username=username, check_in = None, check_out = None, total_hours_of_day=None, note="")
                
            db.add(user_in_that_day)
            db.commit()
            db.refresh(user_in_that_day)

            search_user_in_day = user_in_that_day
        
        
        # Logic chấm công lúc đến
        if search_user_in_day.check_in == None:
            current_time = datetime.now()

            if time(8, 0) < current_time.time() <= time(12, 0):
                search_user_in_day.check_in = current_time
                late_minutes = (current_time - datetime.combine(current_time.date(), time(8, 0))).total_seconds() / 60
                search_user_in_day.note += f"Sáng đến M: {int(late_minutes)}p"
            elif time(13, 0) < current_time.time() <= time(17, 0):
                search_user_in_day.check_in = current_time
                late_minutes = (current_time - datetime.combine(current_time.date(), time(13, 0))).total_seconds() / 60
                search_user_in_day.note += f"Nghỉ sáng, Chiều đến M: {int(late_minutes)}p"
            elif time(12, 0) < current_time.time() < time(13, 0):
                search_user_in_day.check_in = current_time
                search_user_in_day.note += "Nghỉ sáng"
            elif current_time.time() > time(17, 0):
                return f"{username} không chấm công đi làm hôm nay"
            else:
                search_user_in_day.check_in = current_time
                        
            db.commit()
            db.refresh(search_user_in_day)

            return f"{username} chấm công lúc đến thành công"
        else:
            return f"{username} đã chấm công lúc đến trước đó"

    else:
        return "Chưa đăng nhập tài khoản"


# Chấm công lúc về
@app.put("/users/checkout")
async def user_checkout(token: str, db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            
            # Ngày, tháng, năm hiện tại
            current_time_date = datetime.now().date()
            search_user_in_day = db.query(models.TimeCheck).filter(models.TimeCheck.username == username,
                                extract('year', models.TimeCheck.check_in) == current_time_date.year,
                                extract('month', models.TimeCheck.check_in) == current_time_date.month,
                                extract('day', models.TimeCheck.check_in) == current_time_date.day,
                                models.TimeCheck.check_in != None).first()

            if search_user_in_day:
                if search_user_in_day.check_out == None:
                    current_time = datetime.now()

                    if time(17, 0) <= current_time.time() <= time(23, 59):
                        search_user_in_day.check_out = current_time
                    elif time(8, 0) <= current_time.time() <= time(12, 0):
                        search_user_in_day.check_out = current_time
                        late_minutes = (datetime.combine(current_time.date(), time(12, 0)) - current_time).total_seconds() / 60
                        search_user_in_day.note += f", Sáng về S: {int(late_minutes)}p, Chiều nghỉ"
                    elif time(13, 0) <= current_time.time() <= time(17, 0):
                        search_user_in_day.check_out = current_time
                        late_minutes = (datetime.combine(current_time.date(), time(17, 0)) - current_time).total_seconds() / 60
                        search_user_in_day.note += f", Chiều về S: {int(late_minutes)}p"
                    elif time(12, 0) < current_time.time() < time(13, 0):
                        search_user_in_day.check_out = current_time
                        search_user_in_day.note += f", Chiểu nghỉ"
                    else:
                        return f"{username} không chấm công đi về hôm nay (cần chấm công bù)"
                    

                    # Tính toán tổng số giờ làm việc trên ngày
                    work_duration = current_time - search_user_in_day.check_in
                    total_work_hours = work_duration.total_seconds() // 3600

                    if time(12, 0) >= current_time.time() or search_user_in_day.check_in.time() >= time(13, 0):
                        search_user_in_day.total_hours_of_day = total_work_hours
                    else:
                        search_user_in_day.total_hours_of_day = total_work_hours - 1
                    
                    db.commit()
                    db.refresh(search_user_in_day)

                    return f"{username} chấm công lúc về thành công"
                else:
                    return f"{username} đã chấm công lúc về"
            
            else:
                return f"{username} chưa chấm công lúc đến"
            
        except:
            return "Đăng nhập bị sai"

    else:
        return "Chưa đăng nhập tài khoản"


# Xem lịch sử chấm công theo tháng (dành cho User)
@app.get("/users/all_check_month")
async def get_allcheck_month(token: str, user_search: str = Form(), time_search: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)

            if user.role == 2:
                try:
                    searching = time_search.split("/")
                    year_searching = int(searching[1])
                    month_searching = int(searching[0])

                    all_check_status = db.query(models.TimeCheck).filter(models.TimeCheck.username == user_search,
                            extract('year', models.TimeCheck.check_in) == year_searching,
                            extract('month', models.TimeCheck.check_in) == month_searching).all()
                    return all_check_status
                except:
                    # Lịch sử chấm công từ trước đến giờ
                    all_check_status = db.query(models.TimeCheck).filter(models.TimeCheck.username == user_search).all()
                    return all_check_status
            
            elif user.role == 1:
                try:
                    searching = time_search.split("/")
                    year_searching = int(searching[1])
                    month_searching = int(searching[0])

                    all_check_status = db.query(models.TimeCheck).outerjoin(models.User).filter(
                            models.TimeCheck.username == user_search, models.User.role == 0, models.User.delete_flag == False,
                            extract('year', models.TimeCheck.check_in) == year_searching,
                            extract('month', models.TimeCheck.check_in) == month_searching).all()
                    return all_check_status
                except:
                    # Lịch sử chấm công từ trước đến giờ
                    all_check_status = db.query(models.TimeCheck).filter(models.TimeCheck.username == user_search).all()
                    return all_check_status
            else:
                try:
                    searching = time_search.split("/")
                    year_searching = int(searching[1])
                    month_searching = int(searching[0])

                    user_search = username

                    all_check_status = db.query(models.TimeCheck).filter(models.TimeCheck.username == user_search,
                            extract('year', models.TimeCheck.check_in) == year_searching,
                            extract('month', models.TimeCheck.check_in) == month_searching).all()
                    return all_check_status
                except:
                    # Lịch sử chấm công từ trước đến giờ
                    all_check_status = db.query(models.TimeCheck).filter(models.TimeCheck.username == username).all()
                    return all_check_status
                
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"


# Thông báo cho tất cả các user chưa chấm công cả ngày (dành cho superAdmin)
@app.get("/unchecked_list")
async def get_uncheckin(token: str, see_status: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)

            # Chỉ user.role == 2 sẽ nhận được ai chưa chấm công để gửi thông báo
            if user.role == 2:
                if see_status == "checkin":
                    check_in_time = time(8, 45)  # 08:45 AM
                    users_not_checked_in = db.query(models.User).outerjoin(models.TimeCheck).filter(
                        models.TimeCheck.check_in == None,  # No check-in recorded
                        models.User.username == models.TimeCheck.username).all()
                    return users_not_checked_in
                
                elif see_status == "checkout":
                    check_out_time = time(17, 45)  # 17:45 PM
                    users_not_checked_out = db.query(models.User).outerjoin(models.TimeCheck).filter(
                        models.TimeCheck.check_out == None,  # No check-out recorded
                        models.User.username == models.TimeCheck.username).all()
                    return users_not_checked_out
                
                else:
                    all_users_not_check =  db.query(models.User).outerjoin(models.TimeCheck).filter(
                        models.TimeCheck.check_in == None,  models.TimeCheck.check_out == None,
                        models.User.username == models.TimeCheck.username).all()
                    return all_users_not_check
            else:
                return "Không có quyền truy cập để thông báo tới user"
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"



## 4. THỂ LOẠI CÁC YÊU CẦU
# Tạo thể loại yêu cầu (role = 2)
@app.post("/types/type_add")
async def create_type(token: str, id_type: str = Form(), name_type: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)


            if user.role == 2:
                insert_at = datetime.now()
                new_type = models.TypeRequest(type_id=id_type, type_name=name_type, inserted_at=insert_at, deleted_at=None, deleted_flag=False)
                
                db.add(new_type)
                db.commit()
                db.refresh(new_type)

                return new_type
            else:
                return f"{username} không có quyền thêm thể loại yêu cầu"
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"
    

# Sửa thể loại yêu cầu
@app.put("/types/type_edit")
async def edit_type(token: str, id_type: str = Form(), name_type: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)

            if user.role == 2:
                this_type = db.query(models.TypeRequest).filter(models.TypeRequest.deleted_flag == False, models.TypeRequest.type_id == id_type).first()
                # Thay đổi
                this_type.edited_at = datetime.now()
                this_type.type_name = name_type

                db.commit()
                db.refresh(this_type)

                return f"Đã thay đổi tên thể loại {this_type}"
            else:
                return f"{username} không có quyền sửa thể loại yêu cầu"
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"


# Xóa thể loại yêu cầu
app.delete("/types/type_delete")
async def delete_type(token: str, id_type: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)

            if user.role == 2:
                this_type = db.query(models.TypeRequest).filter(models.TypeRequest.deleted_flag == False, models.TypeRequest.type_id == id_type).first()
                
                # Xóa thể loại
                this_type.deleted_at = datetime.now()
                this_type.deleted_flag = True

                db.commit()
                db.refresh(this_type)

                return f"Đã xóa thể loại yêu cầu {this_type}"
            else:
                return f"{username} không có quyền xóa thể loại sách"
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"



## 5. DANH SÁCH CÁC YÊU CẦU
# Tạo yêu cầu
@app.post("/users/create_request")
async def create_request(token: str, username: str = Form(), type_request: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = get_user(db, username)

            # Logic tạo yêu cầu
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"