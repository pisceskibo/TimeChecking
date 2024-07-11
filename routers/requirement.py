# Thư viện Backend Python
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
import models
import jwt
from datetime import datetime, timedelta
from routers import function


# Khởi chạy nhánh router
router = APIRouter()



## 5. DANH SÁCH CÁC YÊU CẦU
"""
hh:mm:ss - dd/mm/yyyy
"""
# Tạo yêu cầu
@router.post("/users/create_request")
async def create_request(token: str, type_request: str = Form(), time_request_start: str = Form(), time_request_end: str = Form(), note: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

            # Kiểm tra xem có thể loại yêu cầu này không
            type_requested = db.query(models.TypeRequest).filter(models.TypeRequest.type_id == type_request, models.TypeRequest.deleted_flag == False).first()
            
            if type_requested:
                insert_at = datetime.now()

                # Lọc số lượng loại yêu cầu này
                search_type = db.query(models.Requirement).filter(
                    models.Requirement.username == username, 
                    models.Requirement.type_requirement == type_request,
                    models.Requirement.deleted_flag == False).all()

                if len(search_type) != 0:
                    get_stt = search_type[-1].stt_this_type
                else:
                    get_stt = 0

                # Tìm người quản lý tương ứng
                this_manager = user.manager_by

                try:
                    # Định dạng chuỗi
                    format_str = "%H:%M:%S - %d/%m/%Y"

                    # Logic tách chuỗi thành datetime
                    time_request_start = time_request_start.strip()     # Xóa khoảng trắng dư thừa 2 phía
                    datetime_obj_start = datetime.strptime(time_request_start, format_str)

                    # Logic tách chuỗi thành datetime
                    time_request_end = time_request_end.strip()     # Xóa khoảng trắng dư thừa 2 phía
                    datetime_obj_end = datetime.strptime(time_request_end, format_str)
                    
                    time_difference = datetime_obj_end - datetime_obj_start
                    
                    if time_difference < timedelta(0):
                        return "Thời gian bắt đầu lớn hơn thời gian kết thúc"
                    else:
                        new_request = models.Requirement(username=username, type_requirement=type_request, 
                                                    inserted_at=insert_at, deleted_at=None, deleted_flag=False, note_requirement=note,
                                                    time_requirement_start=datetime_obj_start, time_requirement_end=datetime_obj_end,
                                                    stt_this_type=get_stt+1, browser_manager=this_manager)
                        
                        db.add(new_request)
                        db.commit()
                        db.refresh(new_request)

                        return f"{username} đã tạo thành công yêu cầu {new_request.type_requirement}"
                    
                except:
                    return "Định dạng thời gian yêu cầu không hợp lệ"

            else:
                return "Không có loại yêu cầu này"
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"


# Xóa yêu cầu
@router.delete("/users/delete_request")
async def delete_request(token: str, type_request: str = Form(), choice_stt: int = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]

            # Kiểm tra xem có thể loại yêu cầu này không
            type_requested = db.query(models.TypeRequest).filter(models.TypeRequest.type_id == type_request, models.TypeRequest.deleted_flag == False).all()
            if type_requested:
                this_all_request_for_type = db.query(models.Requirement).filter(models.Requirement.type_requirement == type_request, models.Requirement.deleted_flag == False,
                                                                                models.Requirement.username == username).all()

                try:
                    this_request = this_all_request_for_type[choice_stt-1]

                    this_request.deleted_at = datetime.now()
                    this_request.deleted_flag = True

                    db.commit()
                    db.refresh(this_request)

                    return f"{username} đã xóa yêu cầu {this_request.type_requirement}"
                except:
                    return "Không có yêu cầu mà bạn chọn"
            else:
                return f"{username} chưa tạo yêu cầu loại này"
        
        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"
    

# Xem lịch sử yêu cầu
@router.get("/request")
async def show_all_request(token: str, search_user: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

            if user.role == 0:
                if search_user == username:
                    search_request_user = db.query(models.Requirement).filter(models.Requirement.username == username, models.Requirement.deleted_flag == False).all()
                    return search_request_user
                else:
                    return f"Không có quyền xem lịch sử của {search_user}"
            
            # Chuyển sang mục duyệt yêu cầu
            elif user.role == 1:
                if search_user == username:
                    search_request_user = db.query(models.Requirement).filter(models.Requirement.username == username, models.Requirement.deleted_flag == False).all()
                    return search_request_user    
                else:
                    user_searching = function.get_user(db, search_user)

                    if user_searching.role != 0:
                        return f"Không có quyền xem lịch sử yêu cầu của {search_user}"
                    else:
                        search_request_user = db.query(models.Requirement).outerjoin(models.User).filter(
                            models.Requirement.username == search_user, 
                            models.Requirement.deleted_flag == False,
                            models.User.manager_by == username).all()
                        return search_request_user
            else:    
                search_request_user = db.query(models.Requirement).filter(models.Requirement.username == search_user, models.Requirement.deleted_flag == False).all()
                return search_request_user

        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"
