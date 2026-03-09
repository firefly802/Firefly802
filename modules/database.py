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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_completed TEXT
        )
    ''')
    
    # Add date_completed column if it doesn't exist (for migration)
    try:
        cursor.execute("ALTER TABLE todos ADD COLUMN date_completed TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

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

    # Notes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Create Indexes for Performance ---
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_todos_completed ON todos(completed)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reminders_completed ON reminders(completed)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at)')

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

# ==========================================
#               DATA ACCESS LAYER
# ==========================================

# --- To-Do Operations ---
def load_todos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "text": row["text"], "completed": bool(row["completed"]), "date_completed": row["date_completed"]} for row in rows]

def add_task(task_text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO todos (text, completed) VALUES (?, ?)", (task_text, False))
    conn.commit()
    conn.close()
    return load_todos()

def toggle_task(index):
    todos = load_todos()
    if 0 <= index < len(todos):
        task = todos[index]
        new_status = not task["completed"]
        date_completed = datetime.date.today().isoformat() if new_status else None
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE todos SET completed = ?, date_completed = ? WHERE id = ?", (new_status, date_completed, task["id"]))
        conn.commit()
        conn.close()
    return load_todos()

def delete_completed_tasks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE completed = 1")
    conn.commit()
    conn.close()
    return load_todos()

# --- Reminder Operations ---
def load_reminders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "text": row["text"], "remind_at": row["remind_at"], "completed": bool(row["completed"])} for row in rows]

def add_reminder(text, remind_at):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (text, remind_at, completed) VALUES (?, ?, ?)", (text, remind_at, False))
    conn.commit()
    conn.close()
    return load_reminders()

def mark_reminder_completed(reminder_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

# --- Appointment Operations ---
def get_appointments_for_date(date_str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments WHERE date = ? ORDER BY time", (date_str,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "date": row["date"], "time": row["time"], "description": row["description"]} for row in rows]

def add_appointment(date_str, time_str, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO appointments (date, time, description) VALUES (?, ?, ?)", (date_str, time_str, description))
    conn.commit()
    conn.close()

def delete_appointment(date_str, appointment):
    if "id" in appointment:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment["id"],))
        conn.commit()
        conn.close()
    else:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM appointments WHERE date = ? AND time = ? AND description = ?", 
                       (date_str, appointment["time"], appointment["description"]))
        conn.commit()
        conn.close()

# --- Contact Operations ---
def load_contacts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "name": row["name"], "phone": row["phone"]} for row in rows]

def add_contact(name, phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO contacts (name, phone) VALUES (?, ?)", (name, phone))
    conn.commit()
    conn.close()

def update_contact(old_contact, new_name, new_phone):
    if "id" in old_contact:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE contacts SET name = ?, phone = ? WHERE id = ?", (new_name, new_phone, old_contact["id"]))
        conn.commit()
        conn.close()
        return True
    return False

def delete_contact(contact):
    if "id" in contact:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact["id"],))
        conn.commit()
        conn.close()

# --- Note Operations ---
def load_notes():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "content": row["content"], "updated_at": row["updated_at"]} for row in rows]

def add_note(title, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()

def update_note(note_id, title, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (title, content, note_id))
    conn.commit()
    conn.close()

def delete_note(note_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
