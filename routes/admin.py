from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.timetable_generator import generate_timetable_for_section
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------ Default Admin Login ------------------
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123"  # change this later
}

class AdminLogin(BaseModel):
    username: str
    password: str

@router.post("/login")
def admin_login(data: AdminLogin):
    if data.username == DEFAULT_ADMIN["username"] and data.password == DEFAULT_ADMIN["password"]:
        return {"message": "Login successful"}
    else:
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
