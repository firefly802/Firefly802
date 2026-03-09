# --- Standard Library Imports ---
import datetime
import time
import threading
import os
import json
from . import config
from .utils import respond
from . import database # Import the consolidated database module

# --- Module Description ---
# This module manages the background thread for checking reminders.
# Data access is now handled by the database module.

def check_reminders(app):
    """Periodically checks for due reminders and appointments, and notifies the user."""
    while True:
        now = datetime.datetime.now()
        now_ts = now.timestamp()
        
        # Check for regular reminders
        reminders = database.load_reminders()
        for reminder in reminders:
            if not reminder["completed"] and reminder["remind_at"] <= now_ts:
                database.mark_reminder_completed(reminder["id"])
                
                # Notify the user in the main thread
                app.after(0, respond, app, f"🔔 Reminder: {reminder['text']}", speak=True)

        # Check for upcoming appointments
        today_str = now.date().isoformat()
        appts = database.get_appointments_for_date(today_str)
        
        for appt in appts:
            try:
                appt_time_str = f"{today_str} {appt['time']}"
                appt_time = datetime.datetime.strptime(appt_time_str, "%Y-%m-%d %H:%M")
                
                reminder_time = appt_time - datetime.timedelta(minutes=15)
                
                # Check if it's time for a 15-minute reminder
                if reminder_time <= now < (reminder_time + datetime.timedelta(seconds=30)):
                    # Check if a reminder for this appointment was already sent
                    if not was_reminder_sent(appt):
                        mark_reminder_as_sent(appt)
                        app.after(0, respond, app, f"🔔 Upcoming Appointment in 15 minutes: {appt['description']}", speak=True)

            except ValueError:
                # Handle cases where the time format is incorrect
                continue

        time.sleep(30) # Check every 30 seconds

# --- Appointment Reminder Persistence (Keep as JSON for simplicity or move to DB later) ---
# For now, keeping the sent_appointment_reminders as a simple JSON cache is fine 
# since it's transient data.

def was_reminder_sent(appointment):
    """Checks if a reminder for a specific appointment has already been sent."""
    sent_reminders = load_sent_reminders()
    # Use a unique signature for the appointment
    sig = f"{appointment['date']}_{appointment['time']}_{appointment['description']}"
    return sig in sent_reminders

def mark_reminder_as_sent(appointment):
    """Marks an appointment reminder as sent."""
    sent_reminders = load_sent_reminders()
    sig = f"{appointment['date']}_{appointment['time']}_{appointment['description']}"
    sent_reminders.append(sig)
    save_sent_reminders(sent_reminders)

def load_sent_reminders():
    """Loads the list of sent appointment reminders."""
    path = os.path.join(os.path.dirname(config.REMINDERS_FILE), "sent_appointment_reminders.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_sent_reminders(sent_reminders):
    """Saves the list of sent appointment reminders."""
    path = os.path.join(os.path.dirname(config.REMINDERS_FILE), "sent_appointment_reminders.json")
    try:
        with open(path, "w") as f:
            json.dump(sent_reminders, f, indent=4)
    except IOError as e:
        print(f"Error saving sent reminders: {e}")

def start_reminder_thread(app):
    """Starts the background thread for checking reminders."""
    reminder_thread = threading.Thread(target=check_reminders, args=(app,), daemon=True)
    reminder_thread.start()
