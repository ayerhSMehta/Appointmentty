from sqlalchemy import Column, Integer, String, Boolean, Date, Time, DateTime, Text
from sqlalchemy.sql import func
from .database import Base
import uuid


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    session_duration = Column(Integer, default=30)  # minutes
    provider_name = Column(String, default="My Practice")


class DefaultWorkingHours(Base):
    __tablename__ = "default_working_hours"

    id = Column(Integer, primary_key=True)
    day_of_week = Column(Integer, unique=True)  # 0=Mon, 6=Sun
    is_working = Column(Boolean, default=True)
    start_time = Column(String, default="09:00")   # HH:MM morning window
    end_time = Column(String, default="17:00")     # HH:MM morning window
    start_time_2 = Column(String, nullable=True)   # HH:MM evening window
    end_time_2 = Column(String, nullable=True)     # HH:MM evening window


class DateOverride(Base):
    __tablename__ = "date_overrides"

    id = Column(Integer, primary_key=True)
    date = Column(String, unique=True)  # YYYY-MM-DD
    is_working = Column(Boolean, default=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    start_time_2 = Column(String, nullable=True)
    end_time_2 = Column(String, nullable=True)
    note = Column(String, nullable=True)


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    date = Column(String, index=True)         # YYYY-MM-DD
    start_time = Column(String)               # HH:MM
    end_time = Column(String)                 # HH:MM
    user_name = Column(String)
    user_contact = Column(String, nullable=True)
    booking_ref = Column(String, unique=True, default=lambda: str(uuid.uuid4())[:8].upper())
    status = Column(String, default="booked")  # booked | cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class OTPToken(Base):
    __tablename__ = "otp_tokens"

    id = Column(Integer, primary_key=True)
    phone = Column(String, index=True)
    otp = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, index=True)
    phone = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)


class ArchivedAppointment(Base):
    __tablename__ = "archived_appointments"

    id = Column(Integer, primary_key=True)
    original_id = Column(Integer)
    date = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    user_name = Column(String)
    user_contact = Column(String, nullable=True)
    booking_ref = Column(String)
    status = Column(String)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime)
    archived_at = Column(DateTime, server_default=func.now())
