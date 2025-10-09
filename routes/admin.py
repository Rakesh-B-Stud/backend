from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.timetable_generator import generate_timetable_for_section  # ✅ matches renamed function

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/generate_timetable")
def generate_timetable(semester: int = Form(...), section: str = Form(...), db: Session = Depends(get_db)):
    pdf_file = generate_timetable_for_section(db, semester, section)
    return {"pdf_file": pdf_file}
