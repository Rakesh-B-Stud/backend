from sqlalchemy.orm import Session
from models import Teacher, Student, Timetable, Availability

def create_timetable_entry(db: Session, day: str, slot: str, semester: int, section: str, teacher_id: int, subject: str):
    """
    Create a single timetable entry and save to DB
    """
    entry = Timetable(
        day=day,
        slot=slot,
        semester=semester,
        section=section,
        teacher_id=teacher_id,
        subject=subject
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_teachers_by_subject(db: Session, subject: str):
    """
    Return list of teachers who can teach the given subject
    """
    teachers = db.query(Teacher).filter(Teacher.subjects_capable.like(f"%{subject}%")).all()
    return teachers

def get_teacher_availability(db: Session, teacher_id: int, day: str, slot: str, subject: str):
    """
    Check if teacher is available for a specific day, slot, and subject
    """
    record = db.query(Availability).filter_by(
        teacher_id=teacher_id,
        day=day,
        slot=slot,
        subject=subject
    ).first()
    if record:
        return record.available
    # Default available if no record exists
    return True

def get_students_by_semester_section(db: Session, semester: int, section: str):
    """
    Fetch all students for a specific semester and section
    """
    return db.query(Student).filter_by(semester=semester, section=section).all()
