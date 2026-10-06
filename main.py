"""
main.py
Bajaj & TVS Two-Wheeler Service Reminder Manager
A desktop application (Windows / macOS / Linux) built with:
    Tkinter (GUI)  +  SQLite (storage)  +  Matplotlib (charts)

Run:
    python main.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import config
import database as db


# ----------------------------------------------------------------------
# Small validation helpers
# ----------------------------------------------------------------------

def parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


# ----------------------------------------------------------------------
# Main Application
# ----------------------------------------------------------------------

class ServiceManagerApp(tk.Tk):
    def __init__(self, user):
        """
        user: dict with keys 'id', 'full_name', 'username' -- the
        currently logged-in customer account. Every vehicle, service and
        reminder shown in this window belongs only to this account.
        """
        super().__init__()
        self.user = user
        self.logout_requested = False

        self.title(f"Two-Wheeler Service Reminder Manager -- {user['full_name']}")
        self.geometry("1080x700")
        self.minsize(980, 640)

        db.init_db()

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24)
        style.configure("Overdue.Treeview", foreground="red")

        account_bar = ttk.Frame(self, padding=(10, 6))
        account_bar.pack(fill="x")
        ttk.Label(account_bar, text=f"Logged in as: {user['full_name']} ({user['username']})",
                  font=("Calibri", 10, "bold")).pack(side="left")
        ttk.Button(account_bar, text="Logout", command=self._logout).pack(side="right")
        ttk.Separator(self).pack(fill="x")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.vehicles_tab = ttk.Frame(notebook)
        self.service_tab = ttk.Frame(notebook)
        self.reminders_tab = ttk.Frame(notebook)
        self.dashboard_tab = ttk.Frame(notebook)

        notebook.add(self.vehicles_tab, text="  Vehicles  ")
        notebook.add(self.service_tab, text="  Service Records  ")
        notebook.add(self.reminders_tab, text="  Reminders  ")
        notebook.add(self.dashboard_tab, text="  Dashboard  ")

        self.notebook = notebook
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._build_vehicles_tab()
        self._build_service_tab()
        self._build_reminders_tab()
        self._build_dashboard_tab()

        self._refresh_vehicles_list()
        self._refresh_vehicle_selectors()
        self._refresh_reminders()

    def _on_tab_changed(self, _event):
        current = self.notebook.select()
        if self.notebook.nametowidget(current) is self.reminders_tab:
            self._refresh_reminders()
        elif self.notebook.nametowidget(current) is self.dashboard_tab:
            self._refresh_dashboard()
        elif self.notebook.nametowidget(current) is self.service_tab:
            self._refresh_vehicle_selectors()

    def _logout(self):
        if messagebox.askyesno("Log Out", "Log out of this account?"):
            self.logout_requested = True
            self.destroy()

    # ------------------------------------------------------------------
    # TAB 1: Vehicles
    # ------------------------------------------------------------------

    def _build_vehicles_tab(self):
        frame = self.vehicles_tab
        form = ttk.LabelFrame(frame, text="Add Vehicle")
        form.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(form, text=f"Registering to: {self.user['full_name']}",
                  foreground="gray").grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(4, 10))

        ttk.Label(form, text="Brand").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.v_brand = ttk.Combobox(form, values=config.BRANDS, state="readonly", width=23)
        self.v_brand.grid(row=1, column=1, padx=6, pady=4)
        self.v_brand.bind("<<ComboboxSelected>>", self._on_brand_selected)

        ttk.Label(form, text="Model").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        self.v_model = ttk.Combobox(form, values=[], state="readonly", width=23)
        self.v_model.grid(row=2, column=1, padx=6, pady=4)

        ttk.Label(form, text="Registration No.").grid(row=3, column=0, sticky="w", padx=6, pady=4)
        self.v_reg = ttk.Entry(form, width=26)
        self.v_reg.grid(row=3, column=1, padx=6, pady=4)

        ttk.Label(form, text="Purchase Date").grid(row=4, column=0, sticky="w", padx=6, pady=4)
        self.v_purchase = ttk.Entry(form, width=26)
        self.v_purchase.insert(0, today_str())
        self.v_purchase.grid(row=4, column=1, padx=6, pady=4)
        ttk.Label(form, text="(YYYY-MM-DD)", foreground="gray").grid(row=5, column=1, sticky="w", padx=6)

        ttk.Label(form, text="Current Odometer (km)").grid(row=6, column=0, sticky="w", padx=6, pady=4)
        self.v_odo = ttk.Entry(form, width=26)
        self.v_odo.insert(0, "0")
        self.v_odo.grid(row=6, column=1, padx=6, pady=4)

        ttk.Button(form, text="Add Vehicle", command=self._add_vehicle).grid(
            row=7, column=0, columnspan=2, pady=12, sticky="ew", padx=6)

        list_frame = ttk.LabelFrame(frame, text="Registered Vehicles")
        list_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        columns = ("id", "owner", "brand", "model", "reg", "odo", "purchase")
        self.vehicle_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=18)
        headings = {"id": "ID", "owner": "Owner", "brand": "Brand", "model": "Model",
                    "reg": "Reg No.", "odo": "Odometer (km)", "purchase": "Purchased"}
        widths = {"id": 40, "owner": 110, "brand": 70, "model": 150,
                  "reg": 110, "odo": 100, "purchase": 100}
        for c in columns:
            self.vehicle_tree.heading(c, text=headings[c])
            self.vehicle_tree.column(c, width=widths[c], anchor="center")
        self.vehicle_tree.pack(fill="both", expand=True, padx=6, pady=6)

        ttk.Button(list_frame, text="Delete Selected Vehicle",
                   command=self._delete_vehicle).pack(pady=6)

    def _on_brand_selected(self, _event=None):
        brand = self.v_brand.get()
        self.v_model["values"] = config.get_models(brand)
        self.v_model.set("")

    def _add_vehicle(self):
        brand = self.v_brand.get().strip()
        model = self.v_model.get().strip()
        reg = self.v_reg.get().strip()
        purchase = self.v_purchase.get().strip()
        odo = self.v_odo.get().strip()

        if not (brand and model and reg):
            messagebox.showerror("Missing Data", "Brand, Model and Registration No. are required.")
            return
        try:
            parse_date(purchase)
        except ValueError:
            messagebox.showerror("Invalid Date", "Purchase date must be in YYYY-MM-DD format.")
            return
        try:
            odo_val = int(odo)
        except ValueError:
            messagebox.showerror("Invalid Odometer", "Odometer reading must be a whole number.")
            return

        try:
            db.add_vehicle(self.user["id"], self.user["full_name"], brand, model, reg, purchase, odo_val)
        except Exception as exc:  # e.g. UNIQUE constraint on reg_number
            messagebox.showerror("Could not add vehicle", str(exc))
            return

        self.v_reg.delete(0, tk.END)
        self.v_odo.delete(0, tk.END)
        self.v_odo.insert(0, "0")

        self._refresh_vehicles_list()
        self._refresh_vehicle_selectors()
        messagebox.showinfo("Added", f"Vehicle {brand} {model} ({reg.upper()}) added.")

    def _refresh_vehicles_list(self):
        for row in self.vehicle_tree.get_children():
            self.vehicle_tree.delete(row)
        for v in db.get_vehicles(self.user["id"]):
            self.vehicle_tree.insert("", "end", values=(
                v["id"], v["owner_name"], v["brand"], v["model"],
                v["reg_number"], v["current_odometer"], v["purchase_date"]))

    def _delete_vehicle(self):
        selected = self.vehicle_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a vehicle to delete.")
            return
        values = self.vehicle_tree.item(selected[0], "values")
        vehicle_id = values[0]
        if messagebox.askyesno("Confirm Delete",
                                "Delete this vehicle and all its service history?"):
            db.delete_vehicle(vehicle_id, self.user["id"])
            self._refresh_vehicles_list()
            self._refresh_vehicle_selectors()

    # ------------------------------------------------------------------
    # TAB 2: Service Records
    # ------------------------------------------------------------------

    def _build_service_tab(self):
        frame = self.service_tab
        form = ttk.LabelFrame(frame, text="Log a Service")
        form.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(form, text="Vehicle").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.s_vehicle = ttk.Combobox(form, values=[], state="readonly", width=30)
        self.s_vehicle.grid(row=0, column=1, padx=6, pady=4)
        self.s_vehicle.bind("<<ComboboxSelected>>", self._on_service_vehicle_selected)

        ttk.Label(form, text="Service Date").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        self.s_date = ttk.Entry(form, width=30)
        self.s_date.insert(0, today_str())
        self.s_date.grid(row=1, column=1, padx=6, pady=4)

        ttk.Label(form, text="Service Type").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        self.s_type = ttk.Combobox(form, values=config.SERVICE_TYPES, state="readonly", width=28)
        self.s_type.grid(row=2, column=1, padx=6, pady=4)

        ttk.Label(form, text="Cost (₹)").grid(row=3, column=0, sticky="w", padx=6, pady=4)
        self.s_cost = ttk.Entry(form, width=30)
        self.s_cost.insert(0, "0")
        self.s_cost.grid(row=3, column=1, padx=6, pady=4)

        ttk.Label(form, text="Odometer at Service (km)").grid(row=4, column=0, sticky="w", padx=6, pady=4)
        self.s_odo = ttk.Entry(form, width=30)
        self.s_odo.grid(row=4, column=1, padx=6, pady=4)

        ttk.Label(form, text="Notes").grid(row=5, column=0, sticky="nw", padx=6, pady=4)
        self.s_notes = tk.Text(form, width=28, height=4)
        self.s_notes.grid(row=5, column=1, padx=6, pady=4)

        self.s_interval_label = ttk.Label(form, text="Next due: --", foreground="gray")
        self.s_interval_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=6, pady=4)

        ttk.Button(form, text="Save Service Record", command=self._add_service).grid(
            row=7, column=0, columnspan=2, pady=12, sticky="ew", padx=6)

        list_frame = ttk.LabelFrame(frame, text="Service History (selected vehicle)")
        list_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        columns = ("date", "type", "cost", "odo", "next_date", "next_odo", "notes")
        self.service_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=18)
        headings = {"date": "Date", "type": "Type", "cost": "Cost (₹)", "odo": "Odometer",
                    "next_date": "Next Due Date", "next_odo": "Next Due Km", "notes": "Notes"}
        widths = {"date": 90, "type": 150, "cost": 70, "odo": 80,
                  "next_date": 100, "next_odo": 90, "notes": 160}
        for c in columns:
            self.service_tree.heading(c, text=headings[c])
            self.service_tree.column(c, width=widths[c], anchor="center")
        self.service_tree.pack(fill="both", expand=True, padx=6, pady=6)

    def _refresh_vehicle_selectors(self):
        vehicles = db.get_vehicles(self.user["id"])
        self._vehicle_lookup = {
            f"{v['brand']} {v['model']} ({v['reg_number']})": v["id"] for v in vehicles
        }
        labels = list(self._vehicle_lookup.keys())
        self.s_vehicle["values"] = labels
        if hasattr(self, "d_vehicle"):
            self.d_vehicle["values"] = ["All Vehicles"] + labels
            if not self.d_vehicle.get():
                self.d_vehicle.set("All Vehicles")

    def _on_service_vehicle_selected(self, _event=None):
        label = self.s_vehicle.get()
        vehicle_id = self._vehicle_lookup.get(label)
        if vehicle_id is None:
            return
        vehicle = db.get_vehicle(vehicle_id, self.user["id"])
        self.s_odo.delete(0, tk.END)
        self.s_odo.insert(0, str(vehicle["current_odometer"]))
        interval = config.get_interval(vehicle["brand"], vehicle["model"])
        self.s_interval_label.config(
            text=f"Next due: every {interval['km']} km or {interval['months']} month(s)")
        self._refresh_service_history(vehicle_id)

    def _add_service(self):
        label = self.s_vehicle.get()
        vehicle_id = self._vehicle_lookup.get(label) if hasattr(self, "_vehicle_lookup") else None
        if vehicle_id is None:
            messagebox.showerror("No Vehicle", "Select a vehicle first.")
            return

        try:
            service_date = parse_date(self.s_date.get())
        except ValueError:
            messagebox.showerror("Invalid Date", "Service date must be in YYYY-MM-DD format.")
            return

        service_type = self.s_type.get().strip()
        if not service_type:
            messagebox.showerror("Missing Data", "Select a service type.")
            return

        try:
            cost = float(self.s_cost.get())
            odometer = int(self.s_odo.get())
        except ValueError:
            messagebox.showerror("Invalid Number", "Cost and odometer must be numeric.")
            return

        notes = self.s_notes.get("1.0", tk.END).strip()
        vehicle = db.get_vehicle(vehicle_id, self.user["id"])
        interval = config.get_interval(vehicle["brand"], vehicle["model"])
        next_date = db.add_months(service_date, interval["months"])
        next_odo = odometer + interval["km"]

        db.add_service(
            vehicle_id, service_date.strftime("%Y-%m-%d"), service_type, cost, odometer,
            next_date.strftime("%Y-%m-%d"), next_odo, notes)

        self.s_notes.delete("1.0", tk.END)
        self._refresh_service_history(vehicle_id)
        self._refresh_vehicles_list()
        messagebox.showinfo(
            "Saved",
            f"Service logged. Next due {next_date.strftime('%Y-%m-%d')} or {next_odo} km.")

    def _refresh_service_history(self, vehicle_id):
        for row in self.service_tree.get_children():
            self.service_tree.delete(row)
        for s in db.get_services_for_vehicle(vehicle_id):
            self.service_tree.insert("", "end", values=(
                s["service_date"], s["service_type"], f"{s['cost']:.2f}",
                s["odometer_at_service"], s["next_service_date"] or "--",
                s["next_service_odometer"] or "--", s["notes"] or ""))

    # ------------------------------------------------------------------
    # TAB 3: Reminders
    # ------------------------------------------------------------------

    def _build_reminders_tab(self):
        frame = self.reminders_tab
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Refresh Reminders", command=self._refresh_reminders).pack(side="left")
        ttk.Label(top, text="   Colour key:").pack(side="left", padx=(20, 4))
        ttk.Label(top, text="OVERDUE", foreground="white", background="#d9534f",
                  padding=3).pack(side="left", padx=2)
        ttk.Label(top, text="DUE SOON", foreground="white", background="#f0ad4e",
                  padding=3).pack(side="left", padx=2)
        ttk.Label(top, text="OK", foreground="white", background="#5cb85c",
                  padding=3).pack(side="left", padx=2)

        caption = ttk.Label(
            frame,
            text=("🧠 Smart ETA learns each vehicle's real riding pace from its own service "
                  "history and predicts the sooner of a calendar-based or usage-based due date "
                  "-- instead of assuming every rider covers the same distance every month."),
            foreground="#555555", wraplength=980, justify="left")
        caption.pack(fill="x", padx=8, pady=(0, 4))

        columns = ("vehicle", "last", "next_date", "days", "next_odo", "km_left",
                   "status", "pace", "smart_eta", "basis")
        self.reminder_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        headings = {"vehicle": "Vehicle", "last": "Last Service", "next_date": "Next Due Date",
                    "days": "Days Left", "next_odo": "Next Due Km", "km_left": "Km Left",
                    "status": "Status", "pace": "Rider Pace (km/day)",
                    "smart_eta": "🧠 Smart ETA", "basis": "Prediction Basis"}
        widths = {"vehicle": 200, "last": 90, "next_date": 90, "days": 70,
                  "next_odo": 90, "km_left": 75, "status": 90, "pace": 110,
                  "smart_eta": 100, "basis": 150}
        for c in columns:
            self.reminder_tree.heading(c, text=headings[c])
            self.reminder_tree.column(c, width=widths[c], anchor="center")
        self.reminder_tree.pack(fill="both", expand=True, padx=8, pady=8)

        self.reminder_tree.tag_configure("overdue", background="#f2dede")
        self.reminder_tree.tag_configure("due_soon", background="#fcf8e3")
        self.reminder_tree.tag_configure("ok", background="#dff0d8")

    def _refresh_reminders(self):
        for row in self.reminder_tree.get_children():
            self.reminder_tree.delete(row)
        for r in db.get_reminders(self.user["id"]):
            tag = {"OVERDUE": "overdue", "DUE SOON": "due_soon", "OK": "ok"}.get(r["status"], "")
            self.reminder_tree.insert("", "end", tags=(tag,), values=(
                r["label"], r["last_service_date"] or "Never",
                r["next_service_date"] or "--",
                r["days_remaining"] if r["days_remaining"] is not None else "--",
                r["next_service_odometer"] if r["next_service_odometer"] is not None else "--",
                r["km_remaining"] if r["km_remaining"] is not None else "--",
                r["status"],
                r["avg_km_per_day"] if r["avg_km_per_day"] is not None else "--",
                r["smart_eta"] or "--",
                r["smart_basis"] or "--"))

    # ------------------------------------------------------------------
    # TAB 4: Dashboard
    # ------------------------------------------------------------------

    def _build_dashboard_tab(self):
        frame = self.dashboard_tab
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="View:").pack(side="left")
        self.d_vehicle = ttk.Combobox(top, values=["All Vehicles"], state="readonly", width=35)
        self.d_vehicle.set("All Vehicles")
        self.d_vehicle.pack(side="left", padx=6)
        ttk.Button(top, text="Refresh Charts", command=self._refresh_dashboard).pack(side="left", padx=10)

        self.fig = Figure(figsize=(9.5, 6), dpi=100)
        self.ax_cost = self.fig.add_subplot(211)
        self.ax_odo = self.fig.add_subplot(212)
        self.fig.subplots_adjust(hspace=0.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    def _refresh_dashboard(self):
        self.ax_cost.clear()
        self.ax_odo.clear()

        selection = self.d_vehicle.get()
        vehicles = db.get_vehicles(self.user["id"])

        if selection == "All Vehicles" or not selection:
            labels = [f"{v['brand']} {v['model']}\n{v['reg_number']}" for v in vehicles]
            totals = []
            for v in vehicles:
                services = db.get_services_for_vehicle(v["id"])
                totals.append(sum(s["cost"] for s in services))
            self.ax_cost.bar(labels, totals, color="#337ab7")
            self.ax_cost.set_title("Total Service Cost per Vehicle")
            self.ax_cost.set_ylabel("Cost (₹)")
            self.ax_cost.tick_params(axis="x", labelrotation=15, labelsize=8)

            self.ax_odo.bar(labels, [v["current_odometer"] for v in vehicles], color="#5cb85c")
            self.ax_odo.set_title("Current Odometer Reading per Vehicle")
            self.ax_odo.set_ylabel("Km")
            self.ax_odo.tick_params(axis="x", labelrotation=15, labelsize=8)
        else:
            vehicle_id = getattr(self, "_vehicle_lookup", {}).get(selection)
            if vehicle_id is None:
                self.canvas.draw()
                return
            services = list(reversed(db.get_services_for_vehicle(vehicle_id)))
            dates = [s["service_date"] for s in services]
            costs = [s["cost"] for s in services]
            odos = [s["odometer_at_service"] for s in services]

            self.ax_cost.plot(dates, costs, marker="o", color="#337ab7")
            self.ax_cost.set_title(f"Service Cost Over Time -- {selection}")
            self.ax_cost.set_ylabel("Cost (₹)")
            self.ax_cost.tick_params(axis="x", labelrotation=30, labelsize=8)

            self.ax_odo.plot(dates, odos, marker="o", color="#5cb85c")
            self.ax_odo.set_title(f"Odometer Progression -- {selection}")
            self.ax_odo.set_ylabel("Km")
            self.ax_odo.tick_params(axis="x", labelrotation=30, labelsize=8)

        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    print("Run 'python app.py' instead -- that's the entry point which shows the "
          "login/create-account screen before opening this window.")
