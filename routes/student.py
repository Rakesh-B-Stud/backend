from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Student, Timetable, Notification  # <-- Ensure Notification model exists
from schemas import StudentLogin  # Must include: usn, password fields

router = APIRouter(prefix="/student", tags=["Student"])

# ------------------- DB Session -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------- Student Login -------------------
@router.post("/login")
def student_login(data: StudentLogin, db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(usn=data.usn.strip()).first()

    if not student:
        raise HTTPException(status_code=401, detail="Invalid USN or password")

    if student.password.strip() != data.password.strip():
        raise HTTPException(status_code=401, detail="Invalid USN or password")

    return {
        "success": True,
        "name": student.name,
        "usn": student.usn,
        "section": student.section,
        "semester": student.semester,
        "department": student.department,
        "first_login": student.is_first_login
    }


# ------------------- Change Password -------------------
@router.post("/change_password")
def change_password(usn: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(usn=usn).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.password = new_password.strip()
    student.is_first_login = False
    db.commit()
    return {"success": True, "message": "Password updated successfully"}


# ------------------- Fetch Timetable -------------------
@router.get("/timetable/{semester}/{section}")
def get_timetable(semester: int, section: str, db: Session = Depends(get_db)):
    timetable_entries = db.query(Timetable).filter(
        Timetable.semester == semester,
        Timetable.section == section
    ).all()

    if not timetable_entries:
        raise HTTPException(status_code=404, detail="No timetable found")

    return [{"day": t.day, "slot": t.slot, "subject": t.subject, "teacher": t.teacher_name} for t in timetable_entries]


# ------------------- Fetch Notifications -------------------
@router.get("/notifications/{department}")
def get_notifications(department: str, db: Session = Depends(get_db)):
    """
    Fetch latest notifications for a specific department.
    Example: Announcements from admin like 'Class cancelled', etc.
    """
    notifications = db.query(Notification).filter(
        (Notification.department == department) | (Notification.department == "ALL")
    ).order_by(Notification.created_at.desc()).all()

    return [
        {
            "title": n.title,
            "message": n.message,
            "date": n.created_at.strftime("%Y-%m-%d %H:%M")
        } for n in notifications
    ]
