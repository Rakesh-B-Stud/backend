from datetime import datetime
from collections import defaultdict
import random
from models import Teacher, Student, Timetable
from crud import get_teachers_by_subject, get_teacher_availability, create_timetable_entry, get_students_by_semester_section
from fpdf import FPDF
import os

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SLOTS = ["8:30-9:30", "9:30-10:30", "10:30-10:45", "10:45-11:45", "11:45-12:45", 
         "12:45-1:30", "1:30-2:30", "2:30-3:30", "3:30-4:30"]

MAX_SLOTS_PER_TEACHER_PER_DAY = 4
PDF_FOLDER = "pdfs"

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def send_notification(message, recipients):
    # Placeholder for email notifications
    print(f"[Notification] To: {recipients} => {message}")

def generate_timetable_for_section(db, semester: int, section: str, class_teacher_name: str):
    """
    Generates timetable, saves in DB, and returns PDF file name
    """
    students = get_students_by_semester_section(db, semester, section)
    if not students:
        return None

    # Find class teacher
    class_teacher = db.query(Teacher).filter(Teacher.name == class_teacher_name).first()
    if not class_teacher:
        raise Exception(f"Class Teacher '{class_teacher_name}' not found")

    # Get subjects
    subjects = set()
    for student in students:
        for teacher in db.query(Teacher).filter(Teacher.semester_handling == semester).all():
            for subj in teacher.subjects_capable.split(","):
                subjects.add(subj.strip())
    subjects = list(subjects)

    timetable = []
    teacher_slot_count = defaultdict(lambda: defaultdict(int))  # teacher_id -> day -> count

    for day in DAYS:
        for slot in SLOTS:
            if "Break" in slot or "Lunch" in slot:
                continue

            # First slot: assign class teacher
            if slot == "8:30-9:30":
                entry = create_timetable_entry(db, day, slot, semester, section, class_teacher.id, "Class Teacher")
                timetable.append(entry)
                teacher_slot_count[class_teacher.id][day] += 1
                continue

            for subj in subjects:
                teachers = get_teachers_by_subject(db, subj)
                random.shuffle(teachers)

                assigned = False
                for teacher in teachers:
                    availability = get_teacher_availability(db, teacher.id, day, slot)
                    if availability and teacher_slot_count[teacher.id][day] < MAX_SLOTS_PER_TEACHER_PER_DAY:
                        if not any(t.slot == slot and t.day == day and t.section == section and t.teacher_id == teacher.id for t in timetable):
                            entry = create_timetable_entry(db, day, slot, semester, section, teacher.id, subj)
                            timetable.append(entry)
                            teacher_slot_count[teacher.id][day] += 1
                            assigned = True
                            break

                if not assigned:
                    all_teachers = db.query(Teacher).all()
                    random.shuffle(all_teachers)
                    for teacher in all_teachers:
                        availability = get_teacher_availability(db, teacher.id, day, slot)
                        if availability and teacher_slot_count[teacher.id][day] < MAX_SLOTS_PER_TEACHER_PER_DAY:
                            entry = create_timetable_entry(db, day, slot, semester, section, teacher.id, subj)
                            timetable.append(entry)
                            teacher_slot_count[teacher.id][day] += 1
                            send_notification(f"{teacher.name} substituted for {subj} on {day} {slot}",
                                              [s.email for s in students])
                            assigned = True
                            break

                if not assigned:
                    send_notification(f"Class for {subj} in semester {semester} section {section} at {day} {slot} cancelled",
                                      [s.email for s in students])

    db.commit()

    # ------------------- Create PDF -------------------
    pdf_file_name = f"timetable_sem{semester}_{section}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf_path = os.path.join(PDF_FOLDER, pdf_file_name)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Semester {semester} - Section {section} Timetable", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 12)

    for day in DAYS:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, day, ln=True)
        pdf.set_font("Arial", "", 12)
        for slot in SLOTS:
            if "Break" in slot or "Lunch" in slot:
                pdf.cell(0, 6, slot, ln=True)
                continue
            entries = [t for t in timetable if t.day == day and t.slot == slot and t.section == section]
            for e in entries:
                teacher = db.query(Teacher).filter_by(teacher_id=e.teacher_id).first()
                teacher_name = teacher.name if teacher else "N/A"
                pdf.cell(0, 6, f"{slot}: {e.subject} ({teacher_name})", ln=True)
        pdf.ln(2)

    pdf.output(pdf_path)
    return pdf_file_name
