"""
Contacts manager for Firefly AI.
Manages contact information.
"""

import os
import json
from typing import List, Dict, Optional
from . import config


def _get_contacts_file():
    """Get the contacts file path."""
    return os.path.join(config.BASE_DIR, "contacts.json")


def _load_contacts_from_file() -> List[Dict]:
    """Load contacts from file."""
    contacts_file = _get_contacts_file()
    if os.path.exists(contacts_file):
        try:
            with open(contacts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_contacts_to_file(contacts: List[Dict]):
    """Save contacts to file."""
    contacts_file = _get_contacts_file()
    os.makedirs(os.path.dirname(contacts_file), exist_ok=True)
    with open(contacts_file, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2)


def load_contacts() -> List[Dict]:
    """
    Load all contacts.
    
    Returns:
        List of contact dictionaries with 'name', 'email', 'phone', etc.
    """
    return _load_contacts_from_file()


def add_contact(name: str, email: str = "", phone: str = "", address: str = "") -> bool:
    """
    Add a new contact.
    
    Args:
        name: Contact name
        email: Contact email
        phone: Contact phone number
        address: Contact address
        
    Returns:
        True if successful, False otherwise
    """
    try:
        contacts = load_contacts()
        
        # Check if contact already exists
        if any(c.get("name", "").lower() == name.lower() for c in contacts):
            return False
        
        new_contact = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address
        }
        contacts.append(new_contact)
        _save_contacts_to_file(contacts)
        return True
    except Exception as e:
        print(f"Error adding contact: {e}")
        return False


def delete_contact(name: str) -> bool:
    """
    Delete a contact by name.
    
    Args:
        name: Contact name
        
    Returns:
        True if successful, False otherwise
    """
    try:
        contacts = load_contacts()
        contacts = [c for c in contacts if c.get("name", "").lower() != name.lower()]
        _save_contacts_to_file(contacts)
        return True
    except Exception as e:
        print(f"Error deleting contact: {e}")
        return False


def find_contact(name: str) -> Optional[Dict]:
    """
    Find a contact by name.
    
    Args:
        name: Contact name to search for
        
    Returns:
        Contact dictionary if found, None otherwise
    """
    contacts = load_contacts()
    for contact in contacts:
        if contact.get("name", "").lower() == name.lower():
            return contact
    return None


def update_contact(name: str, **kwargs) -> bool:
    """
    Update a contact.
    
    Args:
        name: Contact name
        **kwargs: Fields to update (email, phone, address, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        contacts = load_contacts()
        for contact in contacts:
            if contact.get("name", "").lower() == name.lower():
                contact.update(kwargs)
                _save_contacts_to_file(contacts)
                return True
        return False
    except Exception as e:
        print(f"Error updating contact: {e}")
        return False
