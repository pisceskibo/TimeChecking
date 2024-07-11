# Thư viện Backend Python
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
import models
import jwt
from datetime import datetime
from sqlalchemy import extract
from routers import function


# Khởi chạy nhánh router
router = APIRouter()



# 6. DUYỆT YÊU CẦU (đối với Admin hoặc SuperAdmin)
@router.put("/request/accept_requirement")
async def accept_request(token: str, search_user: str = Form(), id_choice_stt: int = Form(), db: Session = Depends(models.get_db)):
    if token != "":
        try:
            decodeJSON = jwt.decode(token, "secret", algorithms=["HS256"])
            username = decodeJSON["username"]
            user = function.get_user(db, username)

            if user.role == 0:
                return f"{username} không có quyền truy cập trang"
            else:
                user_searching = function.get_user(db, search_user)
                
                if user_searching.manager_by == username:
                    # Hiển thị tất cả các yêu cầu của nhân viên tìm kiếm
                    search_request_user = db.query(models.Requirement).filter(
                            models.Requirement.username == search_user, 
                            models.Requirement.deleted_flag == False,
                            models.Requirement.browser_manager == username).all()

                    if len(search_request_user) < id_choice_stt or id_choice_stt <= 0:
                        return "Chưa chọn yêu cầu cần duyệt"
                    else:
                        
                        this_choice_requirement = search_request_user[id_choice_stt - 1]

                        # Duyệt yêu cầu theo thể loại
                        this_type_choice = this_choice_requirement.type_requirement

                        if this_type_choice == "NP":
                            if user_searching.num_of_day > 0:
                                user_searching.num_of_day -= 1
                                this_choice_requirement.deleted_at = datetime.now()
                                this_choice_requirement.deleted_flag = True

                                # Tạo trên TimeCheck
                                NP_timecheck_user = models.TimeCheck(username=search_user, check_in=this_choice_requirement.time_requirement_start, check_out=this_choice_requirement.time_requirement_end, 
                                                                  total_hours_of_day=0, note="Nghỉ phép")
                                
                                db.add(NP_timecheck_user)
                                db.commit()
                                db.refresh(user_searching)
                                db.refresh(this_choice_requirement)
                                db.refresh(NP_timecheck_user)

                                return f"{username} đã duyệt yêu cầu {this_choice_requirement} của {search_user}"
                            else:
                                return "Không còn ngày để nghỉ phép --> nghỉ không phép"
                        
                        elif this_type_choice == "CCB":
                            # Hiển thị trên TimeCheck
                            CCB_timecheck_user = models.TimeCheck(username=search_user, check_in=this_choice_requirement.time_requirement_start, check_out=this_choice_requirement.time_requirement_end, 
                                                                  total_hours_of_day=0, note="Chấm công bù")
                            
                            this_choice_requirement.deleted_at = datetime.now()
                            this_choice_requirement.deleted_flag = True
                            
                            db.add(CCB_timecheck_user)
                            db.commit()
                            db.refresh(CCB_timecheck_user)
                            db.refresh(this_choice_requirement)

                            return f"{username} đã duyệt yêu cầu {this_choice_requirement} của {search_user}"
                        
                        elif this_type_choice == "XDM":
                            # Hiển thị trên TimeCheck
                            XDM_timecheck_user = models.TimeCheck(username=search_user, check_in=this_choice_requirement.time_requirement_start, check_out=None, 
                                                                  total_hours_of_day=0, note="Làm đơn xin đi muộn")
                            
                            this_choice_requirement.deleted_at = datetime.now()
                            this_choice_requirement.deleted_flag = True

                            db.add(XDM_timecheck_user)
                            db.commit()
                            db.refresh(XDM_timecheck_user)
                            db.refresh(this_choice_requirement)

                            return f"{username} đã duyệt yêu cầu {this_choice_requirement} của {search_user}"
                        
                        elif this_type_choice == "XVS":
                            # Hiển thị trên TimeCheck (với checkin đã phải có)
                            current_time_date = datetime.now().date()
                            search_user_in_day = db.query(models.TimeCheck).filter(models.TimeCheck.username == search_user,
                                                extract('year', models.TimeCheck.check_in) == current_time_date.year,
                                                extract('month', models.TimeCheck.check_in) == current_time_date.month,
                                                extract('day', models.TimeCheck.check_in) == current_time_date.day,
                                                models.TimeCheck.check_in != None).first()
                            
                            if search_user_in_day:
                                search_user_in_day.check_out = this_choice_requirement.time_requirement_end
                                search_user_in_day.note += "Làm đơn xin về sớm"

                                this_choice_requirement.deleted_at = datetime.now()
                                this_choice_requirement.deleted_flag = True

                
                                db.commit()
                                db.refresh(search_user_in_day)
                                db.refresh(this_choice_requirement)

                                return f"{username} đã duyệt yêu cầu {this_choice_requirement} của {search_user}"
                            else:
                                return "Không xin về sớm được (vì chưa đi làm hôm nay)"
                            
                        elif this_type_choice == "XRN":
                            time_difference = this_choice_requirement.time_requirement_end - this_choice_requirement.time_requirement_start
                            timedelta_hours = time_difference.total_seconds() / 3600
                            if timedelta_hours > 2:
                                return "Không được ra ngoài quá 2h mỗi ngày"
                            else:
                                this_choice_requirement.deleted_at = datetime.now()
                                this_choice_requirement.deleted_flag = True

                                db.commit()
                                db.refresh(this_choice_requirement)

                                return f"{username} đã duyệt yêu cầu {this_choice_requirement} của {search_user}"
                            
                        elif this_type_choice == "OT":
                            hour = this_choice_requirement.time_requirement_start.hour
                            
                            if hour < 18 or hour >= 24:
                                return "Không đăng ký OT trong thời gian này"
                            else:            
                                hour_end = this_choice_requirement.time_requirement_end.hour
                                
                                if hour_end > 22:
                                    return "Thời gian kết thúc vượt quá OT"
                                
                                total_time = this_choice_requirement.time_requirement_end - this_choice_requirement.time_requirement_start
                                OT_timecheck_user = models.TimeCheck(username=search_user, check_in=this_choice_requirement.time_requirement_start, check_out=this_choice_requirement.time_requirement_end, 
                                                                  total_hours_of_day=total_time.total_seconds() // 3600, note="Làm đơn xin đi muộn")
                                
                                this_choice_requirement.deleted_at = datetime.now()
                                this_choice_requirement.deleted_flag = True
                                
                                db.add(OT_timecheck_user)
                                db.commit()
                                db.refresh(OT_timecheck_user)
                                db.refresh(this_choice_requirement)

                                return f"{username} đã duyệt yêu cầu {this_choice_requirement} của {search_user}"
                        else:
                            return "Không có yêu cầu cần duyệt"

                else:
                    return "Không có quyền duyệt yêu cầu"

        except:
            return "Đăng nhập bị sai"
    else:
        return "Chưa đăng nhập tài khoản"
    