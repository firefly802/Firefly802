# --- Standard Library Imports ---
import tkinter as tk
import calendar
import datetime

# --- Third-Party Imports ---
import customtkinter as ctk

# --- Local Imports ---
from . import appointments
from . import contacts
from . import config
from . import csv_contacts # Import the new CSV module

class CalendarManager(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Calendar")
        self.geometry("1000x700")

        self.parent = parent
        self.today = datetime.date.today()
        self.selected_date = self.today
        self.current_year = self.today.year
        self.current_month = self.today.month
        
        # Keep a reference to this instance for callbacks
        self.parent.calendar_view_instance = self
        
        self.all_contacts = [] # Cache for filtering

        self.init_ui()
        self.update_calendar()
        self.update_appointments_list()

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
        self.notebook.add("Schedule")
        self.notebook.add("Contacts")

        self.init_schedule_tab(self.notebook.tab("Schedule"))
        self.init_contacts_tab(self.notebook.tab("Contacts"))

    def init_schedule_tab(self, tab):
        self.appt_label = ctk.CTkLabel(tab, text="Daily Schedule", font=("Segoe UI", 14, "bold"))
        self.appt_label.pack(pady=(10, 5))
        
        self.slots_frame = ctk.CTkScrollableFrame(tab, label_text="Timeline (08:00 - 17:00)")
        self.slots_frame.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Add Custom Appointment", command=self.add_appointment).pack(side="left", padx=5)

    def init_contacts_tab(self, tab):
        ctk.CTkLabel(tab, text="Contacts", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        
        # Search Bar
        self.contact_search = ctk.CTkEntry(tab, placeholder_text="🔍 Search contacts...")
        self.contact_search.pack(fill="x", padx=10, pady=(0, 10))
        self.contact_search.bind("<KeyRelease>", self.filter_contacts)

        self.contacts_list = tk.Listbox(tab, bg="#2b2b2b", fg="white", border=0, selectbackground="#007acc")
        self.contacts_list.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="Add Contact", command=self.add_contact).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Edit Contact", command=self.edit_contact).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Delete Contact", command=self.delete_contact).pack(side="left", padx=5)
        
        # Add the import button
        ctk.CTkButton(
            btn_frame, 
            text="Import from CSV", 
            command=self.import_csv_contacts,
            fg_color="#28a745",
            hover_color="#218838"
        ).pack(side="left", padx=10)
        
        self.update_contacts_list()

    def import_csv_contacts(self):
        # The main app instance is passed to the import function
        csv_contacts.import_contacts_from_csv(self.parent)

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

                if date == self.selected_date:
                    btn.configure(fg_color=config.ACCENT_COLOR, border_color="white", border_width=2)
                elif date == self.today:
                    btn.configure(fg_color="#ff5555")
                else:
                    btn.configure(fg_color=["#3a7ebf", "#1f538d"])
        
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
        self.update_calendar()
        self.update_appointments_list()

    def update_appointments_list(self):
        for widget in self.slots_frame.winfo_children():
            widget.destroy()

        if hasattr(self, 'selected_date'):
            self.appt_label.configure(text=f"Schedule for {self.selected_date.strftime('%B %d, %Y')}")
            
            date_str = self.selected_date.isoformat()
            appts = appointments.get_appointments_for_date(date_str)
            
            appt_map = {h: [] for h in range(24)}
            for appt in appts:
                try:
                    h = int(appt['time'].split(':')[0])
                    if 0 <= h < 24:
                        appt_map[h].append(appt)
                except (ValueError, IndexError):
                    pass

            for hour in range(8, 18):
                row_frame = ctk.CTkFrame(self.slots_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)

                time_str = f"{hour:02d}:00"
                time_label = ctk.CTkLabel(row_frame, text=time_str, width=60, font=("Consolas", 12, "bold"))
                time_label.pack(side="left", padx=(5, 10), anchor="n")

                content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                content_frame.pack(side="left", fill="x", expand=True)

                hour_appts = appt_map.get(hour, [])

                if not hour_appts:
                    btn = ctk.CTkButton(
                        content_frame, 
                        text="Available", 
                        fg_color="transparent", 
                        border_width=1, 
                        border_color="#444444",
                        text_color="gray", 
                        anchor="w",
                        height=28,
                        command=lambda t=time_str: self.add_appointment(default_time=t)
                    )
                    btn.pack(fill="x")
                else:
                    for appt in hour_appts:
                        appt_row = ctk.CTkFrame(content_frame, fg_color="#2b2b2b", corner_radius=6)
                        appt_row.pack(fill="x", pady=1)
                        
                        desc_text = f"{appt['time']} - {appt['description']}"
                        lbl = ctk.CTkLabel(appt_row, text=desc_text, anchor="w", padx=10)
                        lbl.pack(side="left", fill="x", expand=True, pady=5)
                        
                        del_btn = ctk.CTkButton(
                            appt_row, 
                            text="×", 
                            width=30, 
                            height=25,
                            fg_color="#ff5555", 
                            hover_color="#cc0000",
                            command=lambda a=appt: self.delete_specific_appointment(a)
                        )
                        del_btn.pack(side="right", padx=5, pady=2)

    def add_appointment(self, default_time=None):
        if not hasattr(self, 'selected_date'):
            return

        if default_time:
            time_str = default_time
        else:
            dialog = ctk.CTkInputDialog(text="Enter time (HH:MM):", title="Add Appointment")
            time_str = dialog.get_input()
            if not time_str: return

        dialog = ctk.CTkInputDialog(text=f"Enter description for {time_str}:", title="Add Appointment")
        desc = dialog.get_input()
        if not desc: return
        
        date_str = self.selected_date.isoformat()
        appointments.add_appointment(date_str, time_str, desc)
        self.update_appointments_list()

    def delete_specific_appointment(self, appt):
        if not hasattr(self, 'selected_date'):
            return
            
        date_str = self.selected_date.isoformat()
        appointments.delete_appointment(date_str, appt)
        self.update_appointments_list()

    def update_contacts_list(self):
        self.all_contacts = contacts.load_contacts()
        self.filter_contacts()

    def filter_contacts(self, event=None):
        search_term = self.contact_search.get().lower()
        self.contacts_list.delete(0, tk.END)
        
        self.filtered_contacts = []
        for contact in self.all_contacts:
            if search_term in contact['name'].lower() or search_term in contact['phone']:
                self.contacts_list.insert(tk.END, f"{contact['name']} - {contact['phone']}")
                self.filtered_contacts.append(contact)

    def add_contact(self):
        dialog = ctk.CTkInputDialog(text="Enter name:", title="Add Contact")
        name = dialog.get_input()
        if not name: return

        dialog = ctk.CTkInputDialog(text="Enter phone:", title="Add Contact")
        phone = dialog.get_input()
        if not phone: return

        contacts.add_contact(name, phone)
        self.update_contacts_list()

    def edit_contact(self):
        selected_indices = self.contacts_list.curselection()
        if not selected_indices:
            return
        
        if selected_indices[0] < len(self.filtered_contacts):
            contact_to_edit = self.filtered_contacts[selected_indices[0]]
            
            dialog_name = ctk.CTkInputDialog(text=f"Edit name (Current: {contact_to_edit['name']}):", title="Edit Contact")
            new_name = dialog_name.get_input()
            if not new_name: return 

            dialog_phone = ctk.CTkInputDialog(text=f"Edit phone (Current: {contact_to_edit['phone']}):", title="Edit Contact")
            new_phone = dialog_phone.get_input()
            if not new_phone: return 

            contacts.update_contact(contact_to_edit, new_name, new_phone)
            self.update_contacts_list()

    def delete_contact(self):
        selected_indices = self.contacts_list.curselection()
        if not selected_indices:
            return
        
        for i in sorted(selected_indices, reverse=True):
            if i < len(self.filtered_contacts):
                contacts.delete_contact(self.filtered_contacts[i])
        
        self.update_contacts_list()

    def destroy(self):
        # Clean up the reference in the parent
        self.parent.calendar_view_instance = None
        super().destroy()

def trigger_calendar_view(app):
    # Close existing instance if it's open
    if hasattr(app, 'calendar_view_instance') and app.calendar_view_instance:
        app.calendar_view_instance.destroy()

    calendar_view = CalendarManager(app)
    calendar_view.grab_set()
