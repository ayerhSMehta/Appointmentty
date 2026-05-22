from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..slot_utils import get_slots_for_date, get_working_hours_for_date
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api", tags=["appointments"])


@router.get("/slots/{date_str}", response_model=List[schemas.SlotInfo])
def get_slots(date_str: str, db: Session = Depends(get_db)):
    slots = get_slots_for_date(db, date_str)
    return slots


@router.get("/calendar")
def get_user_calendar(year: int, month: int, db: Session = Depends(get_db)):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)

    result = []
    current = start
    while current < end:
        date_str = current.strftime("%Y-%m-%d")
        windows, _ = get_working_hours_for_date(db, date_str)
        slots = get_slots_for_date(db, date_str)
        available = sum(1 for s in slots if s["is_available"])

        result.append({
            "date": date_str,
            "is_working": len(windows) > 0,
            "total_slots": len(slots),
            "available_slots": available,
        })
        current += timedelta(days=1)
    return result


@router.post("/appointments", response_model=schemas.AppointmentResponse)
def book_appointment(data: schemas.AppointmentCreate, db: Session = Depends(get_db)):
    # Verify the slot is still available
    existing = db.query(models.Appointment).filter(
        models.Appointment.date == data.date,
        models.Appointment.start_time == data.start_time,
        models.Appointment.status == "booked"
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slot already booked")

    # Verify it's a valid working slot
    slots = get_slots_for_date(db, data.date)
    valid = any(s["start_time"] == data.start_time for s in slots)
    if not valid:
        raise HTTPException(status_code=400, detail="Invalid slot")

    appt = models.Appointment(
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        user_name=data.user_name,
        user_contact=data.user_contact,
        booking_ref=str(uuid.uuid4())[:8].upper(),
        notes=data.notes,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt


@router.delete("/appointments/{booking_ref}")
def cancel_appointment(booking_ref: str, db: Session = Depends(get_db)):
    appt = db.query(models.Appointment).filter(
        models.Appointment.booking_ref == booking_ref,
        models.Appointment.status == "booked"
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Booking not found")
    appt.status = "cancelled"
    db.commit()
    return {"detail": "Booking cancelled", "booking_ref": booking_ref}


@router.get("/appointments/{booking_ref}", response_model=schemas.AppointmentResponse)
def get_appointment(booking_ref: str, db: Session = Depends(get_db)):
    appt = db.query(models.Appointment).filter(
        models.Appointment.booking_ref == booking_ref
    ).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Booking not found")
    return appt


@router.get("/settings/public")
def get_public_settings(db: Session = Depends(get_db)):
    s = db.query(models.Settings).filter(models.Settings.id == 1).first()
    if not s:
        return {"session_duration": 30, "provider_name": "My Practice"}
    return {"session_duration": s.session_duration, "provider_name": s.provider_name}
