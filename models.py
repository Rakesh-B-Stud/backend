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
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    usn = Column(String, unique=True)
    email = Column(String, unique=True)
    name = Column(String)
    semester = Column(Integer)
    section = Column(String)

# -------------------- Teachers --------------------
class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    subject = Column(String)
    # remove single availability field; use Availability table instead
    availability = relationship("Availability", back_populates="teacher")

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
