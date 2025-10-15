from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from database import Base, engine
from models import *

# Drop all tables first (if needed)
# Base.metadata.drop_all(bind=engine)   # Optional: only if you want full reset

# Create tables
Base.metadata.create_all(bind=engine)
print("✅ Tables recreated successfully")


# -------------------- Admin --------------------
class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


# -------------------- Students --------------------
class Student(Base):
    __tablename__ = "students"
    usn = Column(String, primary_key=True)  # matches your CSV USN
    name = Column(String)
    email = Column(String)
    department = Column(String)
    semester = Column(String)
    section = Column(String)
    class_teacher = Column(String)
    password = Column(String)
    is_first_login = Column(Boolean, default=True)

# -------------------- Teachers --------------------
class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)  # NEW PK
    teacher_id = Column(Integer, index=True)            
    name = Column(String)
    email = Column(String)
    department = Column(String)
    semester_handling = Column(String)
    section_handling = Column(String)
    subjects_capable = Column(String)
    subject_credits = Column(Integer)
    max_sessions_per_day = Column(Integer)
    available = Column(Boolean, default=True)

    availability = relationship("Availability", back_populates="teacher", cascade="all, delete-orphan")
    timetable_entries = relationship("Timetable", back_populates="teacher", cascade="all, delete-orphan")



# -------------------- Availability --------------------
class Availability(Base):
    __tablename__ = "availability"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"))
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
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"))

    teacher = relationship("Teacher", back_populates="timetable_entries")


# -------------------- Notifications --------------------
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, ForeignKey("students.usn"))
    message = Column(String)


# -------------------- Pydantic Model --------------------
class StudentLogin(BaseModel):
    usn: str
    password: str


# -------------------- Semester Model --------------------
class Semester(Base):
    __tablename__ = "semesters"
    id = Column(Integer, primary_key=True, index=True)
    semester_number = Column(Integer, unique=True, nullable=False)
    department = Column(String, nullable=False)

    sections = relationship("Section", back_populates="semester", cascade="all, delete-orphan")


# -------------------- Section Model --------------------
class Section(Base):
    __tablename__ = "sections"
    id = Column(Integer, primary_key=True, index=True)
    section_name = Column(String, nullable=False)
    semester_id = Column(Integer, ForeignKey("semesters.id"))
    class_teacher = Column(String, nullable=True)

    semester = relationship("Semester", back_populates="sections")
