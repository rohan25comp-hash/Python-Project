"""
app.py
Entry point for the Bajaj & TVS Two-Wheeler Service Reminder Manager.

Run this file (not main.py directly):
    python app.py

Flow:
    1. Shows the Login / Create Account window.
    2. On successful login (or signup), opens the main application,
       scoped entirely to that customer's own vehicles and services.
    3. If the customer clicks "Logout", control returns to the login
       screen. Closing the main window normally (or the login window)
       exits the program.
"""

import database as db
from login import run_login_flow
from main import ServiceManagerApp
from admin import AdminApp


def main():
    db.init_db()
    while True:
        user = run_login_flow()
        if user is None:
            break  # login window closed -- exit program

        if user.get("role") == "admin":
            app = AdminApp(user)
        else:
            app = ServiceManagerApp(user)
        app.mainloop()

        if not app.logout_requested:
            break  # main window closed normally -- exit program
        # else: loop back around to the login screen


if __name__ == "__main__":
    main()
