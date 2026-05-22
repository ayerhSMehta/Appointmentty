from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..slot_utils import get_working_hours_for_date, get_slots_for_date
from .auth import require_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

# All routes in this module require a valid admin session
_auth = Depends(require_admin)


@router.get("/settings", response_model=schemas.SettingsResponse)
def get_settings(db: Session = Depends(get_db), _=_auth):
    s = db.query(models.Settings).filter(models.Settings.id == 1).first()
    if not s:
        s = models.Settings(id=1, session_duration=30, provider_name="My Practice")
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.put("/settings", response_model=schemas.SettingsResponse)
def update_settings(data: schemas.SettingsBase, db: Session = Depends(get_db), _=_auth):
    s = db.query(models.Settings).filter(models.Settings.id == 1).first()
    if not s:
        s = models.Settings(id=1)
        db.add(s)
    s.session_duration = data.session_duration
    s.provider_name = data.provider_name
    db.commit()
    db.refresh(s)
    return s


@router.get("/working-hours", response_model=List[schemas.WorkingHoursResponse])
def get_working_hours(db: Session = Depends(get_db), _=_auth):
    days = db.query(models.DefaultWorkingHours).order_by(
        models.DefaultWorkingHours.day_of_week
    ).all()
    existing_days = {d.day_of_week for d in days}
    for dow in range(7):
        if dow not in existing_days:
            entry = models.DefaultWorkingHours(
                day_of_week=dow,
                is_working=(dow < 5),
                start_time="09:00",
                end_time="17:00",
            )
            db.add(entry)
    db.commit()
    return db.query(models.DefaultWorkingHours).order_by(
        models.DefaultWorkingHours.day_of_week
    ).all()


@router.put("/working-hours/apply-all", response_model=List[schemas.WorkingHoursResponse])
def apply_to_all_days(data: schemas.WorkingHoursBase, db: Session = Depends(get_db), _=_auth):
    for dow in range(7):
        entry = db.query(models.DefaultWorkingHours).filter(
            models.DefaultWorkingHours.day_of_week == dow
        ).first()
        if not entry:
            entry = models.DefaultWorkingHours(day_of_week=dow)
            db.add(entry)
        entry.is_working = data.is_working
        entry.start_time = data.start_time
        entry.end_time = data.end_time
        entry.start_time_2 = data.start_time_2
        entry.end_time_2 = data.end_time_2
    db.commit()
    return db.query(models.DefaultWorkingHours).order_by(
        models.DefaultWorkingHours.day_of_week
    ).all()


@router.put("/working-hours/{day_of_week}", response_model=schemas.WorkingHoursResponse)
def update_working_hours(day_of_week: int, data: schemas.WorkingHoursBase, db: Session = Depends(get_db), _=_auth):
    if day_of_week not in range(7):
        raise HTTPException(status_code=400, detail="day_of_week must be 0-6")
    entry = db.query(models.DefaultWorkingHours).filter(
        models.DefaultWorkingHours.day_of_week == day_of_week
    ).first()
    if not entry:
        entry = models.DefaultWorkingHours(day_of_week=day_of_week)
        db.add(entry)
    entry.is_working = data.is_working
    entry.start_time = data.start_time
    entry.end_time = data.end_time
    entry.start_time_2 = data.start_time_2
    entry.end_time_2 = data.end_time_2
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/date-overrides", response_model=List[schemas.DateOverrideResponse])
def get_date_overrides(db: Session = Depends(get_db), _=_auth):
    return db.query(models.DateOverride).order_by(models.DateOverride.date).all()


@router.put("/date-overrides/{date_str}", response_model=schemas.DateOverrideResponse)
def upsert_date_override(date_str: str, data: schemas.DateOverrideBase, db: Session = Depends(get_db), _=_auth):
    entry = db.query(models.DateOverride).filter(
        models.DateOverride.date == date_str
    ).first()
    if not entry:
        entry = models.DateOverride(date=date_str)
        db.add(entry)
    entry.is_working = data.is_working
    entry.start_time = data.start_time
    entry.end_time = data.end_time
    entry.start_time_2 = data.start_time_2
    entry.end_time_2 = data.end_time_2
    entry.note = data.note
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/date-overrides/{date_str}")
def delete_date_override(date_str: str, db: Session = Depends(get_db), _=_auth):
    entry = db.query(models.DateOverride).filter(
        models.DateOverride.date == date_str
    ).first()
    if entry:
        db.delete(entry)
        db.commit()
    return {"detail": "deleted"}


@router.get("/appointments", response_model=List[schemas.AppointmentResponse])
def get_appointments(from_date: str = None, to_date: str = None, db: Session = Depends(get_db), _=_auth):
    q = db.query(models.Appointment).filter(models.Appointment.status == "booked")
    if from_date:
        q = q.filter(models.Appointment.date >= from_date)
    if to_date:
        q = q.filter(models.Appointment.date <= to_date)
    return q.order_by(models.Appointment.date, models.Appointment.start_time).all()


@router.get("/calendar")
def get_calendar_overview(year: int, month: int, db: Session = Depends(get_db), _=_auth):
    start = datetime(year, month, 1)
    end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

    result = []
    current = start
    while current < end:
        date_str = current.strftime("%Y-%m-%d")
        windows, has_override = get_working_hours_for_date(db, date_str)
        slots = get_slots_for_date(db, date_str)
        available = sum(1 for s in slots if s["is_available"])
        result.append({
            "date": date_str,
            "is_working": len(windows) > 0,
            "total_slots": len(slots),
            "available_slots": available,
            "has_override": has_override,
        })
        current += timedelta(days=1)
    return result
