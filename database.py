from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# -----------------------------
# PostgreSQL Database URL
# -----------------------------
DATABASE_URL = "postgresql://admin:AKarnph4xIO2P35lXV3wLu1jGIytyAGV@dpg-d3jsat95pdvs73emnbf0-a.oregon-postgres.render.com/sjbit_timetable_db"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
