"""
Quiz & Tutorial Tracker
-----------------------
Desktop app (Tkinter, no extra installs needed) to track:
  - Type (Quiz / Tutorial / Assessment)
  - Title and Subject/Unit
  - Notes / details (free-text input)
  - Last date (due date)
  - Status (Pending / Done)
  - Submitted (Yes / No)

Data is saved automatically to tasks.json next to this script.
Run:  python task_tracker.py
"""

import calendar
import json
import os
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
DATE_FMT = "%Y-%m-%d"


class CalendarPopup(tk.Toplevel):
    """Small month-view date picker (pure Tkinter, no extra packages)."""

    def __init__(self, parent, anchor, initial, on_select):
        super().__init__(parent)
        self.title("Pick a date")
        self.resizable(False, False)
        self.on_select = on_select
        self.today = date.today()
        self.selected = initial
        self.year, self.month = initial.year, initial.month

        head = ttk.Frame(self, padding=(6, 6, 6, 2))
        head.pack(fill="x")
        ttk.Button(head, text="<<", width=3, command=lambda: self.shift(-12)).pack(side="left")
        ttk.Button(head, text="<", width=3, command=lambda: self.shift(-1)).pack(side="left")
        self.lbl = ttk.Label(head, anchor="center", font=("TkDefaultFont", 10, "bold"))
        self.lbl.pack(side="left", expand=True, fill="x")
        ttk.Button(head, text=">", width=3, command=lambda: self.shift(1)).pack(side="left")
        ttk.Button(head, text=">>", width=3, command=lambda: self.shift(12)).pack(side="left")

        self.grid_frame = ttk.Frame(self, padding=6)
        self.grid_frame.pack()

        foot = ttk.Frame(self, padding=(6, 0, 6, 6))
        foot.pack(fill="x")
        ttk.Button(foot, text="Today", command=lambda: self.pick(self.today)).pack(side="left")
        ttk.Button(foot, text="Cancel", command=self.destroy).pack(side="right")

        self.draw()

        # place just under the widget that opened it
        self.update_idletasks()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 2
        self.geometry(f"+{x}+{y}")
        self.transient(parent)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def shift(self, months):
        total = self.year * 12 + (self.month - 1) + months
        self.year, self.month = divmod(total, 12)
        self.month += 1
        self.draw()

    def draw(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.lbl.config(text=f"{calendar.month_name[self.month]} {self.year}")

        for col, name in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            ttk.Label(self.grid_frame, text=name, width=4, anchor="center").grid(row=0, column=col)

        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(self.year, self.month)
        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                d = date(self.year, self.month, day)
                bg, fg = "#ffffff", "#000000"
                if d == self.selected:
                    bg, fg = "#0d6efd", "#ffffff"
                elif d == self.today:
                    bg = "#cfe2ff"
                tk.Button(self.grid_frame, text=str(day), width=3, relief="flat",
                          bg=bg, fg=fg, activebackground="#9ec5fe",
                          command=lambda d=d: self.pick(d)).grid(row=r, column=c, padx=1, pady=1)

    def pick(self, d):
        self.on_select(d)
        self.destroy()


class TrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz, Tutorial & Assessment Tracker")
        self.geometry("1000x620")
        self.minsize(900, 560)

        self.tasks = []
        self.selected_id = None
        self.load_data()

        self.build_form()
        self.build_filters()
        self.build_table()
        self.build_statusbar()
        self.refresh()

    # ---------- data ----------
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except (json.JSONDecodeError, OSError):
                messagebox.showwarning("Load error", "Could not read tasks.json. Starting empty.")
                self.tasks = []

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2)
        except OSError as e:
            messagebox.showerror("Save error", str(e))

    def next_id(self):
        return max((t["id"] for t in self.tasks), default=0) + 1

    # ---------- UI ----------
    def build_form(self):
        frm = ttk.LabelFrame(self, text="Add / Edit item", padding=10)
        frm.pack(fill="x", padx=10, pady=(10, 5))

        self.var_type = tk.StringVar(value="Quiz")
        self.var_title = tk.StringVar()
        self.var_subject = tk.StringVar()
        self.var_notes = tk.StringVar()
        self.var_due = tk.StringVar(value=date.today().strftime(DATE_FMT))
        self.var_status = tk.StringVar(value="Pending")
        self.var_submitted = tk.StringVar(value="No")

        ttk.Label(frm, text="Type").grid(row=0, column=0, sticky="w")
        ttk.Combobox(frm, textvariable=self.var_type, values=["Quiz", "Tutorial", "Assessment"],
                     state="readonly", width=12).grid(row=1, column=0, padx=(0, 8), sticky="w")

        ttk.Label(frm, text="Title").grid(row=0, column=1, sticky="w")
        ttk.Entry(frm, textvariable=self.var_title, width=28).grid(row=1, column=1, padx=(0, 8))

        ttk.Label(frm, text="Subject / Unit").grid(row=0, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self.var_subject, width=18).grid(row=1, column=2, padx=(0, 8))

        ttk.Label(frm, text="Last date").grid(row=0, column=3, sticky="w")
        due_box = ttk.Frame(frm)
        due_box.grid(row=1, column=3, padx=(0, 8), sticky="w")
        self.due_entry = ttk.Entry(due_box, textvariable=self.var_due, width=11, state="readonly")
        self.due_entry.pack(side="left")
        self.due_entry.bind("<Button-1>", lambda e: self.open_calendar())
        ttk.Button(due_box, text="Pick", width=5, command=self.open_calendar).pack(side="left", padx=(3, 0))

        ttk.Label(frm, text="Status").grid(row=0, column=4, sticky="w")
        ttk.Combobox(frm, textvariable=self.var_status, values=["Pending", "Done"],
                     state="readonly", width=10).grid(row=1, column=4, padx=(0, 8))

        ttk.Label(frm, text="Submitted").grid(row=0, column=5, sticky="w")
        ttk.Combobox(frm, textvariable=self.var_submitted, values=["No", "Yes"],
                     state="readonly", width=8).grid(row=1, column=5)

        ttk.Label(frm, text="Notes / details (e.g. marks, weight, Moodle link)").grid(
            row=2, column=0, columnspan=6, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.var_notes).grid(
            row=3, column=0, columnspan=6, sticky="ew")
        for c in range(6):
            frm.columnconfigure(c, weight=1 if c == 1 else 0)

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=6, sticky="w", pady=(10, 0))
        ttk.Button(btns, text="Add", command=self.add_task).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Update selected", command=self.update_task).pack(side="left", padx=6)
        ttk.Button(btns, text="Delete selected", command=self.delete_task).pack(side="left", padx=6)
        ttk.Button(btns, text="Clear form", command=self.clear_form).pack(side="left", padx=6)
        ttk.Separator(btns, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(btns, text="Toggle Done", command=self.toggle_done).pack(side="left", padx=6)
        ttk.Button(btns, text="Toggle Submitted", command=self.toggle_submitted).pack(side="left", padx=6)

    def build_filters(self):
        frm = ttk.Frame(self, padding=(10, 5))
        frm.pack(fill="x")

        self.f_type = tk.StringVar(value="All")
        self.f_status = tk.StringVar(value="All")
        self.f_sub = tk.StringVar(value="All")
        self.f_search = tk.StringVar()

        ttk.Label(frm, text="Show:").pack(side="left")
        for var, vals in ((self.f_type, ["All", "Quiz", "Tutorial", "Assessment"]),
                          (self.f_status, ["All", "Pending", "Done"]),
                          (self.f_sub, ["All", "Submitted", "Not submitted"])):
            cb = ttk.Combobox(frm, textvariable=var, values=vals, state="readonly", width=13)
            cb.pack(side="left", padx=4)
            cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(frm, text="Search:").pack(side="left", padx=(15, 4))
        ent = ttk.Entry(frm, textvariable=self.f_search, width=22)
        ent.pack(side="left")
        ent.bind("<KeyRelease>", lambda e: self.refresh())

    def build_table(self):
        wrap = ttk.Frame(self, padding=(10, 5))
        wrap.pack(fill="both", expand=True)

        cols = ("type", "title", "subject", "notes", "due", "days", "status", "submitted")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", selectmode="browse")
        headings = {
            "type": ("Type", 90), "title": ("Title", 200), "subject": ("Subject / Unit", 120),
            "notes": ("Notes", 160),
            "due": ("Last date", 100), "days": ("Days left", 110),
            "status": ("Status", 90), "submitted": ("Submitted", 90),
        }
        for c, (text, w) in headings.items():
            self.tree.heading(c, text=text)
            self.tree.column(c, width=w, anchor="w" if c in ("title", "subject", "notes") else "center")

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.tag_configure("overdue", background="#f8d7da")
        self.tree.tag_configure("soon", background="#fff3cd")
        self.tree.tag_configure("complete", background="#d4edda")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Delete>", lambda e: self.delete_task())

    def build_statusbar(self):
        self.summary = tk.StringVar()
        ttk.Label(self, textvariable=self.summary, relief="sunken", anchor="w",
                  padding=(8, 3)).pack(fill="x", side="bottom")
        legend = ("Colors:  red = overdue & not submitted   |   yellow = due within 3 days   |   "
                  "green = done & submitted")
        ttk.Label(self, text=legend, foreground="#555", padding=(10, 0)).pack(fill="x", side="bottom")

    # ---------- helpers ----------
    def open_calendar(self):
        try:
            current = datetime.strptime(self.var_due.get().strip(), DATE_FMT).date()
        except ValueError:
            current = date.today()
        CalendarPopup(self, self.due_entry, current,
                      lambda d: self.var_due.set(d.strftime(DATE_FMT)))

    def read_form(self):
        title = self.var_title.get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Please enter a title.")
            return None
        try:
            due = datetime.strptime(self.var_due.get().strip(), DATE_FMT).date()
        except ValueError:
            messagebox.showwarning("Invalid date", "Use the format YYYY-MM-DD (e.g. 2026-11-20).")
            return None
        return {
            "type": self.var_type.get(),
            "title": title,
            "subject": self.var_subject.get().strip(),
            "notes": self.var_notes.get().strip(),
            "due": due.strftime(DATE_FMT),
            "status": self.var_status.get(),
            "submitted": self.var_submitted.get(),
        }

    def clear_form(self):
        self.selected_id = None
        self.var_type.set("Quiz")
        self.var_title.set("")
        self.var_subject.set("")
        self.var_notes.set("")
        self.var_due.set(date.today().strftime(DATE_FMT))
        self.var_status.set("Pending")
        self.var_submitted.set("No")
        self.tree.selection_remove(self.tree.selection())

    def find(self, task_id):
        return next((t for t in self.tasks if t["id"] == task_id), None)

    @staticmethod
    def days_left(due_str):
        d = (datetime.strptime(due_str, DATE_FMT).date() - date.today()).days
        if d < 0:
            return f"{-d} day(s) overdue"
        if d == 0:
            return "Due today"
        return f"{d} day(s)"

    # ---------- actions ----------
    def add_task(self):
        data = self.read_form()
        if not data:
            return
        data["id"] = self.next_id()
        self.tasks.append(data)
        self.save_data()
        self.clear_form()
        self.refresh()

    def update_task(self):
        if self.selected_id is None:
            messagebox.showinfo("Nothing selected", "Select a row in the table first.")
            return
        data = self.read_form()
        if not data:
            return
        task = self.find(self.selected_id)
        if task:
            task.update(data)
            self.save_data()
            self.refresh()

    def delete_task(self):
        if self.selected_id is None:
            return
        task = self.find(self.selected_id)
        if task and messagebox.askyesno("Delete", f"Delete '{task['title']}'?"):
            self.tasks.remove(task)
            self.save_data()
            self.clear_form()
            self.refresh()

    def toggle_done(self):
        task = self.find(self.selected_id) if self.selected_id is not None else None
        if not task:
            messagebox.showinfo("Nothing selected", "Select a row first.")
            return
        task["status"] = "Pending" if task["status"] == "Done" else "Done"
        self.save_data()
        self.refresh(keep=task["id"])

    def toggle_submitted(self):
        task = self.find(self.selected_id) if self.selected_id is not None else None
        if not task:
            messagebox.showinfo("Nothing selected", "Select a row first.")
            return
        task["submitted"] = "No" if task["submitted"] == "Yes" else "Yes"
        self.save_data()
        self.refresh(keep=task["id"])

    def on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_id = int(sel[0])
        t = self.find(self.selected_id)
        if t:
            self.var_type.set(t["type"])
            self.var_title.set(t["title"])
            self.var_subject.set(t["subject"])
            self.var_notes.set(t.get("notes", ""))
            self.var_due.set(t["due"])
            self.var_status.set(t["status"])
            self.var_submitted.set(t["submitted"])

    # ---------- table ----------
    def refresh(self, keep=None):
        keep = keep if keep is not None else self.selected_id
        self.tree.delete(*self.tree.get_children())

        q = self.f_search.get().strip().lower()
        shown = sorted(self.tasks, key=lambda t: t["due"])
        today = date.today()

        for t in shown:
            if self.f_type.get() != "All" and t["type"] != self.f_type.get():
                continue
            if self.f_status.get() != "All" and t["status"] != self.f_status.get():
                continue
            if self.f_sub.get() == "Submitted" and t["submitted"] != "Yes":
                continue
            if self.f_sub.get() == "Not submitted" and t["submitted"] != "No":
                continue
            if q and q not in (t["title"] + " " + t["subject"] + " " + t.get("notes", "")).lower():
                continue

            due = datetime.strptime(t["due"], DATE_FMT).date()
            delta = (due - today).days
            tag = ()
            if t["status"] == "Done" and t["submitted"] == "Yes":
                tag = ("complete",)
            elif t["submitted"] == "No" and delta < 0:
                tag = ("overdue",)
            elif t["submitted"] == "No" and delta <= 3:
                tag = ("soon",)

            days_text = "-" if tag == ("complete",) else self.days_left(t["due"])
            self.tree.insert("", "end", iid=str(t["id"]), tags=tag, values=(
                t["type"], t["title"], t["subject"], t.get("notes", ""), t["due"], days_text,
                t["status"], t["submitted"]))

        if keep is not None and self.tree.exists(str(keep)):
            self.tree.selection_set(str(keep))

        total = len(self.tasks)
        pending = sum(1 for t in self.tasks if t["status"] == "Pending")
        not_sub = sum(1 for t in self.tasks if t["submitted"] == "No")
        overdue = sum(1 for t in self.tasks
                      if t["submitted"] == "No"
                      and datetime.strptime(t["due"], DATE_FMT).date() < today)
        self.summary.set(f"Total: {total}   |   Pending: {pending}   |   "
                         f"Not submitted: {not_sub}   |   Overdue: {overdue}")


if __name__ == "__main__":
    TrackerApp().mainloop()
