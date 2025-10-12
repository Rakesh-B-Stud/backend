from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# -------------------- Admin --------------------
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

# -------------------- Students --------------------
# models.py (Student)

class Student(Base):
    __tablename__ = "students"
    usn = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    department = Column(String)
    semester = Column(String)
    section = Column(String)
    class_teacher = Column(String)
    password = Column(String)
    is_first_login = Column(Boolean, default=True)   # <--- new


# -------------------- Teachers --------------------
class Teacher(Base):
    __tablename__ = "teachers"
    teacher_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    department = Column(String)
    semester_handling = Column(String)
    section_handling = Column(String)
    subjects_capable = Column(String)
    subject_credits = Column(Integer)
    max_sessions_per_day = Column(Integer)
    available = Column(Boolean, default=True)

# -------------------- Availability --------------------
class Availability(Base):
    __tablename__ = "availability"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    day = Column(String)
    slot = Column(String)
    available = Column(Boolean, default=True)

    teacher = relationship("Teacher", back_populates="availability")

# -------------------- Timetable --------------------
class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, index=True)
    semester = Column(Integer)
    section = Column(String)
    day = Column(String)
    slot = Column(String)
    subject = Column(String)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    teacher = relationship("Teacher")

# -------------------- Notifications --------------------
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    message = Column(String)
from pydantic import BaseModel

class StudentLogin(BaseModel):
    usn: str
    password: str


# ---------- Semester Model ----------
class Semester(Base):
    __tablename__ = "semesters"
    id = Column(Integer, primary_key=True, index=True)
    semester_number = Column(Integer, unique=True, nullable=False)
    department = Column(String, nullable=False)

    sections = relationship("Section", back_populates="semester")

# ---------- Section Model ----------
class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True, index=True)
    section_name = Column(String, nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"))
    class_teacher = Column(String, nullable=True)

    semester = relationship("Semester", back_populates="sections")
