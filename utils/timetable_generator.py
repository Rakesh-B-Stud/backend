from datetime import datetime
from collections import defaultdict
import random
from models import Teacher, Student, Timetable
from crud import get_teachers_by_subject, get_teacher_availability, create_timetable_entry, get_students_by_semester_section

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
SLOTS = ["8:30-9:30", "9:30-10:30", "10:30-10:45", "10:45-11:45", "11:45-12:45", 
         "12:45-1:30", "1:30-2:30", "2:30-3:30", "3:30-4:30"]

MAX_SLOTS_PER_TEACHER_PER_DAY = 4

def send_notification(message, recipients):
    # Placeholder: implement email notifications
    print(f"[Notification] To: {recipients} => {message}")

def generate_timetable_for_section(db, semester: int, section: str, class_teacher_name: str):
    """
    Generate timetable for given semester, section, and assign the class teacher.
    """
    students = get_students_by_semester_section(db, semester, section)
    if not students:
        return []

    # Find the class teacher object
    class_teacher = db.query(Teacher).filter(Teacher.name == class_teacher_name).first()
    if not class_teacher:
        raise Exception(f"Class Teacher '{class_teacher_name}' not found")

    # Get all subjects in this semester from assigned teachers
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

            # Optional: assign class teacher in first slot of day for homeroom/advisory
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
                        # Assign if not already teaching this section at this slot
                        if not any(t.slot == slot and t.day == day and t.section == section and t.teacher_id == teacher.id for t in timetable):
                            entry = create_timetable_entry(db, day, slot, semester, section, teacher.id, subj)
                            timetable.append(entry)
                            teacher_slot_count[teacher.id][day] += 1
                            assigned = True
                            break

                if not assigned:
                    # Assign any available teacher
                    all_teachers = db.query(Teacher).all()
                    random.shuffle(all_teachers)
                    for teacher in all_teachers:
                        availability = get_teacher_availability(db, teacher.id, day, slot)
                        if availability and teacher_slot_count[teacher.id][day] < MAX_SLOTS_PER_TEACHER_PER_DAY:
                            entry = create_timetable_entry(db, day, slot, semester, section, teacher.id, subj)
                            timetable.append(entry)
                            teacher_slot_count[teacher.id][day] += 1
                            send_notification(
                                f"{teacher.name} substituted for {subj} on {day} {slot}",
                                [s.email for s in students]
                            )
                            assigned = True
                            break

                if not assigned:
                    send_notification(
                        f"Class for {subj} in semester {semester} section {section} at {day} {slot} cancelled",
                        [s.email for s in students]
                    )

    return timetable