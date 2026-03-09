import os
import sys
import importlib

# ensure project root is on sys.path so modules package can be imported
root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if root not in sys.path:
    sys.path.insert(0, root)

import tempfile

import modules.todo as todo


def test_todo_lifecycle(tmp_path):
    # patch the todo file path to a temp file location
    temp_file = tmp_path / "todos.json"
    todo._get_todo_file = lambda: str(temp_file)

    # nothing exists yet
    assert todo.load_todos() == []

    # add a couple of tasks
    id1 = todo.add_task("task one")
    id2 = todo.add_task("task two", priority="high")

    todos = todo.load_todos()
    assert len(todos) == 2
    assert todos[0]["id"] == id1
    assert todos[1]["id"] == id2
    assert todos[1]["priority"] == "high"
    assert not todos[0]["completed"]

    # toggle second task
    assert todo.toggle_task(1)
    todos = todo.load_todos()
    assert todos[1]["completed"] is True

    # get pending and completed lists
    pending = todo.get_pending_tasks()
    completed = todo.get_completed_tasks()
    assert len(pending) == 1
    assert len(completed) == 1

    # delete by id
    assert todo.delete_task(id1)
    todos = todo.load_todos()
    assert len(todos) == 1
    assert todos[0]["id"] == id2

    # toggling with bad index should return False
    assert not todo.toggle_task(10)

    # cleanup
    assert temp_file.exists()
    temp_file.unlink()
