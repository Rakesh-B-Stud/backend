from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from utils.timetable_generator import generate_timetable_for_section

router = APIRouter(prefix="/timetable", tags=["Timetable"])

@router.post("/generate")
def generate_timetable_api(semester: int, section: str, db: Session = Depends(get_db)):
    """
    Generates timetable for a given semester and section
    """
    try:
        timetable = generate_timetable_for_section(db, semester, section)
        return {"msg": "Timetable generated successfully!", 
                "data": [t.__dict__ for t in timetable]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
