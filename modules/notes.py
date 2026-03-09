"""
Notes module for Firefly AI.
Manages text notes and note storage.
"""

import os
import json
import uuid
from typing import List, Dict, Optional
from . import config


def _get_notes_file():
    """Get the notes file path."""
    return config.NOTES_FILE


def _load_notes_from_file() -> List[Dict]:
    """Load notes from file."""
    notes_file = _get_notes_file()
    if os.path.exists(notes_file):
        try:
            with open(notes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_notes_to_file(notes: List[Dict]):
    """Save notes to file."""
    notes_file = _get_notes_file()
    os.makedirs(os.path.dirname(notes_file), exist_ok=True)
    with open(notes_file, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)


def load_notes() -> List[Dict]:
    """
    Load all notes.
    
    Returns:
        List of note dictionaries with 'id', 'title', 'content', and 'timestamp'
    """
    notes_list = _load_notes_from_file()
    
    # Ensure all notes have required fields
    for note in notes_list:
        if "id" not in note:
            note["id"] = str(uuid.uuid4())
        if "title" not in note:
            note["title"] = "Untitled"
        if "content" not in note:
            note["content"] = ""
        if "timestamp" not in note:
            note["timestamp"] = ""
    
    return notes_list


def add_note(title: str, content: str) -> str:
    """
    Add a new note.
    
    Args:
        title: Note title
        content: Note content
        
    Returns:
        The ID of the created note
    """
    import datetime
    
    notes_list = load_notes()
    note_id = str(uuid.uuid4())
    
    new_note = {
        "id": note_id,
        "title": title,
        "content": content,
        "timestamp": datetime.datetime.now().isoformat()
    }
    notes_list.append(new_note)
    _save_notes_to_file(notes_list)
    return note_id


def update_note(note_id: str, title: str, content: str) -> bool:
    """
    Update an existing note.
    
    Args:
        note_id: The ID of the note to update
        title: New title
        content: New content
        
    Returns:
        True if successful, False otherwise
    """
    try:
        notes_list = load_notes()
        for note in notes_list:
            if note.get("id") == note_id:
                note["title"] = title
                note["content"] = content
                _save_notes_to_file(notes_list)
                return True
        return False
    except Exception as e:
        print(f"Error updating note: {e}")
        return False


def delete_note(note_id: str) -> bool:
    """
    Delete a note.
    
    Args:
        note_id: The ID of the note to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        notes_list = load_notes()
        notes_list = [n for n in notes_list if n.get("id") != note_id]
        _save_notes_to_file(notes_list)
        return True
    except Exception as e:
        print(f"Error deleting note: {e}")
        return False


def get_note(note_id: str) -> Optional[Dict]:
    """
    Get a specific note by ID.
    
    Args:
        note_id: The ID of the note
        
    Returns:
        Note dictionary if found, None otherwise
    """
    notes_list = load_notes()
    for note in notes_list:
        if note.get("id") == note_id:
            return note
    return None


def search_notes(query: str) -> List[Dict]:
    """
    Search notes by title or content.
    
    Args:
        query: Search query
        
    Returns:
        List of matching notes
    """
    notes_list = load_notes()
    query_lower = query.lower()
    
    results = []
    for note in notes_list:
        if (query_lower in note.get("title", "").lower() or 
            query_lower in note.get("content", "").lower()):
            results.append(note)
    
    return results
