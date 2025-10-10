from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.timetable_generator import generate_timetable_for_section
from pydantic import BaseModel
from models import Admin

router = APIRouter(tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AdminLogin(BaseModel):
    username: str
    password: str

@router.post("/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter_by(username=data.username).first()
    if not admin or admin.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"success": True, "name": admin.username, "message": "Login successful"}

@router.post("/generate_timetable")
def generate_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    db: Session = Depends(get_db)
):
    pdf_file = generate_timetable_for_section(db, semester, section)
    return {"pdf_file": pdf_file}
