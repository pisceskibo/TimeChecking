# Thư viện cho các hàm chức năng
import models
from passlib.context import CryptContext


## 0. KHỞI TẠO CÁC HÀM CHỨC NĂNG
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Mã hóa mật khẩu
def get_password_hash(password):
    return pwd_context.hash(password)

# Thông tin cua
def get_user(db, username: str):
    return db.query(models.User).filter(models.User.username == username).first()
