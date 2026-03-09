# --- Standard Library Imports ---
import json
import os
import uuid

# --- Local Imports ---
from . import config

TODOS_FILE = config.TODOS_FILE

def load_todos():
    """Loads todos from the JSON file."""
    if not os.path.exists(TODOS_FILE):
        return []
    try:
        with open(TODOS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_todos(todos):
    """Saves todos to the JSON file."""
    os.makedirs(os.path.dirname(TODOS_FILE), exist_ok=True)
    with open(TODOS_FILE, 'w') as f:
        json.dump(todos, f, indent=4)

def add_task(task_text):
    """Adds a new task."""
    todos = load_todos()
    new_task = {
        "id": str(uuid.uuid4()),
        "text": task_text,
        "completed": False
    }
    todos.append(new_task)
    save_todos(todos)
    return new_task

def delete_task(index):
    """Deletes a task by index."""
    todos = load_todos()
    if 0 <= index < len(todos):
        del todos[index]
        save_todos(todos)

def toggle_task(index):
    """Toggles the completion status of a task by index."""
    todos = load_todos()
    if 0 <= index < len(todos):
        todos[index]['completed'] = not todos[index]['completed']
        save_todos(todos)

def get_task(index):
    """Returns a task by index."""
    todos = load_todos()
    if 0 <= index < len(todos):
        return todos[index]
    return None
