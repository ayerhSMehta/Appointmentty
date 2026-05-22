# Appointment Manager

A web-based appointment booking app for trainers and doctors.

## Quick Start

### 1. Start the Backend

```bash
cd appointment-app
bash start_backend.sh
```

The API runs at **http://localhost:8000**  
Interactive API docs: **http://localhost:8000/docs**

### 2. Open the Frontend

Open `frontend/index.html` directly in your browser.  
No build step required — it loads React from CDN.

---

## Two Views

| View | URL | Who uses it |
|------|-----|-------------|
| User Booking | `index.html` (or `index.html#`) | Patients / clients |
| Admin Panel | `index.html#admin` | Doctor / Trainer |

---

## Features

### User (Patient/Client)
- Calendar showing available days with slot counts
- Click a day → see all time slots (green = available, grey = booked)
- One-click booking — just enter your name
- Booking reference shown after confirmation
- "My Bookings" tab — cancel with one click
- Cancel any booking using the booking reference

### Admin (Doctor/Trainer)
- **Settings**: Set provider name + session duration (15/20/30/45/60/90 min) — one time
- **Working Hours**: Set hours per day of week, toggle days on/off, "Apply to All Days" button
- **Date Overrides**: Mark specific dates as off or set custom hours (holidays, special days)
- **Appointments**: View upcoming/all bookings, cancel from admin side

---

## Data

- SQLite database at `backend/appointments.db`
- Appointments older than 30 days are auto-archived daily at midnight
- Archived data stays in `archived_appointments` table (never deleted)
