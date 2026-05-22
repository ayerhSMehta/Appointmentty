from datetime import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session
from . import models


def time_to_minutes(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


def minutes_to_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


def get_working_hours_for_date(db: Session, date_str: str):
    """Returns (windows: list of (start, end) tuples, has_override: bool).
    windows is empty if the day is off."""
    override = db.query(models.DateOverride).filter(
        models.DateOverride.date == date_str
    ).first()
    if override:
        if not override.is_working:
            return [], True
        windows = [(override.start_time, override.end_time)]
        if override.start_time_2 and override.end_time_2:
            windows.append((override.start_time_2, override.end_time_2))
        return windows, True

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dow = dt.weekday()
    default = db.query(models.DefaultWorkingHours).filter(
        models.DefaultWorkingHours.day_of_week == dow
    ).first()
    if not default or not default.is_working:
        return [], False
    windows = [(default.start_time, default.end_time)]
    if default.start_time_2 and default.end_time_2:
        windows.append((default.start_time_2, default.end_time_2))
    return windows, False


def generate_slots(start_time: str, end_time: str, duration_minutes: int) -> List[dict]:
    slots = []
    current = time_to_minutes(start_time)
    end = time_to_minutes(end_time)
    while current + duration_minutes <= end:
        slots.append({
            "start_time": minutes_to_time(current),
            "end_time": minutes_to_time(current + duration_minutes),
        })
        current += duration_minutes
    return slots


def get_slots_for_date(db: Session, date_str: str):
    settings = db.query(models.Settings).filter(models.Settings.id == 1).first()
    duration = settings.session_duration if settings else 30

    windows, _ = get_working_hours_for_date(db, date_str)
    if not windows:
        return []

    all_slots = []
    for start_time, end_time in windows:
        all_slots.extend(generate_slots(start_time, end_time, duration))

    booked = db.query(models.Appointment).filter(
        models.Appointment.date == date_str,
        models.Appointment.status == "booked"
    ).all()
    booked_times = {a.start_time: a for a in booked}

    return [
        {
            "start_time": slot["start_time"],
            "end_time": slot["end_time"],
            "is_available": slot["start_time"] not in booked_times,
            "booking_ref": booked_times[slot["start_time"]].booking_ref if slot["start_time"] in booked_times else None,
            "user_name": booked_times[slot["start_time"]].user_name if slot["start_time"] in booked_times else None,
        }
        for slot in all_slots
    ]
