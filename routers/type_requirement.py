# Thư viện Backend Python
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
import models
import jwt
from datetime import datetime
from routers import function


# Khởi chạy nhánh router
router = APIRouter()



## 4. THỂ LOẠI CÁC YÊU CẦU
# Tạo thể loại yêu cầu (role = 2)
@router.post("/types/type_add")
async def create_type(token: str, id_type: str = Form(), name_type: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

            # Kiểm tra thể loại này đã tạo chưa
            this_type = db.query(models.TypeRequest).filter(models.TypeRequest.deleted_flag == False, models.TypeRequest.type_id == id_type).all()

            
            if len(this_type) == 1:
                return f"Thể loại {id_type} đã được tạo trước đó"
            else:
                if user.role == 2:
                    insert_at = datetime.now()
                    new_type = models.TypeRequest(type_id=id_type, type_name=name_type, inserted_at=insert_at, edited_at = None, deleted_at=None, deleted_flag=False)
            
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
@router.put("/types/type_edit")
async def edit_type(token: str, id_type: str = Form(), name_type: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

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
@router.delete("/types/type_delete")
async def delete_type(token: str, id_type: str = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

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
