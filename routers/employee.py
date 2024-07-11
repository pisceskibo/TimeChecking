# Thư viện Backend
from fastapi import APIRouter, Form, Depends
from sqlalchemy.orm import Session
import models
import jwt
from routers import function


# Khởi chạy nhánh router
router = APIRouter()



## 1. ĐĂNG KÝ VÀ ĐĂNG NHẬP
# Tạo tài khoản cho User
@router.post("/create_account")
async def create_account(username: str = Form(), fullname: str = Form(), email: str = Form(), password: str = Form(), db: Session = Depends(models.get_db)):
    # Kiểm tra có trùng username không?
    user = function.get_user(db, username)

    if user:
        # Username đã tồn tại
        return f"{username} đã tồn tại, yêu cầu chọn Username khác!"
    else:
        passwordHash = function.get_password_hash(password)
        new_user = models.User(username=username, fullname=fullname, email=email, password=passwordHash, 
                               manager_by=None, num_of_day=20, role=0, check_announcement=True, delete_flag=False)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user


# Chức năng login để lấy token
@router.get("/login")
async def login_account(username: str = Form(), password: str = Form(), db: Session = Depends(models.get_db)):
    user = function.get_user(db, username)
    passwordCheck = function.verify_password(password, user.password)

    # Nếu đăng nhập thành công
    if user and passwordCheck:
        encoded_jwt = jwt.encode({"username": username, 
                                  "password": passwordCheck}, "secret", algorithm="HS256")
        return encoded_jwt
    else:
        return ""


# Hiển thị tất cả các nhân viên
@router.get("/users")
async def show_all_users(db: Session = Depends(models.get_db)):
    all_users = db.query(models.User).filter(models.User.delete_flag == False).all()
    return all_users


# Đổi người quản lý cho user (chỉ user.role != 0 mới thêm được nhân viên của mình)
@router.put("/users/choiced_manager")
async def choiced_manager(token: str, new_employee: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        # Decode
        decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
        username = decodeJSON["username"]
        user = function.get_user(db, username)

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
@router.put("/users/account")
async def edit_account(token: str, edit_name: str = Form(), edit_email: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            # Decode
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

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
@router.delete("/users/delete_account")
async def delete_account(token: str, username_again: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            # Decode
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

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
@router.put("/users/announcement")
async def get_announcement(token: str, get_announce: bool = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            # Decode
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]

            user = function.get_user(db, username)
            user.check_announcement = get_announce

            db.commit()
            db.refresh(user)

            return f"Thay đổi thông báo cho {username} thành công"    
        except:
            return "Đăng nhập chưa đúng"

    else:
        return "Chưa đăng nhập tài khoản"



## 2. CHỨC NĂNG PHÂN QUYỀN
# Thêm admin quản lý (chỉ user.role == 2 mới thêm được quyền)
@router.put('/users/set_admin')
async def update_role(token: str, finded_username: str = Form(), new_role: int = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        # Decode
        decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
        username = decodeJSON["username"]
        user = function.get_user(db, username)

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
