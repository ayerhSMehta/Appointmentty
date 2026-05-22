from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random, string, uuid
from .. import models, schemas
from ..database import get_db
from ..config import get_admin_phone, send_otp

router = APIRouter(prefix="/api/auth", tags=["auth"])

OTP_EXPIRY_MINUTES = 10
SESSION_EXPIRY_HOURS = 24
MAX_OTP_ATTEMPTS = 5      # wrong guesses before OTP is invalidated
OTP_RESEND_SECONDS = 60   # minimum gap between OTP requests


def _normalize(phone: str) -> str:
    return phone.replace(" ", "").replace("-", "")


def require_admin(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("X-Admin-Token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = db.query(models.AdminSession).filter(
        models.AdminSession.token == token,
        models.AdminSession.is_active == True,
        models.AdminSession.expires_at > datetime.utcnow(),
    ).first()
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return session


@router.post("/request-otp")
def request_otp(data: schemas.OTPRequest, db: Session = Depends(get_db)):
    try:
        admin_phone = get_admin_phone()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if _normalize(data.phone) != _normalize(admin_phone):
        # Return a generic message to avoid disclosing the admin number
        raise HTTPException(status_code=403, detail="Phone number not authorised")

    # Rate-limit: one OTP per OTP_RESEND_SECONDS
    cutoff = datetime.utcnow() - timedelta(seconds=OTP_RESEND_SECONDS)
    recent = db.query(models.OTPToken).filter(
        models.OTPToken.phone == data.phone,
        models.OTPToken.created_at > cutoff,
        models.OTPToken.used == False,
    ).first()
    if recent:
        wait = int((recent.created_at + timedelta(seconds=OTP_RESEND_SECONDS) - datetime.utcnow()).total_seconds())
        raise HTTPException(status_code=429, detail=f"Please wait {max(wait, 1)}s before requesting another OTP")

    otp = "".join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    record = models.OTPToken(phone=data.phone, otp=otp, expires_at=expires_at)
    db.add(record)
    db.commit()

    send_otp(data.phone, otp)
    return {"detail": f"OTP sent. Valid for {OTP_EXPIRY_MINUTES} minutes."}


@router.post("/verify-otp", response_model=schemas.SessionResponse)
def verify_otp(data: schemas.OTPVerify, db: Session = Depends(get_db)):
    record = db.query(models.OTPToken).filter(
        models.OTPToken.phone == data.phone,
        models.OTPToken.used == False,
        models.OTPToken.expires_at > datetime.utcnow(),
    ).order_by(models.OTPToken.created_at.desc()).first()

    if not record:
        raise HTTPException(status_code=401, detail="No active OTP found. Please request a new one.")

    record.attempts += 1
    if record.attempts >= MAX_OTP_ATTEMPTS:
        record.used = True
        db.commit()
        raise HTTPException(status_code=401, detail="Too many wrong attempts. Please request a new OTP.")

    if record.otp != data.otp:
        db.commit()
        remaining = MAX_OTP_ATTEMPTS - record.attempts
        raise HTTPException(status_code=401, detail=f"Incorrect OTP. {remaining} attempt(s) remaining.")

    record.used = True
    token = str(uuid.uuid4())
    session = models.AdminSession(
        token=token,
        phone=data.phone,
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS),
    )
    db.add(session)
    db.commit()
    return {"token": token, "expires_in": SESSION_EXPIRY_HOURS * 3600}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("X-Admin-Token")
    if token:
        session = db.query(models.AdminSession).filter(
            models.AdminSession.token == token
        ).first()
        if session:
            session.is_active = False
            db.commit()
    return {"detail": "Logged out"}


@router.get("/me")
def me(session=Depends(require_admin)):
    return {"phone": session.phone, "expires_at": session.expires_at}
