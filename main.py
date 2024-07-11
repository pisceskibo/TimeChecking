# Thư viện Backend Python
from fastapi import FastAPI
from routers import employee, timecheck, type_requirement, requirement, approval_requirement

# Cài đặt setting cho program
app = FastAPI()

app.include_router(employee.router)
app.include_router(timecheck.router)
app.include_router(type_requirement.router)
app.include_router(requirement.router)
app.include_router(approval_requirement.router)
