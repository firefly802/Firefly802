# --- Standard Library Imports ---
import tkinter as tk
import calendar
import datetime

# --- Third-Party Imports ---
import customtkinter as ctk

# --- Local Imports ---
from . import appointments
from . import contacts

class CalendarManager(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calendar")
        self.geometry("900x650")

        self.parent = parent
        self.today = datetime.date.today()
        self.current_year = self.today.year
        self.current_month = self.today.month

        self.init_ui()
        self.update_calendar()

    def init_ui(self):
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # --- Calendar View (Left Frame) ---
        calendar_controls = ctk.CTkFrame(left_frame)
        calendar_controls.pack(pady=10)

        ctk.CTkButton(calendar_controls, text="<", command=self.prev_month, width=40).pack(side="left", padx=5)
        self.month_year_label = ctk.CTkLabel(calendar_controls, text="", font=("Segoe UI", 16, "bold"))
        self.month_year_label.pack(side="left", padx=20)
        ctk.CTkButton(calendar_controls, text=">", command=self.next_month, width=40).pack(side="left", padx=5)

        self.calendar_frame = ctk.CTkFrame(left_frame)
        self.calendar_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Appointments and Contacts (Right Frame) ---
        self.notebook = ctk.CTkTabview(right_frame)
        self.notebook.pack(fill="both", expand=True, pady=10, padx=10)
        self.notebook.add("Appointments")
        self.notebook.add("Contacts")

        self.init_appointments_tab(self.notebook.tab("Appointments"))
        self.init_contacts_tab(self.notebook.tab("Contacts"))

    def init_appointments_tab(self, tab):
        ctk.CTkLabel(tab, text="Appointments for Selected Date", font=("Segoe UI", 14, "bold")).pack(pady=10)
        self.appointments_list = tk.Listbox(tab, bg="#2b2b2b", fg="white", border=0, selectbackground="#007acc")
        self.appointments_list.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Add Appointment", command=self.add_appointment).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Delete Appointment", command=self.delete_appointment).pack(side="left", padx=5)

    def init_contacts_tab(self, tab):
        ctk.CTkLabel(tab, text="Contacts", font=("Segoe UI", 14, "bold")).pack(pady=10)
        self.contacts_list = tk.Listbox(tab, bg="#2b2b2b", fg="white", border=0, selectbackground="#007acc")
        self.contacts_list.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Add Contact", command=self.add_contact).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Delete Contact", command=self.delete_contact).pack(side="left", padx=5)
        self.update_contacts_list()

    def update_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_year_label.configure(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        month_calendar = calendar.monthcalendar(self.current_year, self.current_month)
        
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            ctk.CTkLabel(self.calendar_frame, text=day, font=("Segoe UI", 10, "bold")).grid(row=0, column=i, padx=5, pady=5)

        for row_idx, week in enumerate(month_calendar, 1):
            for col_idx, day in enumerate(week):
                if day == 0:
                    continue
                
                date = datetime.date(self.current_year, self.current_month, day)
                btn = ctk.CTkButton(self.calendar_frame, text=str(day), command=lambda d=date: self.select_date(d))
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")

                if date == self.today:
                    btn.configure(fg_color="red")
        
        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)
        for i in range(len(month_calendar) + 1):
            self.calendar_frame.grid_rowconfigure(i, weight=1)

    def prev_month(self):
        self.current_month -= 1
        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()

    def select_date(self, date):
        self.selected_date = date
        self.update_appointments_list()

    def update_appointments_list(self):
        self.appointments_list.delete(0, tk.END)
        if hasattr(self, 'selected_date'):
            date_str = self.selected_date.isoformat()
            appts = appointments.get_appointments_for_date(date_str)
            for appt in appts:
                self.appointments_list.insert(tk.END, f"{appt['time']} - {appt['description']}")

    def add_appointment(self):
        if not hasattr(self, 'selected_date'):
            return

        dialog = ctk.CTkInputDialog(text="Enter time (HH:MM):", title="Add Appointment")
        time_str = dialog.get_input()
        if not time_str: return

        dialog = ctk.CTkInputDialog(text="Enter description:", title="Add Appointment")
        desc = dialog.get_input()
        if not desc: return
        
        date_str = self.selected_date.isoformat()
        appointments.add_appointment(date_str, time_str, desc)
        self.update_appointments_list()

    def delete_appointment(self):
        selected_indices = self.appointments_list.curselection()
        if not selected_indices:
            return
        
        date_str = self.selected_date.isoformat()
        appts = appointments.get_appointments_for_date(date_str)
        
        # We delete from the end to avoid index shifting issues
        for i in sorted(selected_indices, reverse=True):
            appointments.delete_appointment(date_str, appts[i])
        
        self.update_appointments_list()

    def update_contacts_list(self):
        self.contacts_list.delete(0, tk.END)
        all_contacts = contacts.load_contacts()
        for contact in all_contacts:
            self.contacts_list.insert(tk.END, f"{contact['name']} - {contact['phone']}")

    def add_contact(self):
        dialog = ctk.CTkInputDialog(text="Enter name:", title="Add Contact")
        name = dialog.get_input()
        if not name: return

        dialog = ctk.CTkInputDialog(text="Enter phone:", title="Add Contact")
        phone = dialog.get_input()
        if not phone: return

        contacts.add_contact(name, phone)
        self.update_contacts_list()

    def delete_contact(self):
        selected_indices = self.contacts_list.curselection()
        if not selected_indices:
            return
        
        all_contacts = contacts.load_contacts()
        for i in sorted(selected_indices, reverse=True):
            contacts.delete_contact(all_contacts[i])
        
        self.update_contacts_list()

def trigger_calendar_view(app):
    calendar_view = CalendarManager(app)
    calendar_view.grab_set()
