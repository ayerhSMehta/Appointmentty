from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SettingsBase(BaseModel):
    session_duration: int
    provider_name: str


class SettingsResponse(SettingsBase):
    id: int

    class Config:
        from_attributes = True


class WorkingHoursBase(BaseModel):
    day_of_week: int
    is_working: bool
    start_time: str
    end_time: str
    start_time_2: Optional[str] = None
    end_time_2: Optional[str] = None


class WorkingHoursResponse(WorkingHoursBase):
    id: int

    class Config:
        from_attributes = True


class DateOverrideBase(BaseModel):
    date: str
    is_working: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    start_time_2: Optional[str] = None
    end_time_2: Optional[str] = None
    note: Optional[str] = None


class DateOverrideResponse(DateOverrideBase):
    id: int

    class Config:
        from_attributes = True


class SlotInfo(BaseModel):
    start_time: str
    end_time: str
    is_available: bool
    booking_ref: Optional[str] = None
    user_name: Optional[str] = None


class AppointmentCreate(BaseModel):
    date: str
    start_time: str
    end_time: str
    user_name: str
    user_contact: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: int
    date: str
    start_time: str
    end_time: str
    user_name: str
    user_contact: Optional[str] = None
    booking_ref: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OTPRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: str


class SessionResponse(BaseModel):
    token: str
    expires_in: int  # seconds


class CalendarDay(BaseModel):
    date: str
    is_working: bool
    total_slots: int
    available_slots: int
    has_override: bool
