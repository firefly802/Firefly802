# --- Standard Library Imports ---
import os

# --- Module Description ---
# This module stores configuration constants for the application.
# It includes file paths, model names, UI colors, themes, and feature-specific settings.

# --- Paths and Model ---
BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
MODEL_NAME = "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
model_path = os.path.join(BASE_DIR, "models", MODEL_NAME)
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "knowledge.txt")

# Legacy JSON files (kept for migration purposes)
TODOS_FILE = os.path.join(BASE_DIR, "todos.json")
REMINDERS_FILE = os.path.join(BASE_DIR, "reminders.json")
APPOINTMENTS_FILE = os.path.join(BASE_DIR, "appointments.json")
CONTACTS_FILE = os.path.join(BASE_DIR, "contacts.json")
NOTES_FILE = os.path.join(BASE_DIR, "notes.json")

# New Database File
DB_FILE = os.path.join(BASE_DIR, "firefly.db")

CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")  # Chat persistence

# --- GUI Colors ---
BG_COLOR = "#0f111a"
ACCENT_COLOR = "#007acc"
TEXT_COLOR = "#dcdcdc"
USER_COLOR = "#4fc1ff"
AI_COLOR = "#98c379"
ERROR_COLOR = "#ff5555"
BUTTON_BG = "#1e1e1e"
BUTTON_HOVER = "#333333"

# --- Theme Configurations ---
THEMES = {
    "Ocean Blue": "blue",
    "Forest Green": "green",
    "Ruby Red": "dark-blue",  # CustomTkinter has a reddish theme named 'dark-blue'
    "Amethyst Purple": "sweetkind",
}

# --- AI Personalities ---
PERSONALITIES = {
    "Default": "You are Firefly, a helpful and concise AI assistant.",
    "Jarvis": "You are J.A.R.V.I.S, a highly advanced and polite AI butler. Address the user as 'Sir' or 'Ma'am'. Be sophisticated and precise.",
    "Pirate": "You are Captain Firefly, a salty pirate AI. Use pirate slang like 'Ahoy', 'Matey', and 'Shiver me timbers'. Be adventurous but helpful.",
    "Cyberpunk": "You are a futuristic AI from the year 2077. Use slang like 'choom', 'nova', and 'preem'. Keep it edgy and tech-focused.",
    "Grumpy": "You are a reluctant AI assistant who thinks humans are inefficient. Complain slightly about the tasks but still do them correctly.",
    "Teacher": "You are a patient and encouraging tutor. Explain concepts simply and clearly, as if teaching a student. Use analogies.",
    "Coder": "You are a senior software engineer. Focus on technical details, code efficiency, and logic. Be brief and technical."
}

# --- Feature Configurations ---
# Email credentials are loaded from environment variables to avoid
# committing sensitive information. Users should define these in a
# .env file or their shell before launching the app. The example
# .env.example file shows the expected variable names.
# Support both EMAIL_ACCOUNT and EMAIL_ADDRESS for flexibility
EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT") or os.getenv("EMAIL_ADDRESS", "")
# Automatically strip spaces from the password to handle copy-paste errors with App Passwords
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "").replace(" ", "")

# Server settings
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

DATASET_PATH = os.path.join(BASE_DIR, "face_data_storage")

VOICE_OPTIONS = {
    "South Africa (Female)": "en-ZA-LeahNeural",
    "South Africa (Male)": "en-ZA-LukeNeural",
    "US (Female)": "en-US-AriaNeural",
    "US (Male)": "en-US-GuyNeural",
    "UK (Female)": "en-GB-SoniaNeural",
    "UK (Male)": "en-GB-RyanNeural",
}
