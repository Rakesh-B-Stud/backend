from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from utils.timetable_generator import generate_timetable_for_section
from pydantic import BaseModel
from models import Admin, Teacher, Student, Availability, Semester, Section
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
        decoded = contents.decode("utf-8-sig").splitlines()
        reader = csv.DictReader(decoded)
        reader.fieldnames = [header_map.get(h.strip(), h.strip()) for h in reader.fieldnames]

        teachers_added = 0
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

            teacher = db.query(Teacher).filter_by(teacher_id=teacher_id).first()
            if teacher:
                # Update
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
                # Insert
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
                    available=available,
                )
                db.add(teacher)
                teachers_added += 1
                db.flush()  # get teacher.id

                # ✅ Create default availability (5 days × 5 slots)
                days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
                slots = ["1", "2", "3", "4", "5"]
                for d in days:
                    for s in slots:
                        avail = Availability(
                            teacher_id=teacher.teacher_id,
                            day=d,
                            slot=s,
                            available=True
                        )
                        db.add(avail)

        db.commit()
        return {"msg": f"✅ {teachers_added} teachers uploaded/updated successfully with availability"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


# ------------------- Upload Students CSV -------------------
@router.post("/upload_students")
async def upload_students(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid CSV file")

    contents = await file.read()
    decoded = contents.decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)

    students_added = 0
    semester_section_pairs = set()

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
            students_added += 1

            # Track unique semester-section
            semester_section_pairs.add((
                int(row["semester"].strip()),
                row["department"].strip(),
                row["section"].strip(),
                row.get("class_teacher", "").strip()
            ))

        except KeyError as e:
            raise HTTPException(status_code=400, detail=f"Missing column in CSV: {e}")

    # ✅ Populate Semesters and Sections
    for semester_number, department, section_name, class_teacher in semester_section_pairs:
        semester_obj = (
            db.query(Semester)
            .filter_by(semester_number=semester_number, department=department)
            .first()
        )
        if not semester_obj:
            semester_obj = Semester(
                semester_number=semester_number,
                department=department
            )
            db.add(semester_obj)
            db.flush()

        # Add Section if missing
        section_obj = (
            db.query(Section)
            .filter_by(section_name=section_name, semester_id=semester_obj.id)
            .first()
        )
        if not section_obj:
            section_obj = Section(
                section_name=section_name,
                semester_id=semester_obj.id,
                class_teacher=class_teacher
            )
            db.add(section_obj)

    db.commit()
    return {"msg": f"✅ {students_added} students uploaded successfully with semesters & sections created"}


# ------------------- Get Teachers -------------------
@router.get("/get_teachers")
def get_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).all()
    return teachers


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
