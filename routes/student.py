from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import get_students_by_sem_section

router = APIRouter(prefix="/student", tags=["student"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/timetable/{semester}/{section}")
def get_timetable(semester: int, section: str, db: Session = Depends(get_db)):
    # This will query timetable table
    from models import Timetable
    return db.query(Timetable).filter(Timetable.semester==semester, Timetable.section==section).all()
