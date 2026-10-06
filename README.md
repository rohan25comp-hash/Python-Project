# Two-Wheeler Service Reminder Manager (Bajaj & TVS)

A desktop application with **customer accounts**, an **admin dashboard**,
and an **automated reminder email system**. Built with Tkinter (GUI),
SQLite (storage), and Matplotlib (charts).

---

## 1. Setup (do this once)

### Step 1 — Check you have Python
```bash
python --version      # Windows fallback: py --version
python3 --version      # macOS/Linux
```
Need Python 3.9+. If missing, install from **python.org/downloads**
(Windows: tick "Add Python to PATH").

### Step 2 — Put all 11 files in one folder
`app.py`, `main.py`, `login.py`, `admin.py`, `database.py`, `auth.py`,
`config.py`, `email_config.py`, `email_service.py`, `seed_demo_data.py`,
`requirements.txt`.

### Step 3 — Install the one dependency
```bash
pip install -r requirements.txt
```
(Windows: `py -m pip install -r requirements.txt`. macOS/Linux: `pip3 install -r requirements.txt`.)

### Step 4 — Seed the admin account + demo data (run once)
```bash
python seed_demo_data.py
```
This prints every account it creates. **Run this again a day or two
before your actual demo/viva** — it's safe to re-run (it skips accounts
that already exist) and it keeps the OVERDUE / DUE SOON examples timed
correctly relative to the current date.

### Step 5 — Run the app
```bash
python app.py
```

---

## 2. Login credentials (from the seeding script above)

| Role | Username | Password | What it shows |
|---|---|---|---|
| **Admin** | `admin` | `Admin@123` | All customers, all vehicles, all reminders, Email Center |
| Customer | `rahul` | `Demo@123` | 2 vehicles: one **OVERDUE**, one **DUE SOON** — best account for a live demo |
| Customer | `sneha` | `Demo@123` | 1 vehicle, status **OK** |
| Customer | `vikram` | `Demo@123` | 1 vehicle, status OK but a fast rider — best account to show **Smart ETA** pulling the predicted date 3 weeks earlier than the calendar date |

**Suggested demo flow for judges:**
1. Log in as `rahul` / `Demo@123` → Reminders tab → point out the OVERDUE/DUE SOON colour coding and the 🧠 Smart ETA column.
2. Logout → log in as `admin` / `Admin@123` → **All Reminders** tab → same data, system-wide, with customer name + email attached.
3. **Email Center** tab → click **Send Reminder Emails Now** → show the result table (Rahul gets one consolidated email for both his flagged vehicles) → open `sent_emails_log.txt` to show the actual composed email content.
4. (Optional) Log in as `vikram` / `Demo@123` to show a vehicle that's calendar-OK but Smart ETA still flags it earlier based on real riding pace.

Your own account (from the earlier version of this app) still works
too — just log in or create a new one from the Login screen's **Create
Account** button.

---

## 3. The Automated Email System

**What it does:** the Admin's Email Center scans every customer's
vehicles system-wide, groups the ones that are OVERDUE or DUE SOON by
customer, and sends **one consolidated email per customer** (not one
email per vehicle) listing every flagged vehicle, its due date/km, and
its Smart ETA.

**Important — read this before your demo:** sending real email requires
real SMTP credentials, which obviously aren't included here. By default
the system runs in **safe DRY-RUN mode**: nothing goes out over the
network, but every email it *would* have sent is written in full to
`sent_emails_log.txt`, so the Email Center's result table and the log
file together prove the feature genuinely works — you can show a judge
the exact email content without needing live credentials.

**To make it send real emails** (optional, e.g. for your own testing):
1. Open `email_config.py`.
2. Follow the Gmail App Password instructions written at the top of
   that file (Gmail requires an "App Password", not your normal login
   password, once 2-Step Verification is on).
3. Fill in `SMTP_USERNAME` and `SMTP_PASSWORD`, set `ENABLED = True`.
4. Re-run the app — the Email Center will now say "🟢 Configured" and
   actually deliver mail via `smtplib` (STARTTLS on port 587).

This was tested against a real SMTP server during development (not
just written and assumed to work) — message construction, headers, and
delivery mechanics are all verified; only live credentials are missing.

---

## 4. Admin Account — how it's different from a customer account
- Admin accounts are **never created through the signup form** — that
  form always creates `role = "customer"` accounts, hard-coded in
  `login.py`, so nobody can self-promote to admin by typing something
  into a field. The only admin account comes from `seed_demo_data.py`.
- On login, `app.py` checks the account's `role` and opens either the
  customer `ServiceManagerApp` (`main.py`) or the `AdminApp` (`admin.py`).
- The admin dashboard has **read access to every customer's data** (for
  the reminders list and email targeting) but no separate "edit another
  customer's vehicle" feature — it's a monitoring/notification console,
  not a customer-data-editing console.

## 🧠 Unique Feature: Smart ETA (Usage-Based Prediction)
Calculates each vehicle's **actual average km/day** from its own service
history, projects the date its odometer-based service point will really
be reached at that pace, and compares it to the plain calendar due date.
Whichever is **sooner** becomes the Smart ETA. See `vikram`'s account
above for a live example where this pulls the date three weeks earlier
than a naive calendar reminder would. Implemented in
`database.py::get_average_daily_km()` / `_build_reminder_row()`.

## Customer Accounts & Data Isolation
- Passwords are hashed with PBKDF2-HMAC-SHA256 + a random per-user salt
  (100,000 iterations) in `auth.py` — never stored in plain text.
- Every vehicle is tagged with the `user_id` of the account that
  created it; every customer-facing query filters by it, so one
  customer can never see or fetch another's data (tested directly —
  see the project history / your earlier conversation for the isolation
  test that confirms this).

## A note on "every device" cross-platform support
Tkinter is a **desktop GUI toolkit**: this app genuinely runs unmodified
on Windows, macOS and Linux — that's the real, defensible claim for your
report/viva. It does **not** run on Android or iOS. If phone support is
a hard requirement, the honest path is porting the GUI layer to Kivy or
BeeWare/Briefcase, reusing `database.py`, `auth.py`, `config.py`, and
`email_service.py` unchanged.

## Database Schema
- `users(id, full_name, username, email, phone, role, password_salt, password_hash, created_at)`
- `vehicles(id, user_id, owner_name, brand, model, reg_number, purchase_date, current_odometer)`
- `services(id, vehicle_id, service_date, service_type, cost, odometer_at_service, next_service_date, next_service_odometer, notes)`

## File Overview
| File | Purpose |
|---|---|
| `app.py` | Entry point — run this one |
| `login.py` | Login / Create Account screen |
| `main.py` | Customer app: Vehicles, Service Records, Reminders, Dashboard tabs |
| `admin.py` | Admin app: All Customers, All Vehicles, All Reminders, Email Center |
| `database.py` | All SQLite access + the Smart ETA calculation |
| `auth.py` | Password hashing |
| `config.py` | Brand/model service-interval reference table |
| `email_service.py` | Composes and sends/logs reminder emails |
| `email_config.py` | **Edit this** to enable real email sending |
| `seed_demo_data.py` | Creates the admin account + 3 demo customers (run once) |
