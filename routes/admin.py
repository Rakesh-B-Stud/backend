from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.timetable_generator import generate_timetable_for_section
from pydantic import BaseModel
from models import Admin  # ✅ import Admin model

router = APIRouter(tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------ Default Admin (Backup) ------------------
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123"  # default fallback
}

class AdminLogin(BaseModel):
    username: str
    password: str


# ------------------ Login Route ------------------
@router.post("/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    # 1️⃣ Try database admin
    db_admin = db.query(Admin).filter_by(username=data.username, password=data.password).first()
    if db_admin:
        return {"success": True, "message": "Login successful", "name": db_admin.username}

    # 2️⃣ Fallback to default admin
    if data.username == DEFAULT_ADMIN["username"] and data.password == DEFAULT_ADMIN["password"]:
        return {"success": True, "message": "Login successful", "name": "Default Admin"}

    # 3️⃣ If both fail → invalid credentials
    raise HTTPException(status_code=401, detail="Invalid username or password")


# ------------------ Generate Timetable ------------------
@router.post("/generate_timetable")
def generate_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    db: Session = Depends(get_db)
):
    pdf_file = generate_timetable_for_section(db, semester, section)
    return {"pdf_file": pdf_file}
