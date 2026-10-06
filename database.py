"""
database.py
SQLite persistence layer for the Two-Wheeler Service Reminder Manager.
Pure data-access functions -- no GUI code lives here, so it can be
unit-tested or reused independently of Tkinter.
"""

import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
import calendar

import auth

DB_PATH = Path(__file__).parent / "service_manager.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT,
            role TEXT NOT NULL DEFAULT 'customer',
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            owner_name TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            reg_number TEXT UNIQUE NOT NULL,
            purchase_date TEXT,
            current_odometer INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            service_date TEXT NOT NULL,
            service_type TEXT NOT NULL,
            cost REAL DEFAULT 0,
            odometer_at_service INTEGER NOT NULL,
            next_service_date TEXT,
            next_service_odometer INTEGER,
            notes TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
        )
    """)
    conn.commit()

    # Lightweight migration: earlier versions of this project had no
    # accounts, so vehicles had no user_id column. Add it if missing
    # rather than crashing on an existing database file.
    cur.execute("PRAGMA table_info(vehicles)")
    existing_cols = [row[1] for row in cur.fetchall()]
    if "user_id" not in existing_cols:
        cur.execute("ALTER TABLE vehicles ADD COLUMN user_id INTEGER")
        conn.commit()

    cur.execute("PRAGMA table_info(users)")
    existing_user_cols = [row[1] for row in cur.fetchall()]
    if "email" not in existing_user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
    if "role" not in existing_user_cols:
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'customer'")
        conn.commit()

    conn.close()


# ------------------------- user account operations -------------------------

class UsernameTakenError(Exception):
    pass


class InvalidLoginError(Exception):
    pass


def create_user(full_name: str, username: str, password: str, email: str = "",
                 phone: str = "", role: str = "customer"):
    """
    Create a new account. Raises UsernameTakenError on duplicate username.
    `role` is never taken from end-user input in the signup form -- only
    the seeding script creates 'admin' accounts, so a customer can never
    self-promote by typing something into a form field.
    """
    salt_hex, hash_hex = auth.hash_password(password)
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO users (full_name, username, email, phone, role,
                                   password_salt, password_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (full_name.strip(), username.strip().lower(), email.strip(), phone.strip(), role,
             salt_hex, hash_hex, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        new_id = conn.execute("SELECT id FROM users WHERE username = ?",
                               (username.strip().lower(),)).fetchone()["id"]
        return new_id
    except sqlite3.IntegrityError:
        raise UsernameTakenError(f"Username '{username}' is already taken.")
    finally:
        conn.close()


def get_all_customers():
    """All customer (non-admin) accounts, for the admin dashboard."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE role = 'customer' ORDER BY full_name"
    ).fetchall()
    conn.close()
    return rows


def authenticate_user(username: str, password: str):
    """Return the user row on success. Raises InvalidLoginError on failure."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?",
                        (username.strip().lower(),)).fetchone()
    conn.close()
    if row is None or not auth.verify_password(password, row["password_salt"], row["password_hash"]):
        raise InvalidLoginError("Incorrect username or password.")
    return row


def get_user(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


# ---------- date helper (no external dependency needed) ----------

def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


# ---------------------- vehicle operations ------------------------

def add_vehicle(user_id, owner_name, brand, model, reg_number, purchase_date, current_odometer):
    conn = get_connection()
    conn.execute(
        """INSERT INTO vehicles
           (user_id, owner_name, brand, model, reg_number, purchase_date, current_odometer)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, owner_name, brand, model, reg_number.upper().strip(), purchase_date, current_odometer),
    )
    conn.commit()
    conn.close()


def get_vehicles(user_id):
    """Only this customer's own vehicles -- never another account's."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM vehicles WHERE user_id = ? ORDER BY id DESC", (user_id,)
    ).fetchall()
    conn.close()
    return rows


def get_vehicle(vehicle_id, user_id=None):
    """If user_id is given, only returns the vehicle when it belongs to that account."""
    conn = get_connection()
    if user_id is None:
        row = conn.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
    else:
        row = conn.execute("SELECT * FROM vehicles WHERE id = ? AND user_id = ?",
                            (vehicle_id, user_id)).fetchone()
    conn.close()
    return row


def delete_vehicle(vehicle_id, user_id=None):
    conn = get_connection()
    if user_id is None:
        conn.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
    else:
        conn.execute("DELETE FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user_id))
    conn.commit()
    conn.close()


def update_vehicle_odometer(vehicle_id, odometer):
    conn = get_connection()
    conn.execute(
        "UPDATE vehicles SET current_odometer = ? WHERE id = ? AND current_odometer < ?",
        (odometer, vehicle_id, odometer),
    )
    conn.commit()
    conn.close()


# ---------------------- service operations ------------------------

def add_service(vehicle_id, service_date, service_type, cost, odometer_at_service,
                 next_service_date, next_service_odometer, notes):
    conn = get_connection()
    conn.execute(
        """INSERT INTO services
           (vehicle_id, service_date, service_type, cost, odometer_at_service,
            next_service_date, next_service_odometer, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (vehicle_id, service_date, service_type, cost, odometer_at_service,
         next_service_date, next_service_odometer, notes),
    )
    conn.commit()
    conn.close()
    update_vehicle_odometer(vehicle_id, odometer_at_service)


def get_services_for_vehicle(vehicle_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM services WHERE vehicle_id = ? ORDER BY service_date DESC, id DESC",
        (vehicle_id,),
    ).fetchall()
    conn.close()
    return rows


def get_latest_service(vehicle_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM services WHERE vehicle_id = ? ORDER BY service_date DESC, id DESC LIMIT 1",
        (vehicle_id,),
    ).fetchone()
    conn.close()
    return row


def get_all_services(user_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT services.*, vehicles.brand, vehicles.model, vehicles.reg_number
        FROM services JOIN vehicles ON services.vehicle_id = vehicles.id
        WHERE vehicles.user_id = ?
        ORDER BY service_date DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows


def get_average_daily_km(vehicle_id, vehicle_row=None):
    """
    UNIQUE FEATURE: estimate how many km this specific rider actually
    covers per day, from their own service history, instead of assuming
    every rider rides at the same generic pace.

    - 2+ service records -> use the oldest and newest record as the
      measurement window (most accurate: reflects real recent usage).
    - Exactly 1 service record -> fall back to (purchase_date -> that
      service), a rougher but still personalised estimate.
    - 0 service records -> not enough data yet; returns None.
    """
    services = get_services_for_vehicle(vehicle_id)  # newest first
    services = list(reversed(services))              # oldest first

    if len(services) >= 2:
        oldest, newest = services[0], services[-1]
        days = (datetime.strptime(newest["service_date"], "%Y-%m-%d").date() -
                datetime.strptime(oldest["service_date"], "%Y-%m-%d").date()).days
        km = newest["odometer_at_service"] - oldest["odometer_at_service"]
        if days > 0 and km > 0:
            return km / days
        return None

    if len(services) == 1:
        vehicle = vehicle_row or get_vehicle(vehicle_id)
        if not vehicle["purchase_date"]:
            return None
        purchase_date = datetime.strptime(vehicle["purchase_date"], "%Y-%m-%d").date()
        service_date = datetime.strptime(services[0]["service_date"], "%Y-%m-%d").date()
        days = (service_date - purchase_date).days
        km = services[0]["odometer_at_service"]
        if days > 0 and km > 0:
            return km / days
        return None

    return None


def _build_reminder_row(v, today=None):
    """
    Shared core: build one reminder dict for a single vehicle row `v`.
    Used by both get_reminders() (one customer's own vehicles) and
    get_reminders_admin() (every vehicle, for the admin dashboard and the
    automated email scan) so the OVERDUE/DUE SOON/Smart-ETA logic only
    lives in one place.
    """
    today = today or date.today()
    last = get_latest_service(v["id"])
    if last:
        next_date_str = last["next_service_date"]
        next_km = last["next_service_odometer"]
        last_date_str = last["service_date"]
    else:
        next_date_str = None
        next_km = None
        last_date_str = None

    days_remaining = None
    km_remaining = None
    if next_date_str:
        next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
        days_remaining = (next_date - today).days
    if next_km is not None:
        km_remaining = next_km - v["current_odometer"]

    status = "No service logged yet"
    if days_remaining is not None or km_remaining is not None:
        overdue = (days_remaining is not None and days_remaining < 0) or \
                  (km_remaining is not None and km_remaining < 0)
        due_soon = (days_remaining is not None and 0 <= days_remaining <= 7) or \
                   (km_remaining is not None and 0 <= km_remaining <= 200)
        if overdue:
            status = "OVERDUE"
        elif due_soon:
            status = "DUE SOON"
        else:
            status = "OK"

    # ---- Smart ETA (usage-based prediction) ----
    smart_eta_str = None
    smart_basis = None
    avg_km_per_day = get_average_daily_km(v["id"], v)
    if next_date_str and km_remaining is not None:
        calendar_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
        if avg_km_per_day and avg_km_per_day > 0:
            days_to_km_due = km_remaining / avg_km_per_day
            usage_projected_date = today + timedelta(days=max(days_to_km_due, 0))
            if usage_projected_date < calendar_date:
                smart_eta_str = usage_projected_date.strftime("%Y-%m-%d")
                smart_basis = "Usage-based"
            else:
                smart_eta_str = calendar_date.strftime("%Y-%m-%d")
                smart_basis = "Calendar-based"
        else:
            smart_eta_str = calendar_date.strftime("%Y-%m-%d")
            smart_basis = "Calendar-based (not enough ride data yet)"

    return {
        "vehicle_id": v["id"],
        "user_id": v["user_id"],
        "label": f"{v['brand']} {v['model']} ({v['reg_number']})",
        "last_service_date": last_date_str,
        "next_service_date": next_date_str,
        "days_remaining": days_remaining,
        "next_service_odometer": next_km,
        "km_remaining": km_remaining,
        "status": status,
        "avg_km_per_day": round(avg_km_per_day, 1) if avg_km_per_day else None,
        "smart_eta": smart_eta_str,
        "smart_basis": smart_basis,
    }


def get_reminders(user_id):
    """Reminders for one customer's own vehicles only."""
    today = date.today()
    return [_build_reminder_row(v, today) for v in get_vehicles(user_id)]


def get_reminders_admin():
    """
    Reminders for EVERY vehicle across ALL customer accounts, each tagged
    with the owning customer's name/email -- used by the admin dashboard
    and by the automated overdue/due-soon email scan.
    """
    today = date.today()
    conn = get_connection()
    vehicles = conn.execute("""
        SELECT vehicles.*, users.full_name AS owner_full_name, users.email AS owner_email
        FROM vehicles JOIN users ON vehicles.user_id = users.id
        ORDER BY vehicles.id DESC
    """).fetchall()
    conn.close()

    reminders = []
    for v in vehicles:
        r = _build_reminder_row(v, today)
        r["owner_full_name"] = v["owner_full_name"]
        r["owner_email"] = v["owner_email"]
        reminders.append(r)
    return reminders
