from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import admin, student, timetable
from database import Base, engine

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
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(student.router, prefix="/api/student", tags=["Student"])
app.include_router(timetable.router, prefix="/api/timetable", tags=["Timetable"])

# Simple home route
@app.get("/")
def home():
    return {"message": "Welcome to SJBIT Timetable Portal API"}
