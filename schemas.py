from pydantic import BaseModel

class AdminLogin(BaseModel):
    username: str
    password: str

class StudentLogin(BaseModel):
    usn: str
    password: str

class TeacherBase(BaseModel):
    name: str
    email: str
    subject: str
    availability: bool

class TimetableEntry(BaseModel):
    semester: int
    section: str
    day: str
    slot: str
    subject: str
    teacher_name: str
