from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
from datetime import datetime, timedelta


def archive_old_appointments():
    db: Session = SessionLocal()
    try:
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        old = db.query(models.Appointment).filter(
            models.Appointment.date < cutoff
        ).all()

        for appt in old:
            archived = models.ArchivedAppointment(
                original_id=appt.id,
                date=appt.date,
                start_time=appt.start_time,
                end_time=appt.end_time,
                user_name=appt.user_name,
                user_contact=appt.user_contact,
                booking_ref=appt.booking_ref,
                status=appt.status,
                notes=appt.notes,
                created_at=appt.created_at,
            )
            db.add(archived)
            db.delete(appt)

        db.commit()
        print(f"[Scheduler] Archived {len(old)} appointments older than {cutoff}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run daily at midnight
    scheduler.add_job(archive_old_appointments, "cron", hour=0, minute=0)
    scheduler.start()
    return scheduler
