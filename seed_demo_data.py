"""
seed_demo_data.py
Run this ONCE after setting up the project to create:
  - one ADMIN account
  - three demo CUSTOMER accounts, each with vehicle(s) and service
    history already logged, so Reminders / Smart ETA / Email Center all
    have real data to show a judge immediately -- no manual data entry
    needed for the demo.

Usage:
    python seed_demo_data.py

Safe to re-run: if a username already exists, that account (and its
vehicles) is skipped rather than duplicated.

Due dates are computed the same way the running app computes them
(config.get_interval + db.add_months), relative to TODAY at the moment
you run this script -- so run it shortly before your demo for the
freshest OVERDUE / DUE SOON timing.
"""

from datetime import date, timedelta

import config
import database as db


def log_service(vehicle_id, service_date, service_type, cost, odometer, notes=""):
    """Mirrors exactly what the GUI's 'Save Service Record' button does."""
    vehicle = db.get_vehicle(vehicle_id)
    interval = config.get_interval(vehicle["brand"], vehicle["model"])
    next_date = db.add_months(service_date, interval["months"])
    next_odo = odometer + interval["km"]
    db.add_service(vehicle_id, service_date.strftime("%Y-%m-%d"), service_type, cost,
                    odometer, next_date.strftime("%Y-%m-%d"), next_odo, notes)
    return next_date, next_odo


def seed():
    db.init_db()
    today = date.today()
    created, skipped = [], []

    # ---------------------------------------------------------------
    # Admin account
    # ---------------------------------------------------------------
    try:
        admin_id = db.create_user("System Administrator", "admin", "Admin@123",
                                   email="admin@servicemanager.local", role="admin")
        created.append({"role": "ADMIN", "username": "admin", "password": "Admin@123",
                         "user_id": admin_id, "note": "Full admin dashboard + email center"})
    except db.UsernameTakenError:
        skipped.append("admin")

    # ---------------------------------------------------------------
    # Demo customer 1: Rahul Sharma -- 2 vehicles: one OVERDUE, one DUE SOON
    # (best account to show a judge: triggers Reminders colour-coding AND
    #  gets picked up by the Email Center's automated scan)
    # ---------------------------------------------------------------
    try:
        rahul_id = db.create_user("Rahul Sharma", "rahul", "Demo@123",
                                   email="rahul.demo@example.com", phone="9000000001",
                                   role="customer")

        db.add_vehicle(rahul_id, "Rahul Sharma", "Bajaj", "Pulsar 150", "MH01DM001",
                        (today - timedelta(days=220)).isoformat(), 2000)
        v1 = [v for v in db.get_vehicles(rahul_id) if v["reg_number"] == "MH01DM001"][0]["id"]
        # service logged ~4 months ago -> its 3-month due date has already passed = OVERDUE
        log_service(v1, today - timedelta(days=115), "General Service", 650, 2000,
                    "Seeded demo data")

        db.add_vehicle(rahul_id, "Rahul Sharma", "Bajaj", "Platina 100", "MH01DM002",
                        (today - timedelta(days=150)).isoformat(), 1200)
        v2 = [v for v in db.get_vehicles(rahul_id) if v["reg_number"] == "MH01DM002"][0]["id"]
        # service date chosen so its 3-month due date lands 3 days from now = DUE SOON
        log_service(v2, db.add_months(today + timedelta(days=3), -3), "Oil Change", 350, 1200,
                    "Seeded demo data")

        created.append({"role": "CUSTOMER", "username": "rahul", "password": "Demo@123",
                         "user_id": rahul_id,
                         "note": "2 vehicles: Pulsar 150 (OVERDUE), Platina 100 (DUE SOON)"})
    except db.UsernameTakenError:
        skipped.append("rahul")

    # ---------------------------------------------------------------
    # Demo customer 2: Sneha Patil -- 1 vehicle, comfortably OK
    # ---------------------------------------------------------------
    try:
        sneha_id = db.create_user("Sneha Patil", "sneha", "Demo@123",
                                   email="sneha.demo@example.com", phone="9000000002",
                                   role="customer")
        db.add_vehicle(sneha_id, "Sneha Patil", "TVS", "Jupiter", "MH02DM001",
                        (today - timedelta(days=100)).isoformat(), 1800)
        v3 = db.get_vehicles(sneha_id)[0]["id"]
        log_service(v3, today - timedelta(days=10), "General Service", 500, 1830,
                    "Seeded demo data")
        created.append({"role": "CUSTOMER", "username": "sneha", "password": "Demo@123",
                         "user_id": sneha_id, "note": "1 vehicle: Jupiter (OK)"})
    except db.UsernameTakenError:
        skipped.append("sneha")

    # ---------------------------------------------------------------
    # Demo customer 3: Vikram Rao -- 1 vehicle, status OK by the calendar,
    # but a genuinely fast rider (~50 km/day across 2 real service
    # records) -- best account to showcase Smart ETA pulling the
    # predicted date noticeably earlier than the plain calendar date.
    # ---------------------------------------------------------------
    try:
        vikram_id = db.create_user("Vikram Rao", "vikram", "Demo@123",
                                    email="vikram.demo@example.com", phone="9000000003",
                                    role="customer")
        db.add_vehicle(vikram_id, "Vikram Rao", "TVS", "Apache RTR 200 4V", "MH03DM001",
                        (today - timedelta(days=120)).isoformat(), 0)
        v4 = db.get_vehicles(vikram_id)[0]["id"]
        log_service(v4, today - timedelta(days=70), "General Service", 700, 3000,
                    "Seeded demo data -- pace point 1")
        log_service(v4, today - timedelta(days=10), "Oil Change", 400, 6000,
                    "Seeded demo data -- pace point 2 (~50 km/day pace)")
        created.append({"role": "CUSTOMER", "username": "vikram", "password": "Demo@123",
                         "user_id": vikram_id,
                         "note": "1 vehicle: Apache RTR 200 4V -- Smart ETA showcase (fast rider)"})
    except db.UsernameTakenError:
        skipped.append("vikram")

    return created, skipped


if __name__ == "__main__":
    created, skipped = seed()

    print("=" * 72)
    print("SEEDING COMPLETE")
    print("=" * 72)
    if created:
        print("\nCreated accounts:\n")
        for c in created:
            print(f"  [{c['role']}] username: {c['username']:10s}  password: {c['password']:10s}"
                  f"  (user_id={c['user_id']})")
            print(f"           {c['note']}")
    if skipped:
        print("\nAlready existed, skipped (not duplicated):", ", ".join(skipped))
    print("\nRun 'python app.py' and log in with any of the accounts above.")
