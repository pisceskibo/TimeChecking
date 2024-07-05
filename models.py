# Thư viện xây dựng Models
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from database import Base, engine, SessionLocal
from sqlalchemy.orm import relationship


# Model User
class User(Base):
    __tablename__ = 'users'
    username = Column(String(10), primary_key=True, index=True, comment="Mã nhân viên")
    fullname = Column(String(50), index=True, comment="Họ và tên đầy đủ")
    email = Column(String(50), index=True, comment="Email")
    password = Column(String(100), index=True, comment="Mật khẩu")
    manager_by = Column(String(10), index=True, comment="Quản lý bởi ai")
    num_of_day = Column(Integer, index=True, comment="Số ngày nghỉ phép còn lại")
    role = Column(Integer, index=True)
    check_announcement = Column(Boolean, index=True, comment="Bật thông báo")       # True: Bật, False: Tắt
    delete_flag = Column(Boolean, index=True)                   # False: chưa xóa, True: đã xóa

    # Relationship to TimeCheck and Requirement
    timechecks = relationship("TimeCheck", back_populates="user")
    requirements = relationship("Requirement", back_populates="user")


# Model TimeCheck
class TimeCheck(Base):
    __tablename__ = 'timecheck'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  
    username = Column(String(10), ForeignKey('users.username'), index=True, comment="Mã nhân viên")
    check_in = Column(DateTime, index=True, comment="Chấm công lúc đến")
    check_out = Column(DateTime, index=True, comment="Chấm công lúc về")
    total_hours_of_day = Column(Integer, index=True, comment="Tổng số giờ trong ngày")
    note = Column(String(100), index=True, comment="Ghi chú")

    # Relationship to User
    user = relationship("User", back_populates="timechecks")


# Model Requirement
class Requirement(Base):
    __tablename__ = 'requirements'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(10), ForeignKey('users.username'), index=True, comment="Mã nhân viên")
    type_requirement = Column(String(10), ForeignKey('types.type_id'), index=True, comment="Loại yêu cầu")
    inserted_at = Column(DateTime, index=True)
    deleted_at = Column(DateTime, index=True)
    deleted_flag = Column(Boolean, index=True, comment="Xóa yêu cầu")

    # Relationship to user
    user = relationship("User", back_populates="requirements")
    type = relationship("TypeRequest", back_populates="requirements")


# Model TypeRequest
class TypeRequest(Base):
    __tablename__ = 'types'
    type_id = Column(String(10), primary_key=True, index=True, comment="ID Type")
    type_name = Column(String(50), index=True, comment='Tên loại yêu cầu')
    inserted_at = Column(DateTime, index=True)
    edited_at = Column(DateTime, index=True)
    deleted_at = Column(DateTime, index=True)
    deleted_flag = Column(Boolean, index=True, comment="Xóa thể loại yêu cầu")

    # Relationship to Requirement
    requirements = relationship("Requirement", back_populates="type")

    def __str__(self):
        return f"{self.type_id} - {self.type_name}"


Base.metadata.create_all(bind=engine)

# Kết nối tới cơ sở dữ liệu
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
