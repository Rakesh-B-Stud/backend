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

@router.post("/upload_teachers")
async def upload_teachers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    import csv

    # Map CSV headers to model fields
    header_map = {
        "Teacher ID": "teacher_id",
        "Name": "name",
        "Email": "email",
        "Department": "department",
        "Semester Handling": "semester_handling",
        "Section Handling": "section_handling",
        "Subjects Capable": "subjects_capable",
        "Subject Credits": "subject_credits",
        "Max Sessions Per Day": "max_sessions_per_day",
        "Available": "available",
    }

    try:
        contents = await file.read()
        decoded = contents.decode("utf-8-sig").splitlines()  # remove BOM
        reader = csv.DictReader(decoded)
        reader.fieldnames = [header_map.get(h.strip(), h.strip()) for h in reader.fieldnames]

        for row in reader:
            teacher_id = int(row["teacher_id"].strip())
            name = row["name"].strip()
            email = row["email"].strip()
            department = row["department"].strip()
            semester_handling = row["semester_handling"].strip()
            section_handling = row["section_handling"].strip()
            subjects_capable = row["subjects_capable"].strip()
            subject_credits = int(row["subject_credits"].strip())
            max_sessions_per_day = int(row["max_sessions_per_day"].strip())
            available = row["available"].strip().lower() == "true"

            # ✅ Merge: insert new or update existing teacher
            teacher = db.query(Teacher).filter_by(teacher_id=teacher_id).first()
            if teacher:
                teacher.name = name
                teacher.email = email
                teacher.department = department
                teacher.semester_handling = semester_handling
                teacher.section_handling = section_handling
                teacher.subjects_capable = subjects_capable
                teacher.subject_credits = subject_credits
                teacher.max_sessions_per_day = max_sessions_per_day
                teacher.available = available
            else:
                teacher = Teacher(
                    teacher_id=teacher_id,
                    name=name,
                    email=email,
                    department=department,
                    semester_handling=semester_handling,
                    section_handling=section_handling,
                    subjects_capable=subjects_capable,
                    subject_credits=subject_credits,
                    max_sessions_per_day=max_sessions_per_day,
                    available=available
                )
                db.add(teacher)

        db.commit()
        return {"msg": "✅ Teachers uploaded successfully (new + updated)"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


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
