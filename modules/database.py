# --- Standard Library Imports ---
import sqlite3
import json
import os
import datetime
from . import config

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def initialize_database():
    """Creates tables if they don't exist and migrates legacy JSON data."""
    conn = get_connection()
    cursor = conn.cursor()

    # --- Create Tables ---
    
    # To-Dos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Reminders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            remind_at REAL NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    ''')

    # Appointments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')

    # Contacts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

    # --- Migrate Legacy Data ---
    migrate_legacy_data()

def migrate_legacy_data():
    """Reads old JSON files and inserts data into SQLite, then backs up the JSON."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Migrate To-Dos
    if os.path.exists(config.TODOS_FILE):
        try:
            with open(config.TODOS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        cursor.execute('INSERT INTO todos (text, completed) VALUES (?, ?)', 
                                       (item.get('text'), item.get('completed', False)))
            os.rename(config.TODOS_FILE, config.TODOS_FILE + ".bak")
            print("Migrated todos.json to database.")
        except Exception as e:
            print(f"Error migrating todos: {e}")

    # 2. Migrate Reminders
    if os.path.exists(config.REMINDERS_FILE):
        try:
            with open(config.REMINDERS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        cursor.execute('INSERT INTO reminders (text, remind_at, completed) VALUES (?, ?, ?)', 
                                       (item.get('text'), item.get('remind_at'), item.get('completed', False)))
            os.rename(config.REMINDERS_FILE, config.REMINDERS_FILE + ".bak")
            print("Migrated reminders.json to database.")
        except Exception as e:
            print(f"Error migrating reminders: {e}")

    # 3. Migrate Appointments
    if os.path.exists(config.APPOINTMENTS_FILE):
        try:
            with open(config.APPOINTMENTS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for date_str, appt_list in data.items():
                        for appt in appt_list:
                            cursor.execute('INSERT INTO appointments (date, time, description) VALUES (?, ?, ?)', 
                                           (date_str, appt.get('time'), appt.get('description')))
            os.rename(config.APPOINTMENTS_FILE, config.APPOINTMENTS_FILE + ".bak")
            print("Migrated appointments.json to database.")
        except Exception as e:
            print(f"Error migrating appointments: {e}")

    # 4. Migrate Contacts
    if os.path.exists(config.CONTACTS_FILE):
        try:
            with open(config.CONTACTS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        # Check for duplicates before inserting
                        cursor.execute('SELECT id FROM contacts WHERE phone = ?', (item.get('phone'),))
                        if not cursor.fetchone():
                            cursor.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', 
                                           (item.get('name'), item.get('phone')))
            os.rename(config.CONTACTS_FILE, config.CONTACTS_FILE + ".bak")
            print("Migrated contacts.json to database.")
        except Exception as e:
            print(f"Error migrating contacts: {e}")

    conn.commit()
    conn.close()
