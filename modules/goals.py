"""
Goals manager for Firefly AI.
Manages productivity goals with progress tracking.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict
from . import config


def _get_goals_file():
    """Get the goals file path."""
    return os.path.join(config.BASE_DIR, "goals.json")


def _load_goals_from_file() -> List[Dict]:
    """Load goals from file."""
    goals_file = _get_goals_file()
    if os.path.exists(goals_file):
        try:
            with open(goals_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_goals_to_file(goals: List[Dict]):
    """Save goals to file."""
    goals_file = _get_goals_file()
    os.makedirs(os.path.dirname(goals_file), exist_ok=True)
    with open(goals_file, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=2)


def load_goals() -> List[Dict]:
    """
    Load all goals.
    
    Returns:
        List of goal dictionaries with 'id', 'title', 'description', 'target_date', 'progress', 'completed'
    """
    goals = _load_goals_from_file()
    
    # Ensure all goals have required fields
    for goal in goals:
        if "id" not in goal:
            goal["id"] = str(uuid.uuid4())
        if "progress" not in goal:
            goal["progress"] = 0
        if "completed" not in goal:
            goal["completed"] = False
        if "target_date" not in goal:
            goal["target_date"] = None
    
    _save_goals_to_file(goals)  # Save back with defaults
    return goals


def add_goal(title: str, description: str = "", target_date: str = None) -> bool:
    """
    Add a new goal.
    
    Args:
        title: Goal title
        description: Optional description
        target_date: Optional target date (YYYY-MM-DD)
    
    Returns:
        True if added successfully
    """
    if not title.strip():
        return False
    
    goals = load_goals()
    new_goal = {
        "id": str(uuid.uuid4()),
        "title": title.strip(),
        "description": description.strip(),
        "target_date": target_date,
        "progress": 0,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    goals.append(new_goal)
    _save_goals_to_file(goals)
    return True


def update_goal_progress(goal_id: str, progress: int) -> bool:
    """
    Update goal progress.
    
    Args:
        goal_id: Goal ID
        progress: Progress percentage (0-100)
    
    Returns:
        True if updated successfully
    """
    progress = max(0, min(100, progress))
    goals = load_goals()
    for goal in goals:
        if goal["id"] == goal_id:
            goal["progress"] = progress
            if progress == 100:
                goal["completed"] = True
            _save_goals_to_file(goals)
            return True
    return False


def delete_goal(goal_id: str) -> bool:
    """
    Delete a goal.
    
    Args:
        goal_id: Goal ID
    
    Returns:
        True if deleted successfully
    """
    goals = load_goals()
    goals = [g for g in goals if g["id"] != goal_id]
    _save_goals_to_file(goals)
    return True


def toggle_goal_completion(goal_id: str) -> bool:
    """
    Toggle goal completion status.
    
    Args:
        goal_id: Goal ID
    
    Returns:
        True if toggled successfully
    """
    goals = load_goals()
    for goal in goals:
        if goal["id"] == goal_id:
            goal["completed"] = not goal["completed"]
            if goal["completed"]:
                goal["progress"] = 100
            _save_goals_to_file(goals)
            return True
    return False