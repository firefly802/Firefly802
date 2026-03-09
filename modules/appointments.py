# --- Standard Library Imports ---
import json
import os
from . import config

# --- Module Description ---
# This module manages appointments.
# It handles loading, saving, adding, and deleting appointments.
# Appointments are stored in a JSON file defined in config.py.

def load_appointments():
    """Loads appointments from the JSON file."""
    if not os.path.exists(config.APPOINTMENTS_FILE):
        return {}
    try:
        with open(config.APPOINTMENTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_appointments(appointments):
    """Saves appointments to the JSON file."""
    try:
        with open(config.APPOINTMENTS_FILE, "w") as f:
            json.dump(appointments, f, indent=4)
    except IOError as e:
        print(f"Error saving appointments: {e}")

def get_appointments_for_date(date_str):
    """Retrieves appointments for a specific date."""
    appointments = load_appointments()
    return appointments.get(date_str, [])

def add_appointment(date_str, time_str, description):
    """Adds a new appointment."""
    appointments = load_appointments()
    if date_str not in appointments:
        appointments[date_str] = []
    
    appointments[date_str].append({
        "time": time_str,
        "description": description
    })
    
    # Sort appointments by time
    appointments[date_str].sort(key=lambda x: x["time"])
    
    save_appointments(appointments)

def delete_appointment(date_str, appointment):
    """Deletes an appointment."""
    appointments = load_appointments()
    if date_str in appointments:
        if appointment in appointments[date_str]:
            appointments[date_str].remove(appointment)
            if not appointments[date_str]:
                del appointments[date_str]
            save_appointments(appointments)
