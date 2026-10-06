"""
admin.py
Admin dashboard: view every customer account, every registered vehicle,
and every reminder system-wide, plus a one-click "send reminder emails
to all OVERDUE/DUE SOON customers" action.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database as db
import email_service as es


class AdminApp(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.logout_requested = False

        self.title(f"Service Reminder Manager -- Admin ({user['full_name']})")
        self.geometry("1150x720")
        self.minsize(1000, 640)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24)

        top_bar = ttk.Frame(self, padding=(10, 6))
        top_bar.pack(fill="x")
        ttk.Label(top_bar, text=f"Admin: {user['full_name']} ({user['username']})",
                  font=("Calibri", 10, "bold")).pack(side="left")
        ttk.Button(top_bar, text="Logout", command=self._logout).pack(side="right")
        ttk.Separator(self).pack(fill="x")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.customers_tab = ttk.Frame(notebook)
        self.vehicles_tab = ttk.Frame(notebook)
        self.reminders_tab = ttk.Frame(notebook)
        self.email_tab = ttk.Frame(notebook)

        notebook.add(self.customers_tab, text="  All Customers  ")
        notebook.add(self.vehicles_tab, text="  All Vehicles  ")
        notebook.add(self.reminders_tab, text="  All Reminders  ")
        notebook.add(self.email_tab, text="  Email Center  ")

        self.notebook = notebook
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._build_customers_tab()
        self._build_vehicles_tab()
        self._build_reminders_tab()
        self._build_email_tab()

        self._refresh_customers()
        self._refresh_vehicles()
        self._refresh_reminders()

    def _logout(self):
        if messagebox.askyesno("Log Out", "Log out of the admin account?"):
            self.logout_requested = True
            self.destroy()

    def _on_tab_changed(self, _event):
        current = self.notebook.nametowidget(self.notebook.select())
        if current is self.customers_tab:
            self._refresh_customers()
        elif current is self.vehicles_tab:
            self._refresh_vehicles()
        elif current is self.reminders_tab:
            self._refresh_reminders()

    # ------------------------------------------------------------------
    # All Customers
    # ------------------------------------------------------------------
    def _build_customers_tab(self):
        frame = self.customers_tab
        columns = ("id", "name", "username", "email", "phone", "vehicles")
        self.customers_tree = ttk.Treeview(frame, columns=columns, show="headings", height=22)
        headings = {"id": "ID", "name": "Full Name", "username": "Username", "email": "Email",
                    "phone": "Phone", "vehicles": "Vehicles Registered"}
        widths = {"id": 40, "name": 160, "username": 120, "email": 220, "phone": 110, "vehicles": 130}
        for c in columns:
            self.customers_tree.heading(c, text=headings[c])
            self.customers_tree.column(c, width=widths[c], anchor="center")
        self.customers_tree.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(frame, text="Refresh", command=self._refresh_customers).pack(pady=(0, 8))

    def _refresh_customers(self):
        for row in self.customers_tree.get_children():
            self.customers_tree.delete(row)
        for c in db.get_all_customers():
            vehicle_count = len(db.get_vehicles(c["id"]))
            self.customers_tree.insert("", "end", values=(
                c["id"], c["full_name"], c["username"], c["email"] or "--",
                c["phone"] or "--", vehicle_count))

    # ------------------------------------------------------------------
    # All Vehicles
    # ------------------------------------------------------------------
    def _build_vehicles_tab(self):
        frame = self.vehicles_tab
        columns = ("id", "owner", "brand", "model", "reg", "odo")
        self.vehicles_tree = ttk.Treeview(frame, columns=columns, show="headings", height=22)
        headings = {"id": "ID", "owner": "Owner (Customer)", "brand": "Brand", "model": "Model",
                    "reg": "Reg No.", "odo": "Odometer (km)"}
        widths = {"id": 40, "owner": 170, "brand": 80, "model": 160, "reg": 120, "odo": 110}
        for c in columns:
            self.vehicles_tree.heading(c, text=headings[c])
            self.vehicles_tree.column(c, width=widths[c], anchor="center")
        self.vehicles_tree.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(frame, text="Refresh", command=self._refresh_vehicles).pack(pady=(0, 8))

    def _refresh_vehicles(self):
        for row in self.vehicles_tree.get_children():
            self.vehicles_tree.delete(row)
        for c in db.get_all_customers():
            for v in db.get_vehicles(c["id"]):
                self.vehicles_tree.insert("", "end", values=(
                    v["id"], c["full_name"], v["brand"], v["model"],
                    v["reg_number"], v["current_odometer"]))

    # ------------------------------------------------------------------
    # All Reminders (system-wide)
    # ------------------------------------------------------------------
    def _build_reminders_tab(self):
        frame = self.reminders_tab
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Refresh", command=self._refresh_reminders).pack(side="left")
        ttk.Label(top, text="   ").pack(side="left")
        ttk.Label(top, text="OVERDUE", foreground="white", background="#d9534f", padding=3).pack(side="left", padx=2)
        ttk.Label(top, text="DUE SOON", foreground="white", background="#f0ad4e", padding=3).pack(side="left", padx=2)
        ttk.Label(top, text="OK", foreground="white", background="#5cb85c", padding=3).pack(side="left", padx=2)

        columns = ("customer", "email", "vehicle", "next_date", "days", "smart_eta", "status")
        self.admin_reminder_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        headings = {"customer": "Customer", "email": "Email", "vehicle": "Vehicle",
                    "next_date": "Next Due Date", "days": "Days Left",
                    "smart_eta": "Smart ETA", "status": "Status"}
        widths = {"customer": 140, "email": 190, "vehicle": 210, "next_date": 100,
                  "days": 80, "smart_eta": 100, "status": 90}
        for c in columns:
            self.admin_reminder_tree.heading(c, text=headings[c])
            self.admin_reminder_tree.column(c, width=widths[c], anchor="center")
        self.admin_reminder_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.admin_reminder_tree.tag_configure("overdue", background="#f2dede")
        self.admin_reminder_tree.tag_configure("due_soon", background="#fcf8e3")
        self.admin_reminder_tree.tag_configure("ok", background="#dff0d8")

    def _refresh_reminders(self):
        for row in self.admin_reminder_tree.get_children():
            self.admin_reminder_tree.delete(row)
        for r in db.get_reminders_admin():
            tag = {"OVERDUE": "overdue", "DUE SOON": "due_soon", "OK": "ok"}.get(r["status"], "")
            self.admin_reminder_tree.insert("", "end", tags=(tag,), values=(
                r.get("owner_full_name", "--"), r.get("owner_email", "--"), r["label"],
                r["next_service_date"] or "--",
                r["days_remaining"] if r["days_remaining"] is not None else "--",
                r["smart_eta"] or "--", r["status"]))

    # ------------------------------------------------------------------
    # Email Center
    # ------------------------------------------------------------------
    def _build_email_tab(self):
        frame = self.email_tab
        info = ttk.Label(
            frame,
            text=("Sends one consolidated email to every customer who has at least one "
                  "vehicle OVERDUE or DUE SOON. If email_config.py isn't filled in with "
                  "real SMTP credentials, this runs in safe DRY-RUN mode: nothing is sent "
                  "over the network -- each email that would have been sent is written to "
                  "sent_emails_log.txt instead, so you can still demonstrate the feature."),
            wraplength=1000, justify="left")
        info.pack(fill="x", padx=10, pady=10)

        status_text = "🟢 Configured -- will send real emails" if es.is_configured() else \
                      "🟡 Not configured -- running in DRY-RUN mode (see email_config.py)"
        self.email_status_label = ttk.Label(frame, text=status_text, font=("Calibri", 10, "bold"))
        self.email_status_label.pack(anchor="w", padx=10)

        ttk.Button(frame, text="Send Reminder Emails Now",
                   command=self._send_emails).pack(anchor="w", padx=10, pady=10)

        columns = ("customer", "email", "vehicles", "outcome")
        self.email_result_tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        headings = {"customer": "Customer", "email": "Email", "vehicles": "Vehicles Flagged",
                    "outcome": "Outcome"}
        widths = {"customer": 150, "email": 220, "vehicles": 110, "outcome": 420}
        for c in columns:
            self.email_result_tree.heading(c, text=headings[c])
            self.email_result_tree.column(c, width=widths[c], anchor="w")
        self.email_result_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def _send_emails(self):
        reminders = db.get_reminders_admin()
        results = es.send_reminder_emails(reminders)

        for row in self.email_result_tree.get_children():
            self.email_result_tree.delete(row)
        if not results:
            messagebox.showinfo("Nothing To Send", "No customers currently have an OVERDUE or DUE SOON vehicle.")
            return
        for r in results:
            self.email_result_tree.insert("", "end", values=(
                r["customer"], r["email"], r["vehicle_count"], r["outcome"]))

        mode = "sent for real" if es.is_configured() else "written to sent_emails_log.txt (dry-run)"
        messagebox.showinfo("Done", f"Processed {len(results)} customer(s) -- emails {mode}.")


if __name__ == "__main__":
    print("Run 'python app.py' instead -- it shows the login screen and routes "
          "admin accounts here automatically.")
