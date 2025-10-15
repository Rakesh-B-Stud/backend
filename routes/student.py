from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Student, Timetable
from schemas import StudentLogin  # Make sure schemas.py has this Pydantic model

router = APIRouter(prefix="/student", tags=["Student"])

# ------------------- DB Session -------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- Fetch Timetable -------------------
@router.get("/timetable/{semester}/{section}")
def get_timetable(semester: int, section: str, db: Session = Depends(get_db)):
    timetables = db.query(Timetable).filter(
        Timetable.semester == semester,
        Timetable.section == section
    ).all()
    return timetables

# ------------------- Student Login -------------------
@router.post("/login")
def student_login(data: StudentLogin, db: Session = Depends(get_db)):
    try:
        student = db.query(Student).filter_by(usn=data.usn.strip()).first()
        if not student:
            raise HTTPException(status_code=401, detail="Invalid USN or password")

        if student.password != data.password.strip():
            raise HTTPException(status_code=401, detail="Invalid USN or password")

        return {
            "success": True,
            "name": student.name,
            "usn": student.usn,
            "section": student.section,
            "department": student.department,
            "first_login": student.is_first_login
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# ------------------- Change Password -------------------
@router.post("/change_password")
def change_password(usn: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    student = db.query(Student).filter_by(usn=usn).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.password = new_password
    student.is_first_login = False
    db.commit()
    return {"success": True, "message": "Password updated successfully"}
