from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ------------------------------
# PostgreSQL Database URL from Render
# ------------------------------
DATABASE_URL = "postgresql://admin:AKarnph4xIO2P35lXV3wLu1jGIytyAGV@dpg-d3jsat95pdvs73emnbf0-a.oregon-postgres.render.com/sjbit_timetable_db"

# ------------------------------
# Create SQLAlchemy engine
# ------------------------------
engine = create_engine(DATABASE_URL, echo=True)  # echo=True for SQL debug logs

# ------------------------------
# Session maker
# ------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------------------
# Base class for models
# ------------------------------
Base = declarative_base()

# ------------------------------
# Dependency for FastAPI routes
# ------------------------------
def get_db():
    """
    Yield a database session for FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
