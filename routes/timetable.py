# routes/timetable.py
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Timetable, Teacher
from utils.timetable_generator import generate_timetable_for_section
import os

router = APIRouter(prefix="/timetable", tags=["Timetable"])

PDF_FOLDER = "pdfs"
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

# ------------------- DB Session -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- Generate Timetable -------------------
@router.post("/generate")
def generate_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    class_teacher: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        pdf_file = generate_timetable_for_section(db, semester, section, class_teacher)
        if not pdf_file:
            raise HTTPException(status_code=400, detail="Timetable generation failed")
        return {"success": True, "pdf_file": pdf_file, "message": "Timetable generated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ------------------- Get Timetable Entries -------------------
@router.get("/get/{semester}/{section}")
def get_timetable(semester: int, section: str, db: Session = Depends(get_db)):
    records = db.query(Timetable).filter_by(semester=semester, section=section).all()
    if not records:
        raise HTTPException(status_code=404, detail="No timetable found")
    return [
        {
            "day": t.day,
            "slot": t.slot,
            "subject": t.subject,
            "teacher": db.query(Teacher).filter_by(teacher_id=t.teacher_id).first().name
            if t.teacher_id else "N/A"
        }
        for t in records
    ]

# ------------------- Publish Timetable -------------------
@router.post("/publish")
def publish_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    db: Session = Depends(get_db)
):
    records = db.query(Timetable).filter_by(semester=semester, section=section).all()
    if not records:
        raise HTTPException(status_code=404, detail="No timetable found to publish")

    for r in records:
        r.is_published = True
    db.commit()
    return {"success": True, "message": f"Timetable published for Semester {semester}, Section {section}"}
