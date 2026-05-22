import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


def get_admin_phone() -> str:
    phone = os.getenv("ADMIN_PHONE", "").strip()
    if not phone:
        raise ValueError("ADMIN_PHONE is not set in .env")
    return phone


def send_otp(phone: str, otp: str) -> None:
    """Send OTP to phone. Swap this function body to plug in a real SMS provider."""
    print("\n" + "=" * 45)
    print(f"  OTP for {phone}: {otp}")
    print(f"  (logged to console — no SMS sent in dev mode)")
    print("=" * 45 + "\n")

    # ── Twilio (uncomment when ready) ──────────────────
    # from twilio.rest import Client
    # client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    # client.messages.create(
    #     body=f"Your admin OTP is: {otp}. Valid for 10 minutes.",
    #     from_=os.getenv("TWILIO_FROM_NUMBER"),
    #     to=phone,
    # )
