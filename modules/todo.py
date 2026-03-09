"""
To-do list manager for Firefly AI.
Manages tasks and completion status.
"""

import os
import json
import uuid
from typing import List, Dict
from . import config


def _get_todo_file():
    """Get the todo file path."""
    return os.path.join(config.BASE_DIR, "todos.json")


def _load_todos_from_file() -> List[Dict]:
    """Load todos from file."""
    todo_file = _get_todo_file()
    if os.path.exists(todo_file):
        try:
            with open(todo_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_todos_to_file(todos: List[Dict]):
    """Save todos to file."""
    todo_file = _get_todo_file()
    os.makedirs(os.path.dirname(todo_file), exist_ok=True)
    with open(todo_file, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2)


def load_todos() -> List[Dict]:
    """
    Load all todos.
    
    Returns:
        List of todo dictionaries with 'id', 'text', 'completed', and optionally 'priority'
    """
    todos = _load_todos_from_file()
    
    # Ensure all todos have required fields
    for todo in todos:
        if "id" not in todo:
            todo["id"] = str(uuid.uuid4())
        if "completed" not in todo:
            todo["completed"] = False
        if "text" not in todo:
            todo["text"] = ""
    
    return todos


def add_task(text: str, priority: str = "normal") -> str:
    """
    Add a new task.
    
    Args:
        text: Task description
        priority: Task priority (low, normal, high)
        
    Returns:
        The ID of the created task
    """
    todos = load_todos()
    task_id = str(uuid.uuid4())
    
    new_task = {
        "id": task_id,
        "text": text,
        "completed": False,
        "priority": priority
    }
    todos.append(new_task)
    _save_todos_to_file(todos)
    return task_id


def toggle_task(index: int) -> bool:
    """
    Toggle the completed status of a task by index.
    
    Args:
        index: Index of the task in the list
        
    Returns:
        True if successful, False otherwise
    """
    try:
        todos = load_todos()
        if 0 <= index < len(todos):
            todos[index]["completed"] = not todos[index].get("completed", False)
            _save_todos_to_file(todos)
            return True
        return False
    except Exception as e:
        print(f"Error toggling task: {e}")
        return False


def delete_task(task_id: str) -> bool:
    """
    Delete a task by ID.
    
    Args:
        task_id: The ID of the task to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        todos = load_todos()
        todos = [t for t in todos if t.get("id") != task_id]
        _save_todos_to_file(todos)
        return True
    except Exception as e:
        print(f"Error deleting task: {e}")
        return False


def get_pending_tasks() -> List[Dict]:
    """Get all pending (incomplete) tasks."""
    todos = load_todos()
    return [t for t in todos if not t.get("completed", False)]


def get_completed_tasks() -> List[Dict]:
    """Get all completed tasks."""
    todos = load_todos()
    return [t for t in todos if t.get("completed", False)]
