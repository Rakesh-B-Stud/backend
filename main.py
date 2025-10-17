# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine
from models import Admin
from routes import admin, student, timetable

# -------------------- Initialize app --------------------
app = FastAPI(title="SJBIT Timetable Portal API")

# -------------------- CORS --------------------
origins = [
    "http://localhost:3000",
    "https://timetablefrontend-one.vercel.app",
    "https://timetablefrontend-ooy3srak6-rakesh-bs-projects-efb49d55.vercel.app",
    "https://timetablefrontend-7uom3iksq-rakesh-bs-projects-efb49d55.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Create Tables --------------------
Base.metadata.create_all(bind=engine)

# -------------------- Include Routes --------------------
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(student.router)
app.include_router(timetable.router)

# -------------------- Root route --------------------
@app.get("/")
def home():
    return {"message": "Welcome to SJBIT Timetable Portal API"}

# -------------------- Default Admin --------------------
def create_default_admin():
    db = Session(bind=engine)
    existing = db.query(Admin).filter_by(username="rakesh.b.r8b@gmail.com").first()
    if not existing:
        default_admin = Admin(username="rakesh.b.r8b@gmail.com", password="admin123")
        db.add(default_admin)
        db.commit()
        print("✅ Default admin created")
    db.close()

create_default_admin()

# -------------------- Run server --------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
