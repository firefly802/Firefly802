# Contributing to Firefly AI

Thank you for your interest in contributing! Follow these guidelines to make
collaboration smooth and enjoyable.

## Getting Started

1. Fork the repository on GitHub and clone your fork locally.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate     # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```
3. Run the application to ensure it starts:
   ```bash
   python main.py
   ```

## Environment Variables

Sensitive settings (email credentials, API keys, etc.) should be provided via
environment variables or placed in a `.env` file (which is ignored by git).
An example file is provided as `.env.example`.

## Coding Standards

* Follow existing code style (PEP 8 / ruff). The project uses `customtkinter` in
  the GUI, so keep modifications consistent with the current design.
* Write docstrings for new functions/classes.
* Include tests for any new functionality (see the `tests/` folder).

## Testing

The project uses `pytest` for basic unit tests. To run the test suite:

```bash
pytest
```

Add new tests under the `tests/` directory.

## Submitting Changes

1. Create a new branch from `main` for your work.
2. Commit changes with clear messages.
3. Push to your fork and open a pull request.
4. Describe the purpose of your changes and reference any related issues.

Thanks again for helping improve Firefly AI! 
