"""
Appointments manager for Firefly AI.
Manages calendar appointments and schedules.
"""

import os
import json
from typing import List, Dict, Optional
from . import config


def _get_appointments_file():
    """Get the appointments file path."""
    return config.APPOINTMENTS_FILE


def _load_all_appointments() -> Dict[str, List[Dict]]:
    """Load all appointments from file."""
    appt_file = _get_appointments_file()
    if os.path.exists(appt_file):
        try:
            with open(appt_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_all_appointments(appointments: Dict[str, List[Dict]]):
    """Save all appointments to file."""
    appt_file = _get_appointments_file()
    os.makedirs(os.path.dirname(appt_file), exist_ok=True)
    with open(appt_file, "w", encoding="utf-8") as f:
        json.dump(appointments, f, indent=2)


def get_appointments_for_date(date_str: str) -> List[Dict]:
    """
    Get all appointments for a specific date.
    
    Args:
        date_str: ISO format date string (YYYY-MM-DD)
        
    Returns:
        List of appointment dictionaries with 'time' and 'description' keys
    """
    all_appointments = _load_all_appointments()
    return all_appointments.get(date_str, [])


def add_appointment(date_str: str, time_str: str, description: str) -> bool:
    """
    Add a new appointment.
    
    Args:
        date_str: ISO format date string (YYYY-MM-DD)
        time_str: Time in HH:MM format
        description: Appointment description
        
    Returns:
        True if successful, False otherwise
    """
    try:
        all_appointments = _load_all_appointments()
        if date_str not in all_appointments:
            all_appointments[date_str] = []
        
        # Add new appointment
        appointment = {
            "time": time_str,
            "description": description
        }
        all_appointments[date_str].append(appointment)
        _save_all_appointments(all_appointments)
        return True
    except Exception as e:
        print(f"Error adding appointment: {e}")
        return False


def delete_appointment(date_str: str, appointment: Dict) -> bool:
    """
    Delete an appointment.
    
    Args:
        date_str: ISO format date string (YYYY-MM-DD)
        appointment: The appointment dictionary to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        all_appointments = _load_all_appointments()
        if date_str in all_appointments:
            # Remove the appointment that matches this one
            all_appointments[date_str] = [
                a for a in all_appointments[date_str]
                if not (a.get("time") == appointment.get("time") and 
                       a.get("description") == appointment.get("description"))
            ]
            _save_all_appointments(all_appointments)
        return True
    except Exception as e:
        print(f"Error deleting appointment: {e}")
        return False


def get_all_appointments() -> Dict[str, List[Dict]]:
    """Get all appointments."""
    return _load_all_appointments()
