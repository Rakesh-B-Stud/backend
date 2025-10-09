from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import admin, student, timetable
from database import Base, engine
from models import Admin
from sqlalchemy.orm import Session
#routes updated
# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SJBIT Timetable Portal API")

# Allow frontend access (CORS)
origins = [
    "http://localhost:3000",  # local frontend testing
    "https://timetablefrontend-one.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with prefixes
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(student.router, prefix="/student", tags=["Student"])
app.include_router(timetable.router, prefix="/timetable", tags=["Timetable"])

# Simple home route
@app.get("/")
def home():
    return {"message": "Welcome to SJBIT Timetable Portal API"}

# --- Create a default admin if not present ---
def create_default_admin():
    db = Session(bind=engine)
    existing = db.query(Admin).filter_by(username="admin").first()
    if not existing:
        default_admin = Admin(username="rakesh.b.r8b@gmail.com", password="admin123")
        db.add(default_admin)
        db.commit()
        print("✅ Default admin created: username='admin', password='admin123'")
    db.close()

create_default_admin()