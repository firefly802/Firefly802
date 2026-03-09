# --- Local Imports ---
from . import database

def load_notes():
    """Loads all notes from the database, ordered by most recently updated."""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "title": row["title"], "content": row["content"], "updated_at": row["updated_at"]} for row in rows]

def add_note(title, content):
    """Adds a new note."""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
    conn.commit()
    conn.close()

def update_note(note_id, title, content):
    """Updates an existing note."""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (title, content, note_id))
    conn.commit()
    conn.close()

def delete_note(note_id):
    """Deletes a note."""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
