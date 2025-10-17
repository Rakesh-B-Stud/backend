from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Admin, Teacher, Student, Availability, Semester, Section, Timetable  # <-- Added Timetable
from utils.timetable_generator import generate_timetable_for_section
from pydantic import BaseModel
import csv

router = APIRouter(prefix="/admin", tags=["Admin"])

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
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8-sig").splitlines()
        reader = csv.DictReader(decoded)

        teachers_added = 0
        for row in reader:
            teacher_id = int(row["teacher_id"].strip())
            teacher = db.query(Teacher).filter_by(teacher_id=teacher_id).first()
            if not teacher:
                teacher = Teacher(
                    teacher_id=teacher_id,
                    name=row["name"].strip(),
                    email=row["email"].strip(),
                    department=row["department"].strip(),
                    semester_handling=row["semester_handling"].strip(),
                    section_handling=row["section_handling"].strip(),
                    subjects_capable=row["subjects_capable"].strip(),
                    subject_credits=int(row["subject_credits"].strip()),
                    max_sessions_per_day=int(row["max_sessions_per_day"].strip()),
                    available=row["available"].strip().lower() == "true"
                )
                db.add(teacher)
                db.flush()
                teachers_added += 1

                # create default availability 5 days × 7 slots × subjects
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                subjects = [s.strip() for s in row["subjects_capable"].split(",")] if row["subjects_capable"] else ["General"]
                for d in days:
                    for s in range(1, 8):
                        for subj in subjects:
                            db.add(Availability(
                                teacher_id=teacher.teacher_id,
                                day=d,
                                slot=str(s),
                                subject=subj,
                                available=True
                            ))
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
    try:
        contents = await file.read()
        decoded = contents.decode("utf-8-sig").splitlines()
        reader = csv.DictReader(decoded)

        students_added = 0
        semester_section_pairs = set()
        for row in reader:
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
            semester_section_pairs.add((int(row["semester"].strip()), row["department"].strip(), row["section"].strip(), row.get("class_teacher", "").strip()))

        # Create Semester & Section records
        for semester_number, department, section_name, class_teacher in semester_section_pairs:
            semester_obj = db.query(Semester).filter_by(semester_number=semester_number, department=department).first()
            if not semester_obj:
                semester_obj = Semester(semester_number=semester_number, department=department)
                db.add(semester_obj)
                db.flush()
            section_obj = db.query(Section).filter_by(section_name=section_name, semester_id=semester_obj.id).first()
            if not section_obj:
                db.add(Section(section_name=section_name, semester_id=semester_obj.id, class_teacher=class_teacher))

        db.commit()
        return {"msg": f"✅ {students_added} students uploaded successfully with semesters & sections created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

# ------------------- Get Teachers -------------------
@router.get("/get_teachers")
def get_teachers(db: Session = Depends(get_db)):
    teachers = db.query(Teacher).all()
    return [
        {
            "teacher_id": t.teacher_id,
            "name": t.name,
            "subjects_capable": [s.strip() for s in t.subjects_capable.split(",")] if t.subjects_capable else []
        } for t in teachers
    ]

# ------------------- Get Availability -------------------
@router.get("/get_availability/{teacher_id}")
def get_availability(teacher_id: int, db: Session = Depends(get_db)):
    records = db.query(Availability).filter_by(teacher_id=teacher_id).all()
    if not records:
        return []
    return [{"day": r.day, "slot": r.slot, "subject": r.subject, "available": r.available} for r in records]

# ------------------- Update Availability -------------------
@router.post("/update_availability")
def update_availability(
    teacher_id: int = Form(...),
    subject: str = Form(...),
    day: str = Form(...),
    slot: str = Form(...),
    available: str = Form(...),
    db: Session = Depends(get_db)
):
    available_bool = available.lower() == "true"
    record = db.query(Availability).filter_by(teacher_id=teacher_id, subject=subject, day=day, slot=slot).first()
    if not record:
        record = Availability(teacher_id=teacher_id, subject=subject, day=day, slot=slot, available=available_bool)
        db.add(record)
    else:
        record.available = available_bool
    db.commit()
    return {"success": True, "msg": "Availability updated successfully"}

# ------------------- Generate Timetable -------------------
@router.post("/generate_timetable")
def generate_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    class_teacher: str = Form(...),
    db: Session = Depends(get_db)
):
    # Generate timetable objects
    timetable_entries = generate_timetable_for_section(db, semester, section, class_teacher)

    if not timetable_entries:
        raise HTTPException(status_code=400, detail="Timetable generation failed")

    # Save draft in DB (is_published=False)
    for t in timetable_entries:
        t.is_published = False
        db.merge(t)
    db.commit()

    # Return JSON for preview
    return {
        "timetable": [
            {
                "day": t.day,
                "slot": t.slot,
                "subject": t.subject,
                "teacher": t.teacher.name if t.teacher else "N/A"
            } for t in timetable_entries
        ]
    }

# ------------------- Publish Timetable -------------------
@router.post("/publish_timetable")
def publish_timetable(
    semester: int = Form(...),
    section: str = Form(...),
    db: Session = Depends(get_db)
):
    records = db.query(Timetable).filter(
        Timetable.semester == semester,
        Timetable.section == section
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="No timetable found to publish")

    for r in records:
        r.is_published = True
    db.commit()

    return {"success": True, "msg": f"Timetable published for Semester {semester}, Section {section}"}
