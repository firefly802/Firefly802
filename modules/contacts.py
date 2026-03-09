# --- Standard Library Imports ---
import json
import os
from . import config

# --- Module Description ---
# This module manages contacts.
# It handles loading, saving, adding, and deleting contacts.
# Contacts are stored in a JSON file defined in config.py.

def load_contacts():
    """Loads contacts from the JSON file."""
    if not os.path.exists(config.CONTACTS_FILE):
        return []
    try:
        with open(config.CONTACTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_contacts(contacts):
    """Saves contacts to the JSON file."""
    try:
        with open(config.CONTACTS_FILE, "w") as f:
            json.dump(contacts, f, indent=4)
    except IOError as e:
        print(f"Error saving contacts: {e}")

def add_contact(name, phone):
    """Adds a new contact."""
    contacts = load_contacts()
    contacts.append({"name": name, "phone": phone})
    save_contacts(contacts)

def delete_contact(contact):
    """Deletes a contact."""
    contacts = load_contacts()
    if contact in contacts:
        contacts.remove(contact)
        save_contacts(contacts)
