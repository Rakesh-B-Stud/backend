from sqlalchemy.orm import Session
from models import Admin, Student, Teacher, Availability, Timetable, Notification

# -------------------- Admin --------------------
def get_admin_by_email(db: Session, email: str):
    return db.query(Admin).filter(Admin.email == email).first()

# -------------------- Students --------------------
def create_student(db: Session, name, usn, email, semester, section):
    student = Student(name=name, usn=usn, email=email, semester=semester, section=section)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

def get_students_by_semester_section(db: Session, semester: int, section: str):
    return db.query(Student).filter(Student.semester == semester, Student.section == section).all()

# -------------------- Teachers --------------------
def create_teacher(db: Session, name, email, subject):
    teacher = Teacher(name=name, email=email, subject=subject)
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher

def get_teacher_by_id(db: Session, teacher_id: int):
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()

def get_teachers_by_subject(db: Session, subject: str):
    return db.query(Teacher).filter(Teacher.subject == subject).all()

# -------------------- Availability --------------------
def set_availability(db: Session, teacher_id, day, slot, available: bool):
    avail = db.query(Availability).filter(
        Availability.teacher_id == teacher_id,
        Availability.day == day,
        Availability.slot == slot
    ).first()
    if avail:
        avail.available = available
    else:
        avail = Availability(teacher_id=teacher_id, day=day, slot=slot, available=available)
        db.add(avail)
    db.commit()
    return avail

def get_teacher_availability(db: Session, teacher_id, day, slot):
    avail = db.query(Availability).filter(
        Availability.teacher_id == teacher_id,
        Availability.day == day,
        Availability.slot == slot,
        Availability.available == True
    ).first()
    return True if avail else False

# -------------------- Timetable --------------------
def create_timetable_entry(db: Session, day, slot, semester, section, teacher_id, subject):
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

def get_timetable(db: Session, semester: int, section: str):
    return db.query(Timetable).filter(Timetable.semester == semester, Timetable.section == section).all()

# -------------------- Notifications --------------------
def create_notification(db: Session, student_id: int, message: str):
    notif = Notification(student_id=student_id, message=message)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
