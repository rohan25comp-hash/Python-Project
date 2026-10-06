"""
login.py
Customer account login / signup screen, shown before the main app.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database as db


class LoginApp(tk.Tk):
    """
    Shows a Login view and a Create Account (signup) view in the same
    window. On success, self.result is set to a dict describing the
    logged-in user and the window closes. If the person closes the
    window instead, self.result stays None.
    """

    def __init__(self):
        super().__init__()
        self.title("Two-Wheeler Service Reminder Manager -- Login")
        self.geometry("430x480")
        self.resizable(False, False)
        self.result = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Bajaj & TVS Service Reminder Manager",
                  font=("Calibri", 14, "bold"), wraplength=380, justify="center").pack(pady=(0, 15))

        self.login_frame = ttk.Frame(container)
        self.signup_frame = ttk.Frame(container)

        self._build_login_frame()
        self._build_signup_frame()

        self.login_frame.pack(fill="both", expand=True)

    def _on_close(self):
        self.result = None
        self.destroy()

    # ------------------------------------------------------------------
    def _build_login_frame(self):
        f = self.login_frame
        ttk.Label(f, text="Log In", font=("Calibri", 12, "bold")).pack(pady=(0, 10))

        ttk.Label(f, text="Username").pack(anchor="w")
        self.l_username = ttk.Entry(f, width=32)
        self.l_username.pack(pady=(0, 8))

        ttk.Label(f, text="Password").pack(anchor="w")
        self.l_password = ttk.Entry(f, width=32, show="*")
        self.l_password.pack(pady=(0, 8))
        self.l_password.bind("<Return>", lambda _e: self._do_login())

        ttk.Button(f, text="Log In", command=self._do_login).pack(fill="x", pady=(10, 4))
        ttk.Separator(f).pack(fill="x", pady=10)
        ttk.Label(f, text="New customer?").pack()
        ttk.Button(f, text="Create Account",
                   command=self._show_signup).pack(fill="x", pady=(4, 0))

    def _do_login(self):
        username = self.l_username.get().strip()
        password = self.l_password.get()
        if not username or not password:
            messagebox.showerror("Missing Details", "Enter both username and password.")
            return
        try:
            user_row = db.authenticate_user(username, password)
        except db.InvalidLoginError as exc:
            messagebox.showerror("Login Failed", str(exc))
            return
        self.result = {"id": user_row["id"], "full_name": user_row["full_name"],
                        "username": user_row["username"], "email": user_row["email"],
                        "role": user_row["role"]}
        self.destroy()

    # ------------------------------------------------------------------
    def _build_signup_frame(self):
        f = self.signup_frame
        ttk.Label(f, text="Create Account", font=("Calibri", 12, "bold")).pack(pady=(0, 10))

        ttk.Label(f, text="Full Name").pack(anchor="w")
        self.s_fullname = ttk.Entry(f, width=32)
        self.s_fullname.pack(pady=(0, 6))

        ttk.Label(f, text="Username").pack(anchor="w")
        self.s_username = ttk.Entry(f, width=32)
        self.s_username.pack(pady=(0, 6))

        ttk.Label(f, text="Email (for service reminders)").pack(anchor="w")
        self.s_email = ttk.Entry(f, width=32)
        self.s_email.pack(pady=(0, 6))

        ttk.Label(f, text="Phone (optional)").pack(anchor="w")
        self.s_phone = ttk.Entry(f, width=32)
        self.s_phone.pack(pady=(0, 6))

        ttk.Label(f, text="Password").pack(anchor="w")
        self.s_password = ttk.Entry(f, width=32, show="*")
        self.s_password.pack(pady=(0, 6))

        ttk.Label(f, text="Confirm Password").pack(anchor="w")
        self.s_password2 = ttk.Entry(f, width=32, show="*")
        self.s_password2.pack(pady=(0, 6))
        self.s_password2.bind("<Return>", lambda _e: self._do_signup())

        ttk.Button(f, text="Create Account", command=self._do_signup).pack(fill="x", pady=(10, 4))
        ttk.Button(f, text="Back to Log In", command=self._show_login).pack(fill="x", pady=(4, 0))

    def _do_signup(self):
        full_name = self.s_fullname.get().strip()
        username = self.s_username.get().strip()
        email = self.s_email.get().strip()
        phone = self.s_phone.get().strip()
        password = self.s_password.get()
        password2 = self.s_password2.get()

        if not full_name or not username or not email or not password:
            messagebox.showerror("Missing Details",
                                  "Full name, username, email and password are required.")
            return
        if "@" not in email or "." not in email.split("@")[-1]:
            messagebox.showerror("Invalid Email", "Enter a valid email address.")
            return
        if len(password) < 4:
            messagebox.showerror("Weak Password", "Password must be at least 4 characters.")
            return
        if password != password2:
            messagebox.showerror("Password Mismatch", "Passwords do not match.")
            return

        try:
            # role is always "customer" here -- never taken from the form,
            # so nobody can self-promote to admin via signup.
            user_id = db.create_user(full_name, username, password, email=email,
                                      phone=phone, role="customer")
        except db.UsernameTakenError as exc:
            messagebox.showerror("Username Taken", str(exc))
            return

        messagebox.showinfo("Account Created", f"Welcome, {full_name}! You're now logged in.")
        self.result = {"id": user_id, "full_name": full_name, "username": username.lower(),
                        "email": email, "role": "customer"}
        self.destroy()

    # ------------------------------------------------------------------
    def _show_signup(self):
        self.login_frame.pack_forget()
        self.signup_frame.pack(fill="both", expand=True)

    def _show_login(self):
        self.signup_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)


def run_login_flow():
    """Show the login/signup window and block until it closes.
    Returns a user dict on success, or None if the person closed the window."""
    window = LoginApp()
    window.mainloop()
    return window.result
