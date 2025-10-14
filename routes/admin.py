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
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file")

    contents = await file.read()
    decoded = contents.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)
    count = 0
    for row in reader:
        try:
            teacher = Teacher(
                name=row["name"].strip(),
                email=row["email"].strip(),
                department=row["department"].strip(),
                semester_handling=row["semester_handling"].strip(),
                section_handling=row["section_handling"].strip(),
                subjects_capable=row["subjects_capable"].strip(),
                subject_credits=int(row["subject_credits"].strip()),
                max_sessions_per_day=int(row["max_sessions_per_day"].strip()),
                available=True
            )
            db.merge(teacher)
            count += 1
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Missing column in CSV: {e}")
    db.commit()
    return {"msg": f"✅ {count} teachers uploaded successfully"}

# ------------------- Upload Students CSV -------------------
@router.post("/upload_students")
async def upload_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file")

    contents = await file.read()
    decoded = contents.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)
    count = 0
    for row in reader:
        try:
            student = Student(
                usn=row["usn"].strip(),
                name=row["name"].strip(),
                email=row["email"].strip(),
                department=row["department"].strip(),
                semester=row["semester"].strip(),
                section=row["section"].strip(),
                class_teacher=row.get("class_teacher", "").strip(),
                password=row["password"].strip(),
                is_first_login=True
            )
            db.merge(student)
            count += 1
        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Missing column in CSV: {e}")
    db.commit()
    return {"msg": f"✅ {count} students uploaded successfully"}

# ------------------- Generate Timetable -------------------
@router.post("/generate_timetable")
def generate_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    class_teacher: str = Form(...),
    db: Session = Depends(get_db)
):
    pdf_file = generate_timetable_for_section(db, semester, section, class_teacher)
    if not pdf_file:
        raise HTTPException(status_code=400, detail="Timetable generation failed")
    return {"pdf_file": pdf_file}
