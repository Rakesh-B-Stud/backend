from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.timetable_generator import generate_timetable_for_section
from pydantic import BaseModel
from models import Admin, Teacher, Student
import csv

router = APIRouter(tags=["Admin"])

# ------------------- DB Session -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- Admin Login -------------------
class AdminLogin(BaseModel):
    username: str
    password: str

@router.post("/login")
def admin_login(data: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter_by(username=data.username).first()
    if not admin or admin.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"success": True, "name": admin.username, "message": "Login successful"}

# ------------------- Upload Teachers CSV -------------------
@router.post("/upload_teachers")
async def upload_teachers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    decoded = contents.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)
    for row in reader:
        teacher = Teacher(
            teacher_id=int(row["teacher_id"]),
            name=row["name"],
            email=row["email"],
            department=row["department"],
            semester_handling=row["semester_handling"],
            section_handling=row["section_handling"],
            subjects_capable=row["subjects_capable"],
            subject_credits=int(row["subject_credits"]),
            max_sessions_per_day=int(row["max_sessions_per_day"]),
            available=row["available"].lower() == "true"
        )
        db.merge(teacher)  # merge will insert or update
    db.commit()
    return {"msg": "Teachers uploaded successfully"}

# ------------------- Upload Students CSV -------------------
@router.post("/upload_students")
async def upload_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    decoded = contents.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)
    for row in reader:
        student = Student(
            usn=row["usn"],
            name=row["name"],
            email=row["email"],
            department=row["department"],
            semester=int(row["semester"]),
            section=row["section"],
            class_teacher=row["class_teacher"],
            password=row["password"]
        )
        db.merge(student)
    db.commit()
    return {"msg": "Students uploaded successfully"}

# ------------------- Generate Timetable -------------------

@router.post("/generate_timetable")
def generate_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    class_teacher: str = Form(...),  # ✅ Added this
    db: Session = Depends(get_db)
):
    # Pass class_teacher to your timetable generator
    pdf_file = generate_timetable_for_section(db, semester, section, class_teacher)
    if not pdf_file:
        raise HTTPException(status_code=400, detail="Timetable generation failed")
    return {"pdf_file": pdf_file}
