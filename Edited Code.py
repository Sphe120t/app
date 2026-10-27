import hashlib
import hmac
import re
import secrets
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pandas as pd


# Khwezi Mining H&S and equipment monitoring prototype
APP_DIR = Path(__file__).resolve().parent
USERS_FILE = APP_DIR / "users.csv"
WORKERS_FILE = APP_DIR / "workers.csv"
INCIDENTS_FILE = APP_DIR / "safety_incidents.csv"
EQUIPMENT_FILE = APP_DIR / "equipment.csv"
MAINTENANCE_FILE = APP_DIR / "maintenance_records.csv"

PERMISSIONS = {
    "administrator": {
        "view dashboard", "worker safety data", "safety incidents",
        "equipment data", "maintenance data", "risk management",
        "generate reports", "manage users",
    },
    "safety officer": {
        "view dashboard", "worker safety data", "safety incidents",
        "risk management", "generate reports",
    },
    "mining engineer": {
        "view dashboard", "worker safety data", "safety incidents",
        "equipment data", "maintenance data", "risk management",
        "generate reports",
    },
    "maintenance engineer": {
        "view dashboard", "equipment data", "maintenance data",
        "generate reports",
    },
    "manager": {
        "view dashboard", "worker safety data", "safety incidents",
        "equipment data", "maintenance data", "risk management",
        "generate reports",
    },
}

USER_COLUMNS = ["Username", "Salt", "Password Hash", "Role"]
WORKER_COLUMNS = [
    "Worker ID", "Name", "Department", "Job Role", "Shift",
    "PPE Compliance (%)", "Training Status", "Fatigue Level (1-10)",
    "Safety Observations", "Near Misses", "Previous Incidents",
    "Risk Likelihood", "Risk Consequence", "Risk Score", "Risk Level",
    "Assessment Date",
]
INCIDENT_COLUMNS = [
    "Incident ID", "Date", "Time", "Shift", "Location", "Department",
    "Incident Type", "Severity", "Injury Status", "Lost-Time Injury Status",
    "Cause", "Corrective Action", "Incident Status",
]
EQUIPMENT_COLUMNS = [
    "Equipment ID", "Equipment Type", "Manufacturer", "Operating Hours",
    "Temperature (C)", "Vibration (mm/s)", "Fuel Consumption",
    "Brake Status", "Tyre Status", "Engine Status", "Maintenance Status",
    "Downtime (hours)", "Availability (%)",
]
MAINTENANCE_COLUMNS = [
    "Work Order ID", "Equipment ID", "Reported Date", "Due Date",
    "Maintenance Type", "Priority", "Assigned To", "Status", "Notes",
    "Completed Date",
]

BG = "#f7f3fb"
CARD = "#ffffff"
INK = "#3f365a"
MUTED = "#786f86"
PURPLE = "#8068ad"
GREEN = "#5f9a7d"
GOLD = "#e3bb59"
AMBER = "#e9a847"
RED = "#cf6877"


def risk_classification(likelihood, consequence):
    score = int(likelihood) * int(consequence)
    if score <= 4:
        level = "Low"
    elif score <= 9:
        level = "Medium"
    elif score <= 16:
        level = "High"
    else:
        level = "Critical"
    return score, level


def equipment_condition(temperature, vibration):
    """Apply the prototype thresholds stated in the assignment brief."""
    temperature = float(temperature)
    vibration = float(vibration)
    if temperature > 100 or vibration > 8:
        return "Critical"
    if temperature >= 80 or vibration >= 5:
        return "Warning"
    return "Normal"


def availability_percent(operating_hours, downtime):
    operating_hours = float(operating_hours)
    downtime = float(downtime)
    total = operating_hours + downtime
    return 0.0 if total <= 0 else operating_hours / total * 100


def seed_data():
    """Create small demo CSVs once, so the app opens with usable examples."""
    if not WORKERS_FILE.exists():
        workers = []
        for index in range(1, 11):
            workers.append({
                "Worker ID": f"W-{index:03d}",
                "Name": ["Thabo", "Lerato", "Kagiso", "Mpho", "Neo",
                         "Tshepo", "Boitumelo", "Lesego", "Karabo", "Masego"][index - 1],
                "Department": "Production" if index < 6 else "Engineering",
                "Job Role": "Operator" if index < 6 else "Technician",
                "Shift": "Day" if index % 2 else "Night",
                "PPE Compliance (%)": 95 if index not in (3, 7) else 76,
                "Training Status": "Completed",
                "Fatigue Level (1-10)": 8 if index in (4, 9) else 3,
                "Safety Observations": 1 if index % 3 == 0 else 0,
                "Near Misses": 1 if index % 4 == 0 else 0,
                "Previous Incidents": 0 if index % 3 else 1,
                "Risk Likelihood": 2,
                "Risk Consequence": 2,
                "Risk Score": 4,
                "Risk Level": "Low",
                "Assessment Date": date.today().isoformat(),
            })
        pd.DataFrame(workers, columns=WORKER_COLUMNS).to_csv(
            WORKERS_FILE, index=False, encoding="utf-8-sig"
        )

    if not INCIDENTS_FILE.exists():
        samples = [
            ("Safety Incident", "High", "Production", "Day"),
            ("Safety Incident", "Medium", "Engineering", "Night"),
            ("Near Miss", "Medium", "Production", "Day"),
            ("Near Miss", "High", "Engineering", "Night"),
            ("Observation", "High", "Production", "Day"),
            ("Observation", "Low", "Engineering", "Night"),
            ("Observation", "High", "Production", "Day"),
        ]
        incidents = []
        for index, (kind, severity, department, shift) in enumerate(samples, 1):
            incidents.append({
                "Incident ID": f"INC-{index:03d}",
                "Date": date.today().isoformat(),
                "Time": "08:00",
                "Shift": shift,
                "Location": "Mining area",
                "Department": department,
                "Incident Type": kind,
                "Severity": severity,
                "Injury Status": "No injury",
                "Lost-Time Injury Status": "No",
                "Cause": "Demonstration record",
                "Corrective Action": "Review and monitor",
                "Incident Status": "Open" if severity == "High" else "Closed",
            })
        pd.DataFrame(incidents, columns=INCIDENT_COLUMNS).to_csv(
            INCIDENTS_FILE, index=False, encoding="utf-8-sig"
        )

    if not EQUIPMENT_FILE.exists():
        types = ["Haul Truck", "Loader", "Excavator", "Drilling Machine",
                 "Bulldozer", "Scraper Winch", "Crusher", "Conveyor"]
        equipment = []
        for index, name in enumerate(types, 1):
            temp = [65, 82, 74, 102, 78, 86, 70, 62][index - 1]
            vibration = [3.2, 5.4, 4.1, 9.1, 3.5, 6.2, 4.4, 2.8][index - 1]
            status = "Under maintenance" if index in (3, 5) else "Available"
            operating = 100 - index * 3
            downtime = 5 * index
            equipment.append({
                "Equipment ID": f"EQ-{index:03d}",
                "Equipment Type": name,
                "Manufacturer": "Demo Manufacturer",
                "Operating Hours": operating,
                "Temperature (C)": temp,
                "Vibration (mm/s)": vibration,
                "Fuel Consumption": 25 + index,
                "Brake Status": "Normal",
                "Tyre Status": "Normal",
                "Engine Status": "Warning" if temp >= 80 else "Normal",
                "Maintenance Status": status,
                "Downtime (hours)": downtime,
                "Availability (%)": round(availability_percent(operating, downtime), 2),
            })
        pd.DataFrame(equipment, columns=EQUIPMENT_COLUMNS).to_csv(
            EQUIPMENT_FILE, index=False, encoding="utf-8-sig"
        )

    if not MAINTENANCE_FILE.exists():
        pd.DataFrame(columns=MAINTENANCE_COLUMNS).to_csv(
            MAINTENANCE_FILE, index=False, encoding="utf-8-sig"
        )


class ScrollableFrame(tk.Frame):
    """A vertically scrollable page container for notebook sections."""
    def __init__(self, parent, background=BG):
        super().__init__(parent, bg=background)
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = tk.Frame(self.canvas, bg=background)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

class KhweziMiningApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Khwezi Mining | Health, Safety and Equipment Monitoring")
        self.geometry("1220x820")
        self.minsize(980, 680)
        self.configure(bg=BG)
        self.user = None
        seed_data()

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", padding=6, fieldbackground=CARD)
        style.configure("Treeview", rowheight=27, background=CARD,
                        fieldbackground=CARD, foreground=INK)
        style.configure("Treeview.Heading", background="#eee7f5",
                        foreground=INK, font=("Segoe UI", 9, "bold"))
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background="#eee7f5", foreground=INK,
                        padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#ddd1ef")],
                  foreground=[("selected", INK)])
        self.bind_all("<MouseWheel>", self._scroll_under_pointer, add="+")
        self.bind_all("<Button-4>", self._scroll_under_pointer, add="+")
        self.bind_all("<Button-5>", self._scroll_under_pointer, add="+")
        self.show_login()

    def _scroll_under_pointer(self, event):
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
        except tk.TclError:
            return
        while widget is not None:
            if isinstance(widget, ScrollableFrame):
                if getattr(event, "num", None) == 4:
                    widget.canvas.yview_scroll(-1, "units")
                elif getattr(event, "num", None) == 5:
                    widget.canvas.yview_scroll(1, "units")
                else:
                    widget.canvas.yview_scroll(int(-event.delta / 120), "units")
                return "break"
            widget = getattr(widget, "master", None)

    # -------------------- CSV data access --------------------
    def read_csv(self, path, columns):
        if not path.exists():
            return pd.DataFrame(columns=columns)
        try:
            frame = pd.read_csv(path, dtype=str).fillna("")
            for column in columns:
                if column not in frame.columns:
                    frame[column] = ""
            return frame[columns]
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
            return pd.DataFrame(columns=columns)

    def write_csv(self, path, frame, columns):
        frame = frame.reindex(columns=columns).fillna("")
        frame.to_csv(path, index=False, encoding="utf-8-sig")

    def workers(self):
        if not self.has_permission("worker safety data"):
            return pd.DataFrame(columns=WORKER_COLUMNS)
        return self.read_csv(WORKERS_FILE, WORKER_COLUMNS)

    def incidents(self):
        if not self.has_permission("safety incidents"):
            return pd.DataFrame(columns=INCIDENT_COLUMNS)
        return self.read_csv(INCIDENTS_FILE, INCIDENT_COLUMNS)

    def equipment(self):
        if not self.has_permission("equipment data"):
            return pd.DataFrame(columns=EQUIPMENT_COLUMNS)
        return self.read_csv(EQUIPMENT_FILE, EQUIPMENT_COLUMNS)

    def maintenance_records(self):
        if not self.has_permission("maintenance data"):
            return pd.DataFrame(columns=MAINTENANCE_COLUMNS)
        return self.read_csv(MAINTENANCE_FILE, MAINTENANCE_COLUMNS)

    # -------------------- Account and access control --------------------
    def hash_password(self, password, salt):
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), 300_000
        ).hex()

    def load_users(self):
        if not USERS_FILE.exists():
            return []
        try:
            frame = pd.read_csv(USERS_FILE, dtype=str).fillna("")
            for column in USER_COLUMNS:
                if column not in frame.columns:
                    frame[column] = ""
            return frame[USER_COLUMNS].to_dict(orient="records")
        except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
            return []

    def save_users(self, users):
        pd.DataFrame(users, columns=USER_COLUMNS).to_csv(
            USERS_FILE, index=False, encoding="utf-8-sig"
        )

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_window()
        first_run = not self.load_users()
        outer = tk.Frame(self, bg=BG, padx=28, pady=28)
        outer.pack(fill="both", expand=True)
        card = tk.Frame(outer, bg=CARD, padx=34, pady=30,
                        highlightthickness=1, highlightbackground="#e8e0ef")
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="⛏ KHWEZI MINING", bg=CARD, fg=INK,
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(card,
                 text="Health, Safety and Equipment Monitoring",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 10)).pack(
                     anchor="w", pady=(3, 18))
        tk.Label(card,
                 text="Create administrator account" if first_run
                 else "Sign in to your account",
                 bg=CARD, fg=INK, font=("Segoe UI", 14, "bold")).pack(
                     anchor="w", pady=(0, 12))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        for label, variable, secret in [
            ("Username", self.username_var, False),
            ("Password", self.password_var, True),
        ]:
            tk.Label(card, text=label, bg=CARD, fg=INK,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            ttk.Entry(card, textvariable=variable, show="*" if secret else "",
                      width=36).pack(fill="x", pady=(4, 11))

        if first_run:
            tk.Label(card, text="Confirm password", bg=CARD, fg=INK,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")
            ttk.Entry(card, textvariable=self.confirm_var, show="*",
                      width=36).pack(fill="x", pady=(4, 13))
            action, button_text = self.create_first_admin, "Create administrator"
        else:
            action, button_text = self.login, "Sign in"

        self.button(card, button_text, action).pack(anchor="w", pady=(3, 0))

    def create_first_admin(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or len(password) < 8:
            messagebox.showerror("Invalid account",
                                 "Enter a username and password with at least 8 characters.",
                                 parent=self)
            return
        if password != self.confirm_var.get():
            messagebox.showerror("Password mismatch", "The passwords do not match.",
                                 parent=self)
            return
        salt = secrets.token_hex(16)
        self.save_users([{
            "Username": username, "Salt": salt,
            "Password Hash": self.hash_password(password, salt),
            "Role": "administrator",
        }])
        self.login()

    def login(self):
        username = self.username_var.get().strip()
        account = next((user for user in self.load_users()
                        if user["Username"].casefold() == username.casefold()), None)
        if account is None:
            messagebox.showerror("Sign-in failed", "Username or password is incorrect.",
                                 parent=self)
            return
        entered = self.hash_password(self.password_var.get(), account["Salt"])
        if not hmac.compare_digest(entered, account["Password Hash"]):
            messagebox.showerror("Sign-in failed", "Username or password is incorrect.",
                                 parent=self)
            return
        if account["Role"] not in PERMISSIONS:
            messagebox.showerror("Account error", "This account has an invalid role.",
                                 parent=self)
            return
        self.user = account
        self.build_app()

    def logout(self):
        self.user = None
        self.show_login()

    def has_permission(self, permission):
        return (self.user is not None
                and permission in PERMISSIONS.get(self.user["Role"], set()))

    def add_user(self):
        if not self.has_permission("manage users"):
            messagebox.showerror("Access denied", "Only administrators can manage users.",
                                 parent=self)
            return
        window = tk.Toplevel(self)
        window.title("Create User Account")
        window.geometry("420x390")
        window.configure(bg=BG)
        window.transient(self)
        window.grab_set()
        card = tk.Frame(window, bg=CARD, padx=20, pady=18)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        username, password = tk.StringVar(), tk.StringVar()
        role = tk.StringVar(value="safety officer")
        self.form_entry(card, "Username", username)
        self.form_entry(card, "Temporary password (8+ characters)", password,
                        secret=True)
        tk.Label(card, text="Role", bg=CARD, fg=INK,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(9, 3))
        ttk.Combobox(card, textvariable=role, values=list(PERMISSIONS),
                     state="readonly").pack(fill="x")

        def save():
            name, pwd = username.get().strip(), password.get()
            users = self.load_users()
            if not name or len(pwd) < 8:
                messagebox.showerror("Invalid account",
                                     "Enter a username and password of at least 8 characters.",
                                     parent=window)
                return
            if any(item["Username"].casefold() == name.casefold() for item in users):
                messagebox.showerror("Duplicate username", "That username already exists.",
                                     parent=window)
                return
            salt = secrets.token_hex(16)
            users.append({
                "Username": name, "Salt": salt,
                "Password Hash": self.hash_password(pwd, salt),
                "Role": role.get(),
            })
            self.save_users(users)
            messagebox.showinfo("Account created", f"Created {name} as {role.get()}.",
                                parent=window)
            window.destroy()

        self.button(card, "Create account", save).pack(anchor="w", pady=14)

    # -------------------- Shared user interface helpers --------------------
    def button(self, parent, text, command, color=PURPLE):
        return tk.Button(
            parent, text=text, command=command, bg=color, fg="white",
            activebackground="#6e579b", activeforeground="white",
            relief="flat", padx=14, pady=8, cursor="hand2",
            font=("Segoe UI", 9, "bold"),
        )

    def form_entry(self, parent, label, variable, choices=None, secret=False):
        tk.Label(parent, text=label, bg=CARD, fg=INK,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(7, 2))
        if choices:
            widget = ttk.Combobox(parent, textvariable=variable, values=choices,
                                  state="readonly")
        else:
            widget = ttk.Entry(parent, textvariable=variable,
                               show="*" if secret else "")
        widget.pack(fill="x")
        return widget

    def make_table(self, parent, columns, headings=None, widths=None, height=12):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="both", expand=True)
        table = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        headings = headings or {column: column.upper() for column in columns}
        widths = widths or {}
        for column in columns:
            table.heading(column, text=headings.get(column, column.upper()))
            table.column(column, width=widths.get(column, 130), minwidth=80,
                         anchor="w", stretch=True)
        vertical = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        table.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return table

    def replace_table_rows(self, table, records, columns):
        table.delete(*table.get_children())
        for record in records:
            table.insert("", "end", values=[record.get(column, "") for column in columns])

    def header(self, parent, title, subtitle=""):
        tk.Label(parent, text=title, bg=BG, fg=INK,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(parent, text=subtitle, bg=BG, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 10))

    # -------------------- Role-filtered navigation --------------------
    def build_app(self):
        self.clear_window()
        header = tk.Frame(self, bg=INK, padx=22, pady=13)
        header.pack(fill="x")
        tk.Label(header, text="⛏ KHWEZI MINING", bg=INK, fg="white",
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Label(header,
                 text=f"Signed in: {self.user['Username']}  ·  {self.user['Role'].title()}",
                 bg=INK, fg="#eee8f6", font=("Segoe UI", 9)).pack(side="left", padx=22)
        tk.Button(header, text="Sign out", command=self.logout,
                  bg="#eee8f6", fg=INK, relief="flat", padx=12, pady=6,
                  cursor="hand2").pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(12, 4))
        self.allowed_tabs = []
        tab_builders = [
            ("Access Control", "view dashboard", self.build_access),
            ("Dashboard", "view dashboard", self.build_dashboard),
            ("Worker Safety", "worker safety data", self.build_worker_safety),
            ("Safety Incidents", "safety incidents", self.build_incidents),
            ("Equipment", "equipment data", self.build_equipment),
            ("Maintenance", "maintenance data", self.build_maintenance),
            ("Risk Assessment", "risk management", self.build_risk),
            ("Reports", "generate reports", self.build_reports),
        ]
        for title, permission, builder in tab_builders:
            if self.has_permission(permission):
                page = ScrollableFrame(self.tabs, background=BG)
                self.tabs.add(page, text=title)
                page.content.configure(padx=16, pady=12)
                self.allowed_tabs.append((page, title, builder))
                builder(page.content)

        navigation = tk.Frame(self, bg=BG, padx=16, pady=8)
        navigation.pack(fill="x")
        self.navigation_status = tk.Label(
            navigation, text="", bg=BG, fg=INK,
            font=("Segoe UI", 9, "bold"), anchor="w",
        )
        self.navigation_status.pack(side="left", fill="x", expand=True)
        self.next_button = self.button(navigation, "Next →", self.next_access)
        self.next_button.pack(side="right")
        if self.has_permission("manage users"):
            tk.Button(navigation, text="Add user", command=self.add_user,
                      bg="#e7e0f1", fg=INK, relief="flat", padx=12, pady=8,
                      cursor="hand2").pack(side="right", padx=8)
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        if self.allowed_tabs:
            self.tabs.select(self.allowed_tabs[0][0])
        self.update_navigation_status()

    def update_navigation_status(self, _event=None):
        if not self.allowed_tabs:
            return
        selected = self.tabs.select()
        index = next((i for i, (tab, _, _) in enumerate(self.allowed_tabs)
                      if str(tab) == selected), 0)
        current_title = self.allowed_tabs[index][1]
        next_title = self.allowed_tabs[(index + 1) % len(self.allowed_tabs)][1]
        self.navigation_status.config(
            text=f"✨ {self.user['Role'].title()} · {current_title}"
        )
        self.next_button.config(text=f"Next: {next_title}  →")

    def on_tab_changed(self, event=None):
        self.update_navigation_status(event)
        if not self.allowed_tabs:
            return
        selected = self.tabs.select()
        current = next((entry for entry in self.allowed_tabs
                        if str(entry[0]) == selected), None)
        if current is None:
            return
        page, title, builder = current
        if title == "Dashboard":
            for child in page.content.winfo_children():
                child.destroy()
            builder(page.content)
        elif title == "Maintenance":
            self.refresh_maintenance_table()
        elif title == "Reports":
            self.generate_summary()

    def next_access(self):
        if not self.allowed_tabs:
            return
        selected = self.tabs.select()
        index = next((i for i, (tab, _, _) in enumerate(self.allowed_tabs)
                      if str(tab) == selected), -1)
        self.tabs.select(self.allowed_tabs[(index + 1) % len(self.allowed_tabs)][0])
        self.update_navigation_status()

    def build_access(self, parent):
        self.header(parent, "Access Control",
                    "Your account can open only the sections listed as Allowed. Use Next to continue.")
        columns = ["Function", "Access"]
        table = self.make_table(parent, columns, height=12,
                                widths={"Function": 380, "Access": 150})
        functions = sorted({item for permissions in PERMISSIONS.values() for item in permissions})
        rows = [{
            "Function": function.title(),
            "Access": "Allowed" if self.has_permission(function) else "No access",
        } for function in functions]
        self.replace_table_rows(table, rows, columns)

    # -------------------- Dashboard and alerts --------------------
    def collect_alerts(self):
        alerts = []
        if self.has_permission("worker safety data"):
            for _, row in self.workers().iterrows():
                worker = row["Worker ID"]
                if self.number(row["PPE Compliance (%)"]) < 80:
                    alerts.append(f"WARNING · Worker {worker}: PPE compliance is below 80%.")
                if self.number(row["Fatigue Level (1-10)"]) >= 8:
                    alerts.append(f"WARNING · Worker {worker}: high fatigue level recorded.")
                score = self.number(row["Risk Score"])
                if score >= 17:
                    alerts.append(f"CRITICAL · Worker {worker}: critical safety risk (score {score}).")
                elif score >= 10:
                    alerts.append(f"WARNING · Worker {worker}: high safety risk (score {score}).")
        if self.has_permission("safety incidents"):
            for _, row in self.incidents().iterrows():
                severity = row["Severity"].strip().lower()
                kind = row["Incident Type"].strip().lower()
                if severity == "critical":
                    alerts.append(f"CRITICAL · Incident {row['Incident ID']}: critical severity.")
                if kind == "observation" and severity in {"high", "critical"}:
                    alerts.append(f"WARNING · Incident {row['Incident ID']}: high-risk observation.")
        if self.has_permission("equipment data"):
            for _, row in self.equipment().iterrows():
                condition = equipment_condition(row["Temperature (C)"], row["Vibration (mm/s)"])
                if condition != "Normal":
                    alerts.append(
                        f"{condition.upper()} · Equipment {row['Equipment ID']}: "
                        f"temperature {row['Temperature (C)']}°C, vibration {row['Vibration (mm/s)']} mm/s."
                    )
                downtime = self.number(row["Downtime (hours)"])
                if downtime > 20:
                    alerts.append(f"WARNING · Equipment {row['Equipment ID']}: downtime is above 20 hours.")
                maintenance = row["Maintenance Status"].strip().lower()
                if maintenance == "overdue":
                    alerts.append(f"CRITICAL · Equipment {row['Equipment ID']}: maintenance is overdue.")
        if self.has_permission("maintenance data"):
            today = date.today()
            for _, row in self.maintenance_records().iterrows():
                if row["Status"].strip().casefold() == "completed":
                    continue
                try:
                    due_date = datetime.strptime(row["Due Date"], "%Y-%m-%d").date()
                except ValueError:
                    continue
                if due_date < today:
                    alerts.append(f"CRITICAL · Work order {row['Work Order ID']} for {row['Equipment ID']} is overdue.")
                elif due_date == today:
                    alerts.append(f"WARNING · Work order {row['Work Order ID']} for {row['Equipment ID']} is due today.")
        return alerts

    @staticmethod
    def number(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def build_dashboard(self, parent):
        dashboard_bg, card_bg = "#faf7ff", CARD
        gold, text, muted = GOLD, INK, MUTED
        green, amber, red = "#70ae8d", AMBER, RED
        parent.configure(bg=dashboard_bg)
        tk.Label(parent, text="Mining Monitoring Dashboard", bg=dashboard_bg,
                 fg=text, font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Frame(parent, bg=gold, height=3).pack(fill="x", pady=(4, 10))

        workers = self.workers()
        incidents = self.incidents()
        equipment = self.equipment()
        metrics = []
        if self.has_permission("worker safety data"):
            ppe_values = pd.to_numeric(workers["PPE Compliance (%)"], errors="coerce")
            ppe_average = ppe_values.mean() if not ppe_values.empty else 0
            metrics.extend([
                ("Total workers", len(workers)),
                ("PPE compliance", f"{ppe_average:.1f}%"),
                ("High fatigue workers", sum(
                    self.number(v) >= 8 for v in workers["Fatigue Level (1-10)"])),
                ("High-risk observations", sum(
                    (incidents["Incident Type"].str.lower() == "observation")
                    & incidents["Severity"].str.lower().isin(["high", "critical"])
                ) if self.has_permission("safety incidents") else "Restricted"),
            ])
        if self.has_permission("safety incidents"):
            metrics.extend([
                ("Total safety incidents", sum(incidents["Incident Type"].str.lower() == "safety incident")),
                ("Near misses", sum(incidents["Incident Type"].str.lower() == "near miss")),
                ("High/Critical incidents", sum(incidents["Severity"].str.lower().isin(["high", "critical"]))),
                ("Open critical incidents", sum(
                    (incidents["Severity"].str.lower() == "critical")
                    & (incidents["Incident Status"].str.lower() == "open")
                )),
            ])
        if self.has_permission("equipment data"):
            availability = pd.to_numeric(equipment["Availability (%)"], errors="coerce")
            condition_values = [equipment_condition(row["Temperature (C)"], row["Vibration (mm/s)"])
                                for _, row in equipment.iterrows()]
            metrics.extend([
                ("Total equipment", len(equipment)),
                ("Equipment available", sum(equipment["Maintenance Status"].str.lower() == "available")),
                ("Under maintenance", sum(equipment["Maintenance Status"].str.lower() == "under maintenance")),
                ("Avg availability", f"{availability.mean() if not availability.empty else 0:.1f}%"),
                ("Critical equipment alerts", condition_values.count("Critical")),
            ])

        cards = tk.Frame(parent, bg=dashboard_bg)
        cards.pack(fill="x", pady=(0, 7))
        for column in range(4):
            cards.columnconfigure(column, weight=1, uniform="metrics")
        for index, (label, value) in enumerate(metrics):
            row, col = divmod(index, 4)
            card = tk.Frame(cards, bg=card_bg, padx=11, pady=8,
                            highlightthickness=1, highlightbackground="#e9e1ef")
            card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            tk.Frame(card, bg=gold, width=4).pack(side="left", fill="y", padx=(0, 8))
            content = tk.Frame(card, bg=card_bg)
            content.pack(side="left", fill="both", expand=True)
            tk.Label(content, text=label, bg=card_bg, fg=muted,
                     font=("Segoe UI", 8)).pack(anchor="w")
            tk.Label(content, text=str(value), bg=card_bg, fg=text,
                     font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(2, 0))

        chart_row = tk.Frame(parent, bg=dashboard_bg)
        chart_row.pack(fill="both", expand=True, pady=(3, 0))
        chart_row.columnconfigure(0, weight=1)
        chart_row.columnconfigure(1, weight=1)
        line_panel = tk.Frame(chart_row, bg=dashboard_bg)
        line_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        pie_panel = tk.Frame(chart_row, bg=dashboard_bg)
        pie_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(line_panel, text="Incidents per month", bg=dashboard_bg, fg=text,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(pie_panel, text="Equipment condition", bg=dashboard_bg, fg=text,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))
        line = tk.Canvas(line_panel, height=205, bg=dashboard_bg, highlightthickness=0)
        line.pack(fill="both", expand=True)
        pie = tk.Canvas(pie_panel, height=205, bg=dashboard_bg, highlightthickness=0)
        pie.pack(fill="both", expand=True)

        if self.has_permission("safety incidents"):
            dates = pd.to_datetime(incidents["Date"], errors="coerce")
            dated = incidents.loc[dates.notna()].copy()
            dated["Month"] = dates[dates.notna()].dt.to_period("M").astype(str)
            counts = dated.groupby("Month").size().sort_index().tail(6)
            if len(counts):
                width, height = 470, 210
                left, right, top, bottom = 40, width - 18, 16, height - 30
                maximum = max(int(counts.max()), 1)
                points = []
                step = (right - left) / max(len(counts) - 1, 1)
                if len(counts) == 1:
                    step = 0
                for tick in range(0, maximum + 1, max(1, maximum // 4)):
                    y = bottom - tick / maximum * (bottom - top)
                    line.create_line(left, y, right, y, fill="#e3ddea", dash=(2, 3))
                for i, (month, count) in enumerate(counts.items()):
                    x = left + i * step if len(counts) > 1 else (left + right) / 2
                    y = bottom - int(count) / maximum * (bottom - top)
                    points.extend((x, y))
                    line.create_text(x, bottom + 13, text=month[-2:], fill=muted,
                                     font=("Segoe UI", 8))
                    line.create_text(x, y - 10, text=str(count), fill=text,
                                     font=("Segoe UI", 8, "bold"))
                if len(points) >= 4:
                    line.create_line(*points, fill=PURPLE, width=3, smooth=True)
                for i in range(len(counts)):
                    x, y = points[i * 2:i * 2 + 2]
                    line.create_oval(x - 4, y - 4, x + 4, y + 4,
                                     fill=PURPLE, outline=CARD)
            else:
                line.create_text(220, 100, text="Add dated incidents to see a trend.",
                                 fill=muted)
        else:
            line.create_text(220, 100, text="Incident data restricted for this role.",
                             fill=muted)

        if self.has_permission("equipment data"):
            conditions = [equipment_condition(row["Temperature (C)"], row["Vibration (mm/s)"])
                          for _, row in equipment.iterrows()]
            condition_counts = {
                "Normal": conditions.count("Normal"),
                "Warning": conditions.count("Warning"),
                "Critical": conditions.count("Critical"),
            }
            colors = {"Normal": green, "Warning": amber, "Critical": red}
            total = sum(condition_counts.values())
            angle = 0
            for label in ("Normal", "Warning", "Critical"):
                amount = condition_counts[label]
                if amount and total:
                    extent = 360 * amount / total
                    pie.create_arc(20, 12, 205, 197, start=angle, extent=extent,
                                   fill=colors[label], outline=dashboard_bg,
                                   width=2, style="pieslice")
                    angle += extent
            pie.create_text(112, 105, text=f"{total}\nunits", fill=text,
                            font=("Segoe UI", 12, "bold"))
            for i, label in enumerate(("Normal", "Warning", "Critical")):
                y = 65 + i * 31
                pie.create_rectangle(235, y, 250, y + 15, fill=colors[label], outline="")
                pie.create_text(260, y + 8, text=f"{label}: {condition_counts[label]}",
                                anchor="w", fill=text, font=("Segoe UI", 9))
        else:
            pie.create_text(220, 100, text="Equipment data restricted for this role.",
                            fill=muted)

        alerts = self.collect_alerts()
        alert_frame = tk.LabelFrame(parent, text=f"Current alerts ({len(alerts)})",
                                    bg=CARD, fg=INK, padx=10, pady=6,
                                    font=("Segoe UI", 9, "bold"))
        alert_frame.pack(fill="x", pady=(6, 0))
        alert_text = tk.Text(alert_frame, height=min(max(len(alerts), 2), 4),
                             bg=CARD, fg=INK, relief="flat", wrap="word")
        alert_text.pack(fill="x")
        alert_text.insert("1.0", "\n".join(alerts) if alerts else
                          "No active alerts in the records available to your role.")
        alert_text.configure(state="disabled")

    # -------------------- Worker safety records --------------------
    def build_worker_safety(self, parent):
        self.header(parent, "Worker Safety Monitoring",
                    "Record worker indicators and review saved assessments.")
        actions = tk.Frame(parent, bg=BG)
        actions.pack(fill="x", pady=(0, 8))
        self.button(actions, "+ Add worker assessment",
                    self.add_worker_assessment).pack(side="left")
        self.button(actions, "Refresh", self.refresh_worker_table,
                    color=GREEN).pack(side="left", padx=7)
        tk.Label(parent,
                 text="PPE below 80% and fatigue levels of 8 or higher generate dashboard alerts.",
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 6))
        self.worker_table = self.make_table(parent, WORKER_COLUMNS, height=13)
        self.refresh_worker_table()

    def refresh_worker_table(self):
        if not hasattr(self, "worker_table") or not self.has_permission("worker safety data"):
            return
        self.replace_table_rows(self.worker_table,
                                self.workers().to_dict(orient="records"), WORKER_COLUMNS)

    def add_worker_assessment(self):
        if not self.has_permission("worker safety data"):
            messagebox.showerror("Access denied", "Your role cannot record worker safety data.", parent=self)
            return
        window = tk.Toplevel(self)
        window.title("Add Worker Safety Assessment")
        window.geometry("650x720")
        window.configure(bg=BG)
        window.transient(self)
        window.grab_set()
        canvas = tk.Canvas(window, bg=BG, highlightthickness=0)
        scroll = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg=CARD, padx=18, pady=14)
        canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=14)
        scroll.pack(side="right", fill="y", padx=(0, 14), pady=14)

        fields = [
            ("Worker ID", ""), ("Name", ""), ("Department", "Production"),
            ("Job Role", "Operator"), ("Shift", "Day"),
            ("PPE Compliance (%)", "95"), ("Training Status", "Completed"),
            ("Fatigue Level (1-10)", "3"), ("Safety Observations", "0"),
            ("Near Misses", "0"), ("Previous Incidents", "0"),
            ("Risk Likelihood (1-5)", "1"), ("Risk Consequence (1-5)", "1"),
        ]
        variables = {}
        choices = {
            "Shift": ["Day", "Night"],
            "Training Status": ["Completed", "Expired", "Not Completed"],
        }
        for label, initial in fields:
            var = tk.StringVar(value=initial)
            variables[label] = var
            if label in choices:
                self.form_entry(form, label, var, choices[label])
            else:
                self.form_entry(form, label, var)

        def save():
            vals = {label: var.get().strip() for label, var in variables.items()}
            if not vals["Worker ID"] or not vals["Name"]:
                messagebox.showerror("Missing information", "Worker ID and name are required.", parent=window)
                return
            df = self.workers()
            if (df["Worker ID"].str.casefold() == vals["Worker ID"].casefold()).any():
                messagebox.showerror("Duplicate ID", "That Worker ID already exists.", parent=window)
                return
            try:
                ppe = float(vals["PPE Compliance (%)"])
                fatigue = float(vals["Fatigue Level (1-10)"])
                observations = int(vals["Safety Observations"])
                near_misses = int(vals["Near Misses"])
                previous = int(vals["Previous Incidents"])
                likelihood = int(vals["Risk Likelihood (1-5)"])
                consequence = int(vals["Risk Consequence (1-5)"])
                if not 0 <= ppe <= 100 or not 1 <= fatigue <= 10:
                    raise ValueError("PPE must be 0-100 and fatigue must be 1-10.")
                if min(observations, near_misses, previous) < 0:
                    raise ValueError("Counts cannot be negative.")
                if not 1 <= likelihood <= 5 or not 1 <= consequence <= 5:
                    raise ValueError("Likelihood and consequence must be from 1 to 5.")
            except ValueError as error:
                messagebox.showerror("Invalid assessment", str(error), parent=window)
                return
            score, level = risk_classification(likelihood, consequence)
            row = {
                "Worker ID": vals["Worker ID"], "Name": vals["Name"],
                "Department": vals["Department"], "Job Role": vals["Job Role"],
                "Shift": vals["Shift"], "PPE Compliance (%)": ppe,
                "Training Status": vals["Training Status"],
                "Fatigue Level (1-10)": fatigue,
                "Safety Observations": observations, "Near Misses": near_misses,
                "Previous Incidents": previous, "Risk Likelihood": likelihood,
                "Risk Consequence": consequence, "Risk Score": score,
                "Risk Level": level, "Assessment Date": date.today().isoformat(),
            }
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            self.write_csv(WORKERS_FILE, df, WORKER_COLUMNS)
            self.refresh_worker_table()
            window.destroy()
            messagebox.showinfo("Saved", f"Assessment saved for {row['Name']}.", parent=self)

        self.button(form, "Save worker assessment", save).pack(anchor="w", pady=14)

    # -------------------- Safety incident database --------------------
    def build_incidents(self, parent):
        self.header(parent, "Safety Incident Database",
                    "Add, search, filter and analyse incident records.")
        tools = tk.Frame(parent, bg=CARD, padx=8, pady=8)
        tools.pack(fill="x", pady=(0, 8))
        self.incident_search = tk.StringVar()
        self.incident_filter_field = tk.StringVar(value="All")
        self.incident_filter_value = tk.StringVar()
        tk.Label(tools, text="Search", bg=CARD, fg=INK).pack(side="left")
        search = ttk.Entry(tools, textvariable=self.incident_search, width=20)
        search.pack(side="left", padx=5)
        search.bind("<KeyRelease>", lambda _e: self.refresh_incident_table())
        ttk.Combobox(tools, textvariable=self.incident_filter_field,
                     values=["All", "Shift", "Department", "Severity", "Incident Type", "Incident Status"],
                     state="readonly", width=18).pack(side="left", padx=5)
        ttk.Entry(tools, textvariable=self.incident_filter_value, width=16).pack(side="left")
        self.button(tools, "Apply filter", self.refresh_incident_table,
                    color=GREEN).pack(side="left", padx=5)
        self.button(tools, "Clear", self.clear_incident_filters,
                    color="#9b8eb1").pack(side="left")
        self.button(tools, "+ Add incident", self.add_incident).pack(side="right")

        table_cols = ["Incident ID", "Date", "Time", "Shift", "Location",
                      "Department", "Incident Type", "Severity", "Injury Status",
                      "Lost-Time Injury Status", "Cause", "Corrective Action", "Incident Status"]
        self.incident_table = self.make_table(parent, table_cols, height=14)
        bottom = tk.Frame(parent, bg=BG)
        bottom.pack(fill="x", pady=7)
        self.incident_count = tk.Label(bottom, text="", bg=BG, fg=MUTED)
        self.incident_count.pack(side="left")
        self.button(bottom, "Analysis summary", self.incident_analysis,
                    color=GREEN).pack(side="right")
        self.refresh_incident_table()

    def refresh_incident_table(self):
        if not hasattr(self, "incident_table") or not self.has_permission("safety incidents"):
            return
        df = self.incidents()
        original_count = len(df)
        term = self.incident_search.get().strip().casefold()
        if term:
            mask = df.apply(lambda row: row.astype(str).str.casefold().str.contains(term, regex=False).any(), axis=1)
            df = df[mask]
        field = self.incident_filter_field.get()
        value = self.incident_filter_value.get().strip().casefold()
        if field != "All" and value:
            df = df[df[field].str.casefold() == value]
        self.replace_table_rows(self.incident_table, df.to_dict(orient="records"), INCIDENT_COLUMNS)
        self.incident_count.config(text=f"Showing {len(df)} of {original_count} incidents")

    def clear_incident_filters(self):
        self.incident_search.set("")
        self.incident_filter_field.set("All")
        self.incident_filter_value.set("")
        self.refresh_incident_table()

    def add_incident(self):
        if not self.has_permission("safety incidents"):
            messagebox.showerror("Access denied", "Your role cannot add safety incidents.", parent=self)
            return
        window = tk.Toplevel(self)
        window.title("Add Safety Incident")
        window.geometry("660x760")
        window.configure(bg=BG)
        window.transient(self)
        window.grab_set()
        form = tk.Frame(window, bg=CARD, padx=18, pady=14)
        form.pack(fill="both", expand=True, padx=16, pady=16)
        definitions = [
            ("Date", date.today().isoformat(), None), ("Time", datetime.now().strftime("%H:%M"), None),
            ("Shift", "Day", ["Day", "Night"]), ("Location", "", None),
            ("Department", "", None), ("Incident Type", "Safety Incident",
             ["Safety Incident", "Near Miss", "Observation", "Unsafe Condition"]),
            ("Severity", "Low", ["Low", "Medium", "High", "Critical"]),
            ("Injury Status", "No injury", ["No injury", "Injury"]),
            ("Lost-Time Injury Status", "No", ["No", "Yes"]),
            ("Cause", "", None), ("Corrective Action", "", None),
            ("Incident Status", "Open", ["Open", "Under investigation", "Closed"]),
        ]
        variables = {}
        for label, initial, options in definitions:
            variable = tk.StringVar(value=initial)
            variables[label] = variable
            self.form_entry(form, label, variable, options)

        def save():
            vals = {key: variable.get().strip() for key, variable in variables.items()}
            if not vals["Location"] or not vals["Department"]:
                messagebox.showerror("Missing information", "Location and department are required.", parent=window)
                return
            try:
                datetime.strptime(vals["Date"], "%Y-%m-%d")
                datetime.strptime(vals["Time"], "%H:%M")
            except ValueError:
                messagebox.showerror("Invalid date/time", "Use YYYY-MM-DD and HH:MM formats.", parent=window)
                return
            df = self.incidents()
            number = 1
            existing = set(df["Incident ID"])
            while f"INC-{number:03d}" in existing:
                number += 1
            record = {column: "" for column in INCIDENT_COLUMNS}
            record.update(vals)
            record["Incident ID"] = f"INC-{number:03d}"
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
            self.write_csv(INCIDENTS_FILE, df, INCIDENT_COLUMNS)
            self.refresh_incident_table()
            window.destroy()
            messagebox.showinfo("Saved", f"Incident {record['Incident ID']} recorded.", parent=self)

        self.button(form, "Save incident", save).pack(anchor="w", pady=12)

    def incident_analysis(self):
        if not self.has_permission("safety incidents"):
            return
        df = self.incidents()
        if df.empty:
            messagebox.showinfo("Incident analysis", "No incidents are recorded.", parent=self)
            return
        summary = [f"Total incidents: {len(df)}", "", "By department:"]
        summary.extend(f"  {key}: {value}" for key, value in df.groupby("Department").size().sort_values(ascending=False).items())
        summary.extend(["", "By shift:"])
        summary.extend(f"  {key}: {value}" for key, value in df.groupby("Shift").size().sort_values(ascending=False).items())
        summary.extend(["", "By incident type:"])
        summary.extend(f"  {key}: {value}" for key, value in df.groupby("Incident Type").size().sort_values(ascending=False).items())
        summary.extend(["", "By severity:"])
        summary.extend(f"  {key}: {value}" for key, value in df.groupby("Severity").size().items())
        messagebox.showinfo("Incident analysis", "\n".join(summary), parent=self)

    # -------------------- Equipment and maintenance --------------------
    def build_equipment(self, parent):
        self.header(parent, "Equipment Database and Condition Monitoring",
                    "Search, record and monitor equipment readings. Prototype thresholds only.")
        toolbar = tk.Frame(parent, bg=CARD, padx=8, pady=8)
        toolbar.pack(fill="x", pady=(0, 8))
        self.equipment_search = tk.StringVar()
        self.equipment_filter = tk.StringVar(value="All")
        tk.Label(toolbar, text="Search", bg=CARD, fg=INK).pack(side="left")
        entry = ttk.Entry(toolbar, textvariable=self.equipment_search, width=22)
        entry.pack(side="left", padx=5)
        entry.bind("<KeyRelease>", lambda _e: self.refresh_equipment_table())
        ttk.Combobox(toolbar, textvariable=self.equipment_filter,
                     values=["All", "Available", "Due", "Overdue", "Under maintenance"],
                     state="readonly", width=20).pack(side="left", padx=5)
        self.button(toolbar, "Apply", self.refresh_equipment_table,
                    color=GREEN).pack(side="left", padx=5)
        self.button(toolbar, "+ Add equipment", self.add_equipment).pack(side="right")
        cols = EQUIPMENT_COLUMNS
        self.equipment_table = self.make_table(parent, cols, height=14)
        self.equipment_count = tk.Label(parent, text="", bg=BG, fg=MUTED)
        self.equipment_count.pack(anchor="w", pady=6)
        self.refresh_equipment_table()

    def refresh_equipment_table(self):
        if not hasattr(self, "equipment_table") or not self.has_permission("equipment data"):
            return
        df = self.equipment()
        total = len(df)
        term = self.equipment_search.get().strip().casefold()
        if term:
            mask = df.apply(lambda row: row.astype(str).str.casefold().str.contains(term, regex=False).any(), axis=1)
            df = df[mask]
        selected = self.equipment_filter.get()
        if selected != "All":
            df = df[df["Maintenance Status"].str.casefold() == selected.casefold()]
        self.replace_table_rows(self.equipment_table, df.to_dict(orient="records"), EQUIPMENT_COLUMNS)
        self.equipment_count.config(text=f"Showing {len(df)} of {total} equipment records")

    def add_equipment(self):
        if not self.has_permission("equipment data"):
            messagebox.showerror("Access denied", "Your role cannot add equipment.", parent=self)
            return
        window = tk.Toplevel(self)
        window.title("Add Equipment")
        window.geometry("650x760")
        window.configure(bg=BG)
        window.transient(self)
        window.grab_set()
        form = tk.Frame(window, bg=CARD, padx=18, pady=14)
        form.pack(fill="both", expand=True, padx=16, pady=16)
        definitions = [
            ("Equipment ID", "", None),
            ("Equipment Type", "Haul Truck", ["Haul Truck", "Loader", "Excavator", "Drilling Machine", "Bulldozer", "Scraper Winch", "Crusher", "Conveyor", "Other"]),
            ("Manufacturer", "", None), ("Operating Hours", "0", None),
            ("Temperature (C)", "60", None), ("Vibration (mm/s)", "3", None),
            ("Fuel Consumption", "0", None),
            ("Brake Status", "Normal", ["Normal", "Warning", "Fault"]),
            ("Tyre Status", "Normal", ["Normal", "Warning", "Fault"]),
            ("Engine Status", "Normal", ["Normal", "Warning", "Fault"]),
            ("Maintenance Status", "Available", ["Available", "Due", "Overdue", "Under maintenance"]),
            ("Downtime (hours)", "0", None),
        ]
        variables = {}
        for label, initial, options in definitions:
            variable = tk.StringVar(value=initial)
            variables[label] = variable
            self.form_entry(form, label, variable, options)

        def save():
            vals = {key: variable.get().strip() for key, variable in variables.items()}
            if not vals["Equipment ID"]:
                messagebox.showerror("Missing ID", "Equipment ID is required.", parent=window)
                return
            df = self.equipment()
            if (df["Equipment ID"].str.casefold() == vals["Equipment ID"].casefold()).any():
                messagebox.showerror("Duplicate ID", "That Equipment ID already exists.", parent=window)
                return
            try:
                operating = float(vals["Operating Hours"])
                temp = float(vals["Temperature (C)"])
                vibration = float(vals["Vibration (mm/s)"])
                fuel = float(vals["Fuel Consumption"])
                downtime = float(vals["Downtime (hours)"])
                if min(operating, temp, vibration, fuel, downtime) < 0:
                    raise ValueError("Numeric readings cannot be negative.")
            except ValueError as error:
                messagebox.showerror("Invalid readings", str(error), parent=window)
                return
            record = {column: "" for column in EQUIPMENT_COLUMNS}
            record.update(vals)
            record["Availability (%)"] = round(availability_percent(operating, downtime), 2)
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
            self.write_csv(EQUIPMENT_FILE, df, EQUIPMENT_COLUMNS)
            self.refresh_equipment_table()
            window.destroy()
            messagebox.showinfo("Saved", f"Equipment {record['Equipment ID']} saved.", parent=self)

        self.button(form, "Save equipment", save).pack(anchor="w", pady=12)

    def build_maintenance(self, parent):
        self.header(parent, "Maintenance Monitoring",
                    "Create maintenance work orders, monitor due dates and identify equipment needing review.")
        actions = tk.Frame(parent, bg=BG)
        actions.pack(fill="x", pady=(0, 8))
        self.button(actions, "+ Create work order", self.add_maintenance_order).pack(side="left")
        self.button(actions, "Mark selected complete", self.complete_maintenance_order,
                    color=GREEN).pack(side="left", padx=8)
        self.button(actions, "Refresh", self.refresh_maintenance_table,
                    color="#9b8eb1").pack(side="left")

        tk.Label(parent, text="Maintenance work orders", bg=BG, fg=INK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(4, 5))
        self.maintenance_table = self.make_table(
            parent, MAINTENANCE_COLUMNS, height=8,
            widths={"Work Order ID": 120, "Equipment ID": 120,
                    "Reported Date": 110, "Due Date": 110,
                    "Maintenance Type": 150, "Priority": 90,
                    "Assigned To": 130, "Status": 100, "Notes": 200,
                    "Completed Date": 110},
        )
        tk.Label(parent, text="Equipment requiring review", bg=BG, fg=INK,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(12, 5))
        self.maintenance_equipment_table = self.make_table(
            parent, ["Equipment ID", "Equipment Type", "Maintenance Status",
                     "Downtime (hours)", "Availability (%)", "Condition"], height=7
        )
        self.maintenance_summary = tk.Label(parent, text="", bg=BG, fg=INK,
                                            font=("Segoe UI", 10, "bold"))
        self.maintenance_summary.pack(anchor="w", pady=8)
        self.refresh_maintenance_table()

    def refresh_maintenance_table(self):
        if not hasattr(self, "maintenance_table") or not self.has_permission("maintenance data"):
            return
        orders = self.maintenance_records()
        self.replace_table_rows(self.maintenance_table,
                                orders.to_dict(orient="records"), MAINTENANCE_COLUMNS)
        df = self.equipment()
        subset = df[
            df["Maintenance Status"].str.lower().isin(["due", "overdue", "under maintenance"])
            | (pd.to_numeric(df["Downtime (hours)"], errors="coerce") > 20)
            | (pd.to_numeric(df["Availability (%)"], errors="coerce") < 80)
        ].copy()
        rows = []
        for _, item in subset.iterrows():
            rows.append({
                "Equipment ID": item["Equipment ID"],
                "Equipment Type": item["Equipment Type"],
                "Maintenance Status": item["Maintenance Status"],
                "Downtime (hours)": item["Downtime (hours)"],
                "Availability (%)": item["Availability (%)"],
                "Condition": equipment_condition(item["Temperature (C)"], item["Vibration (mm/s)"]),
            })
        cols = ["Equipment ID", "Equipment Type", "Maintenance Status",
                "Downtime (hours)", "Availability (%)", "Condition"]
        self.replace_table_rows(self.maintenance_equipment_table, rows, cols)
        self.maintenance_summary.config(
            text=(f"Open work orders: {sum(orders['Status'].str.casefold() != 'completed')}  ·  "
                  f"Equipment needing review: {len(rows)} of {len(df)} records")
        )

    def add_maintenance_order(self):
        if not self.has_permission("maintenance data"):
            messagebox.showerror("Access denied", "Your role cannot manage maintenance work orders.", parent=self)
            return
        equipment = self.equipment()
        if equipment.empty:
            messagebox.showinfo("No equipment", "Add equipment before creating a maintenance work order.", parent=self)
            return

        window = tk.Toplevel(self)
        window.title("Create Maintenance Work Order")
        window.geometry("560x650")
        window.configure(bg=BG)
        window.transient(self)
        window.grab_set()
        form = ScrollableFrame(window, background=BG)
        form.pack(fill="both", expand=True, padx=14, pady=14)
        card = tk.Frame(form.content, bg=CARD, padx=18, pady=14)
        card.pack(fill="both", expand=True)
        equipment_ids = equipment["Equipment ID"].tolist()
        initial_equipment = equipment_ids[0]
        fields = [
            ("Equipment ID", initial_equipment, equipment_ids),
            ("Reported Date", date.today().isoformat(), None),
            ("Due Date", date.today().isoformat(), None),
            ("Maintenance Type", "Preventive", ["Preventive", "Corrective", "Inspection", "Repair"]),
            ("Priority", "Medium", ["Low", "Medium", "High", "Critical"]),
            ("Assigned To", "", None),
            ("Notes", "", None),
        ]
        variables = {}
        for label, initial, choices in fields:
            variable = tk.StringVar(value=initial)
            variables[label] = variable
            self.form_entry(card, label, variable, choices)

        def save():
            values = {name: variable.get().strip() for name, variable in variables.items()}
            if not values["Assigned To"]:
                messagebox.showerror("Missing information", "Enter the person assigned to this work order.", parent=window)
                return
            try:
                reported = datetime.strptime(values["Reported Date"], "%Y-%m-%d").date()
                due = datetime.strptime(values["Due Date"], "%Y-%m-%d").date()
                if due < reported:
                    raise ValueError("Due date cannot be before the reported date.")
            except ValueError as error:
                messagebox.showerror("Invalid dates", f"Use YYYY-MM-DD dates. {error}", parent=window)
                return

            existing = set(self.maintenance_records()["Work Order ID"])
            index = 1
            while f"MO-{index:04d}" in existing:
                index += 1
            record = {column: "" for column in MAINTENANCE_COLUMNS}
            record.update(values)
            record.update({"Work Order ID": f"MO-{index:04d}", "Status": "Open"})
            orders = pd.concat([self.maintenance_records(), pd.DataFrame([record])], ignore_index=True)
            self.write_csv(MAINTENANCE_FILE, orders, MAINTENANCE_COLUMNS)

            equipment_df = self.equipment()
            equipment_df.loc[equipment_df["Equipment ID"] == values["Equipment ID"],
                             "Maintenance Status"] = "Due"
            self.write_csv(EQUIPMENT_FILE, equipment_df, EQUIPMENT_COLUMNS)
            self.refresh_maintenance_table()
            window.destroy()
            messagebox.showinfo("Work order created", f"Work order {record['Work Order ID']} was saved.", parent=self)

        self.button(card, "Save work order", save).pack(anchor="w", pady=14)

    def complete_maintenance_order(self):
        if not self.has_permission("maintenance data"):
            return
        selected = self.maintenance_table.selection()
        if not selected:
            messagebox.showinfo("Select a work order", "Select a work order row first.", parent=self)
            return
        values = self.maintenance_table.item(selected[0], "values")
        work_order_id, equipment_id = values[0], values[1]
        orders = self.maintenance_records()
        match = orders["Work Order ID"] == work_order_id
        if not match.any():
            messagebox.showerror("Not found", "That work order is no longer in the records.", parent=self)
            return
        orders.loc[match, "Status"] = "Completed"
        orders.loc[match, "Completed Date"] = date.today().isoformat()
        self.write_csv(MAINTENANCE_FILE, orders, MAINTENANCE_COLUMNS)
        equipment = self.equipment()
        other_open = orders[(orders["Equipment ID"] == equipment_id)
                            & (orders["Status"].str.casefold() != "completed")]
        if other_open.empty:
            equipment.loc[equipment["Equipment ID"] == equipment_id,
                          "Maintenance Status"] = "Available"
        self.write_csv(EQUIPMENT_FILE, equipment, EQUIPMENT_COLUMNS)
        self.refresh_maintenance_table()
        messagebox.showinfo("Completed", f"Work order {work_order_id} marked complete.", parent=self)

    # -------------------- Risk assessment --------------------
    def build_risk(self, parent):
        self.header(parent, "Risk Assessment",
                    "Calculate Risk Score = Likelihood × Consequence on a 1–5 scale.")
        card = tk.Frame(parent, bg=CARD, padx=18, pady=16)
        card.pack(fill="x")
        likelihood = tk.StringVar(value="1")
        consequence = tk.StringVar(value="1")
        self.form_entry(card, "Likelihood (1-5)", likelihood, ["1", "2", "3", "4", "5"])
        self.form_entry(card, "Consequence (1-5)", consequence, ["1", "2", "3", "4", "5"])
        result = tk.Label(parent, text="", bg=BG, fg=INK,
                          font=("Segoe UI", 13, "bold"), justify="left")
        result.pack(anchor="w", pady=16)

        def calculate():
            try:
                likelihood_value = int(likelihood.get())
                consequence_value = int(consequence.get())
                if not 1 <= likelihood_value <= 5 or not 1 <= consequence_value <= 5:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid values", "Both values must be whole numbers from 1 to 5.", parent=self)
                return
            score, level = risk_classification(likelihood_value, consequence_value)
            warning = "\nImmediate review is recommended." if level in {"High", "Critical"} else ""
            result.config(text=f"Risk score: {score}/25\nRisk classification: {level}{warning}",
                          fg=RED if level in {"High", "Critical"} else GREEN)

        self.button(card, "Calculate risk", calculate).pack(anchor="w", pady=(12, 0))

    # -------------------- Reports --------------------
    def build_reports(self, parent):
        self.header(parent, "Reports",
                    "Review role-filtered performance summaries or export authorized datasets as CSV.")
        self.report_output = tk.Text(parent, height=15, wrap="word", state="disabled",
                                     bg=CARD, fg=INK, relief="flat", padx=12, pady=10)
        self.report_output.pack(fill="both", expand=True, pady=8)
        actions = tk.Frame(parent, bg=BG)
        actions.pack(fill="x")
        self.button(actions, "Generate summary", self.generate_summary).pack(side="left")
        self.button(actions, "Export report CSV", self.export_report,
                    color=GREEN).pack(side="left", padx=8)
        exports = tk.LabelFrame(parent, text="Export records you are permitted to access",
                                bg=BG, fg=INK, padx=10, pady=9)
        exports.pack(fill="x", pady=(6, 0))
        datasets = [
            ("Worker records", "worker safety data", WORKERS_FILE, WORKER_COLUMNS),
            ("Incident records", "safety incidents", INCIDENTS_FILE, INCIDENT_COLUMNS),
            ("Equipment records", "equipment data", EQUIPMENT_FILE, EQUIPMENT_COLUMNS),
            ("Maintenance work orders", "maintenance data", MAINTENANCE_FILE, MAINTENANCE_COLUMNS),
        ]
        for label, permission, source_path, columns in datasets:
            if self.has_permission(permission):
                self.button(
                    exports, f"Export {label}",
                    lambda p=source_path, c=columns, n=label: self.export_dataset(p, c, n),
                    color="#9b8eb1",
                ).pack(side="left", padx=4, pady=3)

        available_external = [
            ("Worker Safety", "worker safety data"),
            ("Safety Incidents", "safety incidents"),
            ("Equipment", "equipment data"),
            ("Maintenance", "maintenance data"),
        ]
        allowed_external = [label for label, permission in available_external
                            if self.has_permission(permission)]
        external = tk.LabelFrame(
            parent, text="Analyze external data", bg=BG, fg=INK,
            padx=10, pady=10,
        )
        external.pack(fill="x", pady=(10, 8))
        tk.Label(
            external,
            text=("Upload a CSV, Excel, or JSON file. Choose its data type; the app "
                  "will map common column names, validate it, and analyze it using "
                  "the same safety and equipment thresholds. The upload is analyzed "
                  "separately and does not change saved records."),
            bg=BG, fg=MUTED, justify="left", wraplength=900,
        ).pack(anchor="w", pady=(0, 8))
        external_controls = tk.Frame(external, bg=BG)
        external_controls.pack(fill="x")
        self.external_category = tk.StringVar(value=allowed_external[0])
        tk.Label(external_controls, text="Data type", bg=BG, fg=INK).pack(side="left")
        ttk.Combobox(
            external_controls, textvariable=self.external_category,
            values=allowed_external, state="readonly", width=22,
        ).pack(side="left", padx=7)
        self.button(external_controls, "Upload and analyze", self.upload_external_data,
                    color=GREEN).pack(side="left")
        self.external_file_label = tk.Label(
            external, text="No external file loaded", bg=BG, fg=MUTED,
        )
        self.external_file_label.pack(anchor="w", pady=(8, 4))
        self.external_analysis_text = tk.Text(
            external, height=12, wrap="word", state="disabled",
            bg=CARD, fg=INK, relief="flat", padx=10, pady=8,
        )
        self.external_analysis_text.pack(fill="x", pady=4)
        self.external_preview_frame = tk.Frame(external, bg=BG)
        self.external_preview_frame.pack(fill="both", expand=True, pady=(4, 0))
        self.generate_summary()

    @staticmethod
    def normalize_column_name(value):
        return re.sub(r"[^a-z0-9]+", "", str(value).casefold())

    def canonicalize_external_columns(self, frame, category):
        """Map common spreadsheet header variants onto the app's field names."""
        schema_by_category = {
            "Worker Safety": WORKER_COLUMNS,
            "Safety Incidents": INCIDENT_COLUMNS,
            "Equipment": EQUIPMENT_COLUMNS,
            "Maintenance": MAINTENANCE_COLUMNS,
        }
        aliases = {
            "Worker ID": ["worker id", "worker number", "employee id", "employee number", "personnel id", "id"],
            "Name": ["name", "worker name", "employee name", "full name"],
            "Department": ["department", "section", "team"],
            "Job Role": ["job role", "job title", "position", "occupation"],
            "Shift": ["shift", "work shift"],
            "PPE Compliance (%)": ["ppe compliance", "ppe compliance percent", "ppe compliance percentage", "ppe compliance (%)", "ppe"],
            "Training Status": ["training status", "training", "training completion"],
            "Fatigue Level (1-10)": ["fatigue", "fatigue level", "fatigue level (1-10)", "fatigue score"],
            "Safety Observations": ["safety observations", "observations", "observation count"],
            "Near Misses": ["near misses", "near miss", "near miss count", "near misses count"],
            "Previous Incidents": ["previous incidents", "incident history", "prior incidents"],
            "Risk Likelihood": ["risk likelihood", "likelihood"],
            "Risk Consequence": ["risk consequence", "consequence", "severity score"],
            "Risk Score": ["risk score", "risk rating"],
            "Risk Level": ["risk level", "risk category", "risk classification"],
            "Assessment Date": ["assessment date", "date assessed", "assessment timestamp"],
            "Incident ID": ["incident id", "incident number", "case id", "record id"],
            "Date": ["date", "incident date", "reported date", "recorded date"],
            "Time": ["time", "incident time", "reported time"],
            "Location": ["location", "site", "work area", "area"],
            "Incident Type": ["incident type", "type", "event type", "category"],
            "Severity": ["severity", "severity level", "incident severity"],
            "Injury Status": ["injury status", "injury", "injury outcome"],
            "Lost-Time Injury Status": ["lost-time injury status", "lost time injury", "lti", "lost time"],
            "Cause": ["cause", "root cause", "incident cause"],
            "Corrective Action": ["corrective action", "action taken", "preventive action"],
            "Incident Status": ["incident status", "status", "case status"],
            "Equipment ID": ["equipment id", "asset id", "asset number", "machine id", "unit id"],
            "Equipment Type": ["equipment type", "equipment", "machine type", "asset type"],
            "Manufacturer": ["manufacturer", "make", "brand"],
            "Operating Hours": ["operating hours", "hours operated", "run hours"],
            "Temperature (C)": ["temperature", "temperature c", "temperature (c)", "temp", "equipment temperature"],
            "Vibration (mm/s)": ["vibration", "vibration mm/s", "vibration (mm/s)", "vibration level"],
            "Fuel Consumption": ["fuel consumption", "fuel used", "fuel usage"],
            "Brake Status": ["brake status", "brakes"],
            "Tyre Status": ["tyre status", "tire status", "tyres", "tires"],
            "Engine Status": ["engine status", "engine condition"],
            "Maintenance Status": ["maintenance status", "maintenance condition", "equipment status"],
            "Downtime (hours)": ["downtime", "downtime hours", "downtime (hours)", "hours down"],
            "Availability (%)": ["availability", "availability percent", "availability (%)", "uptime percentage"],
            "Work Order ID": ["work order id", "work order number", "maintenance id", "order id"],
            "Reported Date": ["reported date", "created date", "opened date"],
            "Due Date": ["due date", "maintenance due date", "scheduled date"],
            "Maintenance Type": ["maintenance type", "work type", "service type"],
            "Priority": ["priority", "maintenance priority"],
            "Assigned To": ["assigned to", "technician", "owner", "assignee"],
            "Notes": ["notes", "comments", "description", "work description"],
            "Completed Date": ["completed date", "completion date", "closed date"],
            "Status": ["work order status", "maintenance work status"],
        }
        alias_lookup = {}
        for canonical, options in aliases.items():
            for option in [canonical, *options]:
                alias_lookup[self.normalize_column_name(option)] = canonical

        # These headers mean different things in different imported datasets.
        if category == "Safety Incidents":
            alias_lookup[self.normalize_column_name("reported date")] = "Date"
            alias_lookup[self.normalize_column_name("status")] = "Incident Status"
        elif category == "Maintenance":
            alias_lookup[self.normalize_column_name("status")] = "Status"
            alias_lookup[self.normalize_column_name("reported date")] = "Reported Date"
        elif category == "Equipment":
            alias_lookup[self.normalize_column_name("status")] = "Maintenance Status"

        renamed = {}
        used = set()
        for original in frame.columns:
            mapped = alias_lookup.get(self.normalize_column_name(original))
            if mapped and mapped not in used:
                renamed[original] = mapped
                used.add(mapped)
        normalized = frame.rename(columns=renamed).copy()
        schema = schema_by_category[category]
        normalized = normalized.loc[:, ~normalized.columns.duplicated()]
        for column in schema:
            if column not in normalized.columns:
                normalized[column] = ""
        return normalized[schema].fillna("")

    def read_external_file(self, path):
        suffix = Path(path).suffix.casefold()
        if suffix == ".csv":
            try:
                return pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
            except UnicodeDecodeError:
                return pd.read_csv(path, dtype=str, encoding="latin-1").fillna("")
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path, dtype=str).fillna("")
        if suffix == ".json":
            return pd.read_json(path, dtype=False).fillna("")
        raise ValueError("Select a .csv, .xlsx, .xls, or .json file.")

    def external_required_columns(self, category):
        required = {
            "Worker Safety": ["PPE Compliance (%)", "Fatigue Level (1-10)"],
            "Safety Incidents": ["Incident Type", "Severity"],
            "Equipment": ["Temperature (C)", "Vibration (mm/s)"],
            "Maintenance": ["Equipment ID", "Due Date", "Status"],
        }
        return required[category]

    def upload_external_data(self):
        category = self.external_category.get()
        permission = {
            "Worker Safety": "worker safety data",
            "Safety Incidents": "safety incidents",
            "Equipment": "equipment data",
            "Maintenance": "maintenance data",
        }.get(category)
        if not permission or not self.has_permission(permission):
            messagebox.showerror("Access denied", "Your role cannot analyze this data type.", parent=self)
            return
        path = filedialog.askopenfilename(
            parent=self, title="Choose external mining data",
            filetypes=[
                ("Supported data", "*.csv *.xlsx *.xls *.json"),
                ("CSV files", "*.csv"), ("Excel workbooks", "*.xlsx *.xls"),
                ("JSON files", "*.json"), ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            uploaded = self.read_external_file(path)
            if uploaded.empty:
                raise ValueError("The selected file has no data rows.")
            data = self.canonicalize_external_columns(uploaded, category)
            missing = [column for column in self.external_required_columns(category)
                       if uploaded.empty or not data[column].astype(str).str.strip().ne("").any()]
            if missing:
                raise ValueError(
                    "This file does not contain the required field(s) for "
                    f"{category}: {', '.join(missing)}. Check the column headings."
                )
            if category in {"Safety Incidents", "Worker Safety"}:
                date_column = "Date" if category == "Safety Incidents" else "Assessment Date"
                if date_column in data.columns:
                    parsed_dates = pd.to_datetime(data[date_column], errors="coerce")
                    data[date_column] = parsed_dates.dt.strftime("%Y-%m-%d").fillna("")
            if category == "Worker Safety":
                for _, row in data.iterrows():
                    likelihood = self.number(row["Risk Likelihood"], default=-1)
                    consequence = self.number(row["Risk Consequence"], default=-1)
                    if likelihood in range(1, 6) and consequence in range(1, 6):
                        score, level = risk_classification(likelihood, consequence)
                        if not str(row["Risk Score"]).strip():
                            data.loc[_, "Risk Score"] = score
                        if not str(row["Risk Level"]).strip():
                            data.loc[_, "Risk Level"] = level
            self.show_external_analysis(category, data, path)
        except ImportError as error:
            package = "xlrd" if Path(path).suffix.casefold() == ".xls" else "openpyxl"
            messagebox.showerror(
                "Excel reader unavailable",
                "Install the Excel reader package in PyCharm's terminal with:\n"
                f"pip install {package}\n\n{error}", parent=self,
            )
        except (OSError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            messagebox.showerror("Could not analyze file", str(error), parent=self)

    def external_analysis_rows(self, category, data):
        rows = [{"Metric": "Rows analyzed", "Value": len(data)}]
        if category == "Worker Safety":
            ppe = pd.to_numeric(data["PPE Compliance (%)"], errors="coerce")
            fatigue = pd.to_numeric(data["Fatigue Level (1-10)"], errors="coerce")
            training = data["Training Status"].str.casefold()
            rows.extend([
                {"Metric": "Average PPE compliance (%)", "Value": round(ppe.mean(), 2) if ppe.notna().any() else "N/A"},
                {"Metric": "PPE below 80%", "Value": int((ppe < 80).sum())},
                {"Metric": "High fatigue (8 or above)", "Value": int((fatigue >= 8).sum())},
                {"Metric": "Training expired/not completed", "Value": int(training.isin(["expired", "not completed"]).sum())},
            ])
            scores = pd.to_numeric(data["Risk Score"], errors="coerce")
            if not scores.notna().any():
                likelihood = pd.to_numeric(data["Risk Likelihood"], errors="coerce")
                consequence = pd.to_numeric(data["Risk Consequence"], errors="coerce")
                scores = likelihood * consequence
            rows.extend([
                {"Metric": "High/Critical risk scores (10+)", "Value": int((scores >= 10).sum())},
                {"Metric": "Critical risk scores (17+)", "Value": int((scores >= 17).sum())},
            ])
            for department, count in data.groupby("Department").size().items():
                rows.append({"Metric": f"Workers in {department or 'Unspecified'}", "Value": int(count)})
        elif category == "Safety Incidents":
            types = data["Incident Type"].str.casefold()
            severity = data["Severity"].str.casefold()
            status = data["Incident Status"].str.casefold()
            rows.extend([
                {"Metric": "Safety incidents", "Value": int((types == "safety incident").sum())},
                {"Metric": "Near misses", "Value": int((types == "near miss").sum())},
                {"Metric": "High/Critical incidents", "Value": int(severity.isin(["high", "critical"]).sum())},
                {"Metric": "Open incidents", "Value": int((status != "closed").sum())},
                {"Metric": "Lost-time injuries", "Value": int(data["Lost-Time Injury Status"].str.casefold().eq("yes").sum())},
            ])
            for dimension in ("Department", "Shift", "Incident Type", "Severity"):
                for value, count in data.groupby(dimension).size().sort_values(ascending=False).items():
                    rows.append({"Metric": f"{dimension}: {value or 'Unspecified'}", "Value": int(count)})
            dates = pd.to_datetime(data["Date"], errors="coerce")
            dated = data.loc[dates.notna()].copy()
            dated["Month"] = dates[dates.notna()].dt.to_period("M").astype(str)
            for month, count in dated.groupby("Month").size().sort_index().items():
                rows.append({"Metric": f"Incidents in {month}", "Value": int(count)})
        elif category == "Equipment":
            conditions = []
            for _, row in data.iterrows():
                try:
                    conditions.append(equipment_condition(
                        row["Temperature (C)"], row["Vibration (mm/s)"]
                    ))
                except (TypeError, ValueError):
                    conditions.append("Unspecified")
            availability = pd.to_numeric(data["Availability (%)"], errors="coerce")
            if not availability.notna().any():
                operating = pd.to_numeric(data["Operating Hours"], errors="coerce")
                downtime = pd.to_numeric(data["Downtime (hours)"], errors="coerce")
                derived = operating / (operating + downtime) * 100
                availability = availability.fillna(derived)
            rows.extend([
                {"Metric": "Normal condition", "Value": conditions.count("Normal")},
                {"Metric": "Warning condition", "Value": conditions.count("Warning")},
                {"Metric": "Critical condition", "Value": conditions.count("Critical")},
                {"Metric": "Rows missing temperature or vibration", "Value": conditions.count("Unspecified")},
                {"Metric": "Average availability (%)", "Value": round(availability.mean(), 2) if availability.notna().any() else "N/A"},
                {"Metric": "Downtime above 20 hours", "Value": int((pd.to_numeric(data["Downtime (hours)"], errors="coerce") > 20).sum())},
            ])
            for status, count in data.groupby("Maintenance Status").size().items():
                rows.append({"Metric": f"Maintenance status: {status or 'Unspecified'}", "Value": int(count)})
        else:
            pending = data[data["Status"].str.casefold() != "completed"]
            overdue = 0
            due_today = 0
            today = date.today()
            for value in pending["Due Date"]:
                try:
                    due_date = datetime.strptime(value, "%Y-%m-%d").date()
                    overdue += due_date < today
                    due_today += due_date == today
                except ValueError:
                    pass
            rows.extend([
                {"Metric": "Open work orders", "Value": len(pending)},
                {"Metric": "Overdue work orders", "Value": overdue},
                {"Metric": "Due today", "Value": due_today},
            ])
            for priority, count in pending.groupby("Priority").size().items():
                rows.append({"Metric": f"Open work orders with {priority or 'unspecified'} priority", "Value": int(count)})
        return rows

    def show_external_analysis(self, category, data, path):
        self.external_file_label.config(
            text=f"Loaded: {Path(path).name}  ·  {len(data)} rows  ·  analyzed separately",
            fg=GREEN,
        )
        analysis_rows = self.external_analysis_rows(category, data)
        analysis_text = [
            f"External {category} analysis",
            f"Rows analyzed: {len(data)}",
            f"Rows with at least one missing field: {int(data.astype(str).apply(lambda col: col.str.strip().eq('')).any(axis=1).sum())}",
            "",
        ]
        analysis_text.extend(f"• {row['Metric']}: {row['Value']}" for row in analysis_rows[1:])
        self.external_analysis_text.configure(state="normal")
        self.external_analysis_text.delete("1.0", "end")
        self.external_analysis_text.insert("1.0", "\n".join(analysis_text))
        self.external_analysis_text.configure(state="disabled")

        for child in self.external_preview_frame.winfo_children():
            child.destroy()
        tk.Label(
            self.external_preview_frame,
            text=f"Data preview (showing up to 250 of {len(data)} rows)",
            bg=BG, fg=INK, font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(2, 5))
        preview = self.make_table(
            self.external_preview_frame, list(data.columns), height=8,
        )
        self.replace_table_rows(
            preview, data.head(250).to_dict(orient="records"), list(data.columns),
        )

    def export_dataset(self, source_path, columns, label):
        required_permissions = {
            "Worker records": "worker safety data",
            "Incident records": "safety incidents",
            "Equipment records": "equipment data",
            "Maintenance work orders": "maintenance data",
        }
        if not self.has_permission(required_permissions.get(label, "")):
            messagebox.showerror("Access denied", "Your role cannot export this dataset.", parent=self)
            return
        source = self.read_csv(source_path, columns)
        if source.empty:
            messagebox.showinfo("No records", f"There are no {label.lower()} to export.", parent=self)
            return
        filename = f"khwezi_{label.lower().replace(' ', '_')}_{date.today().isoformat()}.csv"
        path = filedialog.asksaveasfilename(
            parent=self, title=f"Export {label}", defaultextension=".csv",
            initialfile=filename, filetypes=[("CSV file", "*.csv")],
        )
        if not path:
            return
        source.to_csv(path, index=False, encoding="utf-8-sig")
        messagebox.showinfo("Export complete", f"Saved {len(source)} records to:\n{path}", parent=self)

    def report_rows(self):
        rows = []
        if self.has_permission("worker safety data"):
            df = self.workers()
            ppe = pd.to_numeric(df["PPE Compliance (%)"], errors="coerce")
            risk_levels = df["Risk Level"].str.casefold()
            rows.extend([
                {"Category": "Worker safety", "Metric": "Total workers", "Value": len(df)},
                {"Category": "Worker safety", "Metric": "Average PPE compliance (%)", "Value": round(ppe.mean(), 2) if len(ppe) else 0},
                {"Category": "Worker safety", "Metric": "High fatigue workers", "Value": sum(self.number(v) >= 8 for v in df["Fatigue Level (1-10)"])},
                {"Category": "Worker safety", "Metric": "Training not current", "Value": sum(df["Training Status"].str.casefold().isin(["expired", "not completed"]))},
                {"Category": "Worker safety", "Metric": "High/Critical worker risks", "Value": sum(risk_levels.isin(["high", "critical"]))},
            ])
            for department, group in df.groupby("Department"):
                values = pd.to_numeric(group["PPE Compliance (%)"], errors="coerce")
                rows.append({"Category": "Worker analysis", "Metric": f"{department} workers", "Value": len(group)})
                rows.append({"Category": "Worker analysis", "Metric": f"{department} average PPE (%)", "Value": round(values.mean(), 2) if values.notna().any() else 0})
            for shift, group in df.groupby("Shift"):
                fatigue = pd.to_numeric(group["Fatigue Level (1-10)"], errors="coerce")
                rows.append({"Category": "Worker analysis", "Metric": f"{shift} shift average fatigue", "Value": round(fatigue.mean(), 2) if fatigue.notna().any() else 0})
        if self.has_permission("safety incidents"):
            df = self.incidents()
            rows.extend([
                {"Category": "Safety incidents", "Metric": "Total safety incidents", "Value": sum(df["Incident Type"].str.lower() == "safety incident")},
                {"Category": "Safety incidents", "Metric": "Near misses", "Value": sum(df["Incident Type"].str.lower() == "near miss")},
                {"Category": "Safety incidents", "Metric": "High/Critical incidents", "Value": sum(df["Severity"].str.lower().isin(["high", "critical"]))},
                {"Category": "Safety incidents", "Metric": "Open incidents", "Value": sum(df["Incident Status"].str.casefold() != "closed")},
                {"Category": "Safety incidents", "Metric": "Lost-time injuries", "Value": sum(df["Lost-Time Injury Status"].str.casefold() == "yes")},
            ])
            for dimension in ("Department", "Shift", "Incident Type", "Severity"):
                for value, count in df.groupby(dimension).size().sort_values(ascending=False).items():
                    rows.append({"Category": f"Incident analysis by {dimension.lower()}",
                                 "Metric": str(value), "Value": int(count)})
            dates = pd.to_datetime(df["Date"], errors="coerce")
            dated = df.loc[dates.notna()].copy()
            dated["Month"] = dates[dates.notna()].dt.to_period("M").astype(str)
            for month, count in dated.groupby("Month").size().sort_index().items():
                rows.append({"Category": "Incident analysis by month",
                             "Metric": month, "Value": int(count)})
        if self.has_permission("equipment data"):
            df = self.equipment()
            availability = pd.to_numeric(df["Availability (%)"], errors="coerce")
            conditions = [equipment_condition(row["Temperature (C)"], row["Vibration (mm/s)"])
                          for _, row in df.iterrows()]
            rows.extend([
                {"Category": "Equipment", "Metric": "Total equipment", "Value": len(df)},
                {"Category": "Equipment", "Metric": "Under maintenance", "Value": sum(df["Maintenance Status"].str.lower() == "under maintenance")},
                {"Category": "Equipment", "Metric": "Average availability (%)", "Value": round(availability.mean(), 2) if len(availability) else 0},
                {"Category": "Equipment", "Metric": "Warning/Critical condition alerts", "Value": sum(value != "Normal" for value in conditions)},
                {"Category": "Equipment", "Metric": "Equipment below 80% availability", "Value": sum(availability < 80)},
            ])
            status_counts = df.groupby("Maintenance Status").size()
            for status, count in status_counts.items():
                rows.append({"Category": "Equipment analysis by maintenance status",
                             "Metric": status or "Unspecified", "Value": int(count)})
            for equipment_type, group in df.groupby("Equipment Type"):
                group_availability = pd.to_numeric(group["Availability (%)"], errors="coerce")
                rows.append({"Category": "Equipment analysis by type",
                             "Metric": f"{equipment_type} average availability (%)",
                             "Value": round(group_availability.mean(), 2) if group_availability.notna().any() else 0})
        if self.has_permission("maintenance data"):
            orders = self.maintenance_records()
            pending = orders[orders["Status"].str.casefold() != "completed"]
            today = date.today()
            overdue = 0
            for due in pending["Due Date"]:
                try:
                    overdue += datetime.strptime(due, "%Y-%m-%d").date() < today
                except ValueError:
                    pass
            rows.extend([
                {"Category": "Maintenance", "Metric": "Total work orders", "Value": len(orders)},
                {"Category": "Maintenance", "Metric": "Open work orders", "Value": len(pending)},
                {"Category": "Maintenance", "Metric": "Overdue work orders", "Value": overdue},
            ])
        return rows

    def generate_summary(self):
        rows = self.report_rows()
        text = "MINING MONITORING SUMMARY\nGenerated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n\n"
        text += "\n".join(f"{row['Category']} — {row['Metric']}: {row['Value']}" for row in rows)
        self.report_output.config(state="normal")
        self.report_output.delete("1.0", "end")
        self.report_output.insert("1.0", text)
        self.report_output.config(state="disabled")

    def export_report(self):
        rows = self.report_rows()
        if not rows:
            messagebox.showinfo("No data", "There are no reportable records for this role.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self, title="Save mining report", defaultextension=".csv",
            initialfile=f"khwezi_report_{date.today().isoformat()}.csv",
            filetypes=[("CSV file", "*.csv")],
        )
        if not path:
            return
        pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
        messagebox.showinfo("Report exported", f"Saved report to:\n{path}", parent=self)


if __name__ == "__main__":
    KhweziMiningApp().mainloop()
