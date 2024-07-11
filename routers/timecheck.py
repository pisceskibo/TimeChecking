# Thư viện Backend Python
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
import models
import jwt
from datetime import datetime, time
from sqlalchemy import extract
from routers import function


# Khởi chạy nhánh router
router = APIRouter()



## 3. CHECKIN VÀ CHECKOUT
# Chấm công lúc đến
@router.post("/users/checkin")
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

        # Kiểm tra đã chấm công lúc đến chưa
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
@router.put("/users/checkout")
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
@router.get("/users/all_check_month")
async def get_allcheck_month(token: str, user_search: str = Form(), time_search: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)
            return user

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

                    if user_search != username:
                        all_check_status = db.query(models.TimeCheck).outerjoin(models.User).filter(
                                models.TimeCheck.username == user_search, 
                                models.User.role == 0, models.User.delete_flag == False, models.User.manager_by == username,
                                extract('year', models.TimeCheck.check_in) == year_searching,
                                extract('month', models.TimeCheck.check_in) == month_searching).all()
                    else:
                        all_check_status = db.query(models.TimeCheck).outerjoin(models.User).filter(
                                models.TimeCheck.username == username,
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

                    if user_search == username:
                        all_check_status = db.query(models.TimeCheck).filter(models.TimeCheck.username == username,
                                extract('year', models.TimeCheck.check_in) == year_searching,
                                extract('month', models.TimeCheck.check_in) == month_searching).all()
                        return all_check_status
                    else:
                        return f"Không có quyền xem các yêu cầu của {user_search}"
                except:
                    # Lịch sử chấm công từ trước đến giờ
                    all_check_status = db.query(models.TimeCheck).filter(models.TimeCheck.username == username).all()
                    return all_check_status
                
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"


# Thông báo cho tất cả các user chưa chấm công cả ngày (dành cho superAdmin)
@router.get("/unchecked_list")
async def get_uncheckin(token: str, see_status: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

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
