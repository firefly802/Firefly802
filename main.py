# --- Standard Library Imports ---
import os
import json
import ctypes
import threading
import webbrowser
import re
import random  # Added for randomized greetings
import datetime  # Added for daily quote
import time
import logging
from typing import Any
from dotenv import load_dotenv

# Load environment variables from .env file immediately
load_dotenv()

# --- Logging Setup ---
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firefly.log")


def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("Firefly")


logger = setup_logging()

# --- Third-Party Imports ---
import tkinter as tk
import customtkinter as ctk
import psutil

# Lazy load heavy libraries
# import wikipedia  <-- Moved to usage
try:
    from gpt4all import GPT4All
except ImportError:
    GPT4All = None
from tkinter import filedialog, messagebox  # Added for file dialog
# import cv2  <-- Moved to usage

# --- Local Module Imports ---
from modules import config
from modules import utils
from modules import commands
from modules import reminders  # Added for Reminders
from modules import dashboard  # Added for Daily Briefing
from modules import calendar_manager  # Added for Calendar
from modules import database  # Added for Database Initialization
from modules import notes_manager  # Added for Notes
from modules import email_client  # Added for Email Reader
from modules import goals  # Added for Goals
from modules import analytics  # Added for Analytics
from modules.utils import ToolTip, play_ui_sound  # Imported play_ui_sound

# Enable High DPI Awareness (Windows) - Makes GUI crisp and fixes screenshot/recording scaling
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore[attr-defined]
except AttributeError:
    pass


# --- Chat Persistence Functions (defined before use) ---
def load_chat_history():
    """Loads chat history from JSON file if it exists.

    Returns:
        List of tuples [(role, message), ...] or empty list if no history
    """
    # Use the same path variable as save_chat_history for consistency
    chat_file = config.CHAT_HISTORY_FILE
    if not os.path.exists(chat_file):
        return []
    try:
        with open(chat_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error loading chat history: {e}")
    return []


# Initialize AI as None for lazy loading (prevents startup freeze)
ai: Any = None
ai_preload_thread = None

# Set CustomTkinter Theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Global App Reference
app: Any = None

# Chat History for Context Awareness (load from file if exists)
chat_history = load_chat_history()
MAX_HISTORY = 6  # Keep last 3 exchanges (User + AI)
MAX_SAVED_HISTORY = 50  # Maximum entries to save to file

# Document Context for RAG
document_context = ""
MAX_DOCUMENT_SIZE = 1024 * 1024  # 1MB max document size

# Wake Word Listener
wake_word_active = False

# Loading States
AI_LOADING = True  # Track if AI is still loading
AI_LOADED = False  # Track if AI has finished loading
AI_AVAILABLE = False  # Track if AI model is available

# --- Randomized Greetings ---
GREETINGS = [
    "👩🏽‍💻 Firefly AI Assistant Ready... how can I light up your day?",
    "✨ Hello there! Firefly is online and eager to assist.",
    "💡 Greetings! Firefly here, ready to spark some solutions.",
    "🌟 Your personal AI assistant, Firefly, is at your service!",
    "🚀 Firefly is go! What adventure shall we embark on today?",
    "👋 Hey! Firefly's awake and ready to chat.",
    "🌈 Welcome back! Firefly's here to make things brighter.",
]

# --- Fallback greeting when AI is unavailable ---
FALLBACK_GREETINGS = [
    "👩🏽‍💻 Firefly Assistant Ready (Command Mode)... how can I help?",
    "⚡ Firefly in offline mode. Use commands to get things done!",
    "🛠️ Firefly is running in limited mode. Try commands like 'time', 'weather', or 'open notepad'.",
]


# --- Chat Persistence Functions ---
def save_chat_history(history):
    """Saves chat history to JSON file with size limit.

    Args:
        history: List of tuples [(role, message), ...]
    """
    try:
        # Limit saved history to prevent file from growing too large
        limited_history = (
            history[-MAX_SAVED_HISTORY:]
            if len(history) > MAX_SAVED_HISTORY
            else history
        )
        with open(config.CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(limited_history, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.warning(f"Error saving chat history: {e}")


def export_chat_history(filename, history):
    """Exports chat history to a text file.

    Args:
        filename: Path to export file
        history: Chat history list to export
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Firefly AI Chat History\n")
            f.write("=" * 50 + "\n\n")
            for role, msg in history:
                f.write(f"{role}: {msg}\n\n")
        return True
    except IOError as e:
        logger.warning(f"Error exporting chat history: {e}")
        return False


# --- Command Registry (Cleaner Architecture) ---
SIMPLE_COMMANDS = [
    (["time", "date"], commands.trigger_time),
    (["calculator"], commands.trigger_calc),
    (["lock screen", "lock computer"], commands.trigger_lock),
    (["screenshot"], commands.trigger_screenshot),
    (["system status", "cpu usage"], commands.trigger_system_health),
    (["timer"], commands.trigger_timer),
    (["password"], commands.trigger_password_gen),
    (["disk space"], commands.trigger_disk_usage),
    (["restart"], commands.trigger_restart),
    (["translate"], commands.trigger_translate),
    (["system info"], commands.trigger_system_info),
    (["ip address", "my ip"], commands.trigger_ip_info),
    (
        ["on this day"],
        lambda app: threading.Thread(
            target=commands.trigger_on_this_day, args=(app,), daemon=True
        ).start(),
    ),
    (["spark", "idea", "incubator"], commands.trigger_idea_incubator),
    (
        ["calendar"],
        lambda current_app: calendar_manager.trigger_calendar_view(current_app),
    ),
    (["downloads"], commands.trigger_downloads),
    (["notepad"], commands.trigger_notepad),
    (["battery report"], commands.trigger_battery_report),
    (["organize files"], commands.trigger_organize_files),
    (["news", "headlines"], commands.trigger_news),
    (["task manager"], commands.trigger_task_manager),
    (["control panel"], commands.trigger_control_panel),
    (["cmd"], commands.trigger_cmd),
    (["shutdown"], commands.trigger_shutdown),
    (["convert", "unit converter"], commands.trigger_unit_converter),
    (
        ["dashboard", "briefing"],
        lambda current_app: current_app.tabview.set("Home"),
    ),
    (
        ["pomodoro", "focus"],
        lambda current_app: commands.trigger_pomodoro(current_app),
    ),
    (["open chat", "chat"], commands.trigger_open_chat),
    (["open tools"], commands.trigger_open_tools),
    (["open todo", "todo", "tasks"], commands.trigger_open_todo),
    (["open reminders", "reminders"], commands.trigger_open_reminders),
    (["open goals", "goals"], commands.trigger_open_goals),
    (["open analytics", "analytics"], commands.trigger_open_analytics),
    (["open zen", "zen", "meditate"], commands.trigger_open_zen),
    (["open settings", "settings"], commands.trigger_open_settings),
]


def preload_ai_model():
    """Loads the AI model in a background thread to improve first-response time."""
    global ai, AI_LOADING, AI_LOADED, AI_AVAILABLE
    if not os.path.exists(config.model_path):
        logger.error(f"Model not found at {config.model_path}")
        AI_LOADING = False
        AI_AVAILABLE = False
        return
    try:
        logger.info("Pre-loading AI model... (This may take a minute)")
        # Update status indicator if app exists
        if app and hasattr(app, "update_ai_status"):
            app.after(0, app.update_ai_status, "loading")

        # Lazy import
        from gpt4all import GPT4All

        ai = GPT4All(config.model_path, allow_download=False, device="cpu")

        AI_LOADING = False
        AI_LOADED = True
        AI_AVAILABLE = True
        logger.info("AI model pre-loaded successfully.")
        if app and hasattr(app, "update_ai_status"):
            app.after(0, app.update_ai_status, "ready")
    except Exception as e:
        AI_LOADING = False
        AI_AVAILABLE = False
        logger.error(f"Failed to pre-load model: {e}")
        if app and hasattr(app, "update_ai_status"):
            app.after(0, app.update_ai_status, "error")


def generate_response(user_message, voice_mode=False):
    """
    Main logic handler:
    1. Checks for specific commands (Weather, Wiki, Search).
    2. Checks the SIMPLE_COMMANDS registry.
    3. If no command matches, generates a response using the AI model.
    """
    try:
        global ai, chat_history, document_context

        # Input validation - prevent crashes from invalid input
        if not user_message or not isinstance(user_message, str):
            return

        # Strip and validate message content
        user_message = user_message.strip()

        # Additional validation: minimum length
        if len(user_message) < 2:
            return

        # Remove control characters
        user_message = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", user_message)

        # Limit max length
        if len(user_message) > 10000:
            user_message = user_message[:10000]

        msg_lower = user_message.lower()

        # --- 1. Specific Command Checks ---

        # Weather Check - Get weather for specified city or default to Johannesburg
        if "weather" in msg_lower:
            city = (
                msg_lower.replace("weather", "")
                .replace("check", "")
                .replace(" in ", "")
                .strip()
                or "johannesburg"
            )
            try:
                weather_result = utils.get_weather_sa(city)
                utils.respond(app, weather_result, speak=True)
            except Exception as e:
                utils.respond(app, f"⚠️ Could not fetch weather: {str(e)}", tag="error")
            return

        # Simple Commands Registry - Check if message matches any registered commands
        for keywords, handler in SIMPLE_COMMANDS:
            if any(kw in msg_lower for kw in keywords):
                try:
                    app.after(0, handler, app)
                except Exception as e:
                    utils.respond(app, f"⚠️ Command error: {str(e)}", tag="error")
                return

        # Wikipedia Lookup - Search Wikipedia for topic
        if msg_lower.startswith("wiki") or "wikipedia" in msg_lower:
            topic = (
                user_message.lower()
                .replace("wikipedia", "")
                .replace("wiki", "")
                .strip()
            )
            if topic:
                try:
                    # Lazy import
                    import wikipedia

                    summary = wikipedia.summary(topic, sentences=2, auto_suggest=False)
                    utils.respond(app, summary, display_text=f"📚 Wikipedia: {summary}")
                except Exception as e:
                    utils.respond(app, f"⚠️ Wikipedia error: {str(e)}", tag="error")
            return

        # Google Search - Open Google search in browser
        if msg_lower.startswith("search for"):
            query = msg_lower.replace("search for", "").strip()
            if query:
                try:
                    webbrowser.open(f"https://www.google.com/search?q={query}")
                    utils.respond(app, f"✅ Searching for '{query}'...", speak=False)
                except Exception as e:
                    utils.respond(app, f"⚠️ Search error: {str(e)}", tag="error")
            else:
                try:
                    app.after(0, commands.trigger_google_search, app)
                except Exception as e:
                    utils.respond(app, f"⚠️ Error opening search: {str(e)}", tag="error")
            return

        # Abort Shutdown - Cancel pending shutdown
        if "abort" in msg_lower or "cancel shutdown" in msg_lower:
            try:
                os.system("shutdown /a")
                utils.respond(app, "Shutdown aborted.")
            except Exception as e:
                utils.respond(app, f"⚠️ Could not abort shutdown: {str(e)}", tag="error")
            return

        # --- 2. AI Generation (Fallback) ---

        # Check if the AI model is available
        if not AI_AVAILABLE:
            # Check if model is still loading
            if AI_LOADING:
                utils.respond(
                    app, "🔄 AI model is still loading, please wait...", speak=False
                )
                return

            # AI failed to load - offer command-only mode
            utils.respond(
                app,
                "⚠️ AI model is unavailable. You can still use commands like:\n"
                "• 'time', 'weather', 'joke'\n"
                "• 'open notepad', 'open youtube'\n"
                "• 'screenshot', 'password', 'timer'\n"
                "• Or check the Tools tab for more options.",
                tag="error",
                speak=False,
            )
            return

        # Load custom knowledge context
        knowledge_context = ""
        if os.path.exists(config.KNOWLEDGE_FILE):
            try:
                with open(config.KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    knowledge_context = f.read().strip()
            except IOError as e:
                logger.warning(f"Could not read knowledge file: {e}")
            except Exception as e:
                logger.warning(f"Error reading knowledge file: {e}")

        # --- Context Injection (New) ---
        # Gather dynamic context about the user's day
        now = datetime.datetime.now()
        today_str = now.date().isoformat()

        # 1. Appointments
        todays_appointments = database.get_appointments_for_date(today_str)
        appt_context = "No appointments today."
        if todays_appointments:
            appt_list = [
                f"- {a['time']}: {a['description']}" for a in todays_appointments
            ]
            appt_context = "Today's Appointments:\n" + "\n".join(appt_list)

        # 2. To-Dos
        pending_todos = [t for t in database.load_todos() if not t["completed"]]
        todo_context = "No pending tasks."
        if pending_todos:
            todo_list = [f"- {t['text']}" for t in pending_todos[:5]]  # Limit to top 5
            todo_context = "Top Pending Tasks:\n" + "\n".join(todo_list)

        # 3. Current Time
        time_context = (
            f"Current Date and Time: {now.strftime('%A, %B %d, %Y at %H:%M')}"
        )

        dynamic_context = f"{time_context}\n\n{appt_context}\n\n{todo_context}"

        # Determine System Prompt based on Personality
        selected_persona = app.selected_personality.get() if app else "Default"
        base_prompt = config.PERSONALITIES.get(
            selected_persona, config.PERSONALITIES["Default"]
        )

        # Construct the prompt with history and document context
        system_prompt = (
            f"{base_prompt}\n"
            "Answer the user's question directly and concisely. "
            "Do not offer follow-up questions, do not ask if there is anything else, and do not deviate from the topic. "
            "Stop generating immediately after answering the specific question asked.\n\n"
            "Use the following personal knowledge to answer if relevant:\n"
            f"{knowledge_context}\n\n"
            "Use the following real-time context about the user's day:\n"
            f"{dynamic_context}\n\n"
            "Use the following document content to answer if relevant:\n"
            f"{document_context}\n\n"
        )

        # Build conversation history string for context
        history_str = ""
        for role, msg in chat_history:
            history_str += f"### {role}:\n{msg}\n"

        # Construct full prompt with system instructions, history, and user message
        full_prompt = (
            f"### System:\n{system_prompt}\n"
            f"{history_str}"
            f"### User:\n{user_message}\n"
            f"### Assistant:\n"
        )

        # Streaming Response Logic - Display AI response in real-time
        response_text = ""

        # Set AI to processing state
        if app and hasattr(app, "update_ai_status"):
            app.after(0, app.update_ai_status, "processing")

        # Create a placeholder message bubble for the AI response
        app.after(0, app.add_message, "Firefly", "", "ai", True)

        # Generate tokens from AI model and stream them to UI
        try:
            for token in ai.generate(
                full_prompt, max_tokens=150, temp=0.7, streaming=True
            ):
                # Filter emojis for consistency with add_message
                clean_token = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27ff]", "", token)
                # Remove any model output markers that echo the prompt structure
                # (e.g. "### User", "### Assistant").
                clean_token = re.sub(r"###\s*(User|Assistant):?", "", clean_token)
                if not clean_token:
                    # skip if marker-only token
                    continue
                response_text += clean_token
                # Update the last message bubble with the new token
                app.after(0, app.update_last_message, clean_token)
        except Exception as e:
            if app and hasattr(app, "update_ai_status"):
                app.after(0, app.update_ai_status, "ready")
            utils.respond(
                app, f"⚠️ AI generation error: {str(e)}", tag="error", speak=False
            )
            return

        # Reset AI status back to ready
        if app and hasattr(app, "update_ai_status"):
            app.after(0, app.update_ai_status, "ready")

        # Final sanitization: ensure no leftover markers remain
        response_text = re.sub(r"###\s*(User|Assistant):?", "", response_text).strip()
        # Update chat history with the conversation (keep last N exchanges for context)
        chat_history.append(("User", user_message))
        chat_history.append(("Assistant", response_text))
        if len(chat_history) > MAX_HISTORY:
            chat_history = chat_history[-MAX_HISTORY:]

        # Save chat history to file for persistence
        save_chat_history(chat_history)

        # Speak the response using TTS if enabled
        try:
            utils.speak_text(app, response_text)
        except Exception as e:
            logger.warning(f"TTS error: {e}")

        # If in voice mode, trigger another voice input after response
        if voice_mode and app:
            app.after(0, lambda: trigger_voice_input(app))

    except Exception as e:
        utils.respond(
            app, f"⚠️ An unexpected error occurred: {str(e)}", tag="error", speak=False
        )


def send_message(_event=None, voice_mode=False):
    """Sends user message to AI and processes the response in a background thread."""
    if not app:
        return
    user_message = app.entry.get().strip()

    # Input validation
    if not user_message:
        return

    # Additional validation: minimum length and whitespace-only
    if len(user_message) < 2:
        app.add_message(
            "System",
            "⚠️ Message too short. Please enter at least 2 characters.",
            "error",
        )
        return

    # Remove control characters and normalize whitespace
    user_message = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", user_message)
    user_message = " ".join(user_message.split())  # Normalize whitespace

    # Add user message to chat UI
    try:
        app.add_message("You", user_message, "user")
        app.entry.delete(0, tk.END)
    except Exception as e:
        logger.error(f"Error updating UI: {e}")
        return

    try:
        play_ui_sound("MenuPopup")  # Play sound on message sent
    except Exception as e:
        logger.warning(f"Could not play sound: {e}")

    # Process message in background thread to keep UI responsive
    try:
        thread = threading.Thread(
            target=generate_response, args=(user_message, voice_mode)
        )
        thread.daemon = True
        thread.start()
    except Exception as e:
        app.add_message("System", f"⚠️ Failed to process message: {str(e)}", "error")


def clear_chat():
    """Clears chat history, document context, and resets the chat display."""
    global chat_history, document_context
    if app:
        app.clear_chat()
    chat_history = []  # Clear memory
    document_context = ""  # Clear document context

    # Clear saved chat history file
    save_chat_history([])

    if app:
        app.update_doc_status("No document loaded")


def train_bot():
    """Opens the knowledge file for the user to edit."""
    try:
        if not os.path.exists(config.KNOWLEDGE_FILE):
            with open(config.KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                f.write(
                    "Add facts here that you want Firefly to know.\nExample: My WiFi password is 1234.\nExample: My dog's name is Rover."
                )

        app.add_message("System", "🧠 Opening knowledge file...", "ai")
        os.startfile(config.KNOWLEDGE_FILE)
    except Exception as e:
        app.add_message("System", f"❌ Error opening knowledge file: {e}", "error")


def upload_document():
    """Allows user to upload a text file for RAG."""
    global document_context
    file_path = filedialog.askopenfilename(
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if file_path:
        try:
            # Check file size first
            file_size = os.path.getsize(file_path)
            if file_size > MAX_DOCUMENT_SIZE:
                app.add_message(
                    "System",
                    f"❌ File too large. Maximum size is {MAX_DOCUMENT_SIZE // 1024}KB.",
                    "error",
                )
                return

            with open(file_path, "r", encoding="utf-8") as f:
                document_context = f.read().strip()

            app.add_message(
                "System", f"📄 Loaded document: {os.path.basename(file_path)}", "ai"
            )
            app.update_doc_status(f"📄 {os.path.basename(file_path)}")
        except UnicodeDecodeError:
            app.add_message(
                "System", "❌ Cannot read file. Use UTF-8 encoded text files.", "error"
            )
        except Exception as e:
            app.add_message("System", f"❌ Failed to load document: {e}", "error")


def trigger_voice_input(current_app):
    """Starts voice input in a background thread for hands-free interaction."""
    threading.Thread(
        target=utils.listen_for_voice, args=(current_app, send_message), daemon=True
    ).start()


# --- Main GUI Class ---
class FireflyApp(ctk.CTk):
    """
    The main application class for the Firefly Assistant.
    Handles the GUI initialization, tab management, and settings.
    """

    def __init__(self):
        super().__init__()

        self.title("Firefly AI Assistant 💻❄️")
        self.geometry("1280x800")
        self.state("zoomed")

        # --- Splash Screen ---
        self.withdraw()  # Hide main window initially
        self.show_splash_screen()

        # Set Window Icon if available
        icon_path = os.path.join(config.BASE_DIR, "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # --- Load Settings ---
        self.settings_file = os.path.join(config.BASE_DIR, "settings.json")
        self.settings = self.load_settings()

        # Apply Global Settings
        ctk.set_appearance_mode(self.settings["appearance_mode"])
        ctk.set_default_color_theme(
            self.settings.get("color_theme", "blue")
        )  # Apply saved theme
        scale = int(self.settings["ui_scaling"].replace("%", "")) / 100
        ctk.set_widget_scaling(scale)

        # Settings Variables
        self.use_natural_voice = ctk.BooleanVar(
            master=self, value=self.settings["use_natural_voice"]
        )
        self.selected_voice = ctk.StringVar(
            master=self, value=self.settings["selected_voice"]
        )
        self.selected_theme = ctk.StringVar(
            master=self, value=self.settings.get("color_theme_name", "Ocean Blue")
        )  # New variable
        self.selected_personality = ctk.StringVar(
            master=self, value=self.settings.get("personality", "Default")
        )  # New variable for personality
        self.wake_word_enabled = ctk.BooleanVar(
            master=self, value=False
        )  # New variable for wake word

        # Font Settings
        self.font_family = ctk.StringVar(
            master=self, value=self.settings.get("font_family", "Segoe UI")
        )
        self.font_size = ctk.IntVar(
            master=self, value=self.settings.get("font_size", 12)
        )

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top Navigation
        self.nav_frame = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="ew")
        self.nav_frame.grid_columnconfigure(6, weight=1)

        self.logo = ctk.CTkLabel(
            self.nav_frame, text="Firefly AI", font=("Segoe UI", 18, "bold")
        )
        self.logo.grid(row=0, column=0, padx=20, pady=10)

        # Navigation buttons in top bar
        self.nav_buttons = {}
        nav_items = [
            ("🏠 Home", "Home"),
            ("💬 Chat", "Chat"),
            (" To-Do", "To-Do"),
            ("🔔 Reminders", "Reminders"),
            ("⚙️ Settings", "Settings"),
        ]
        for i, (text, tab_name) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self.nav_frame,
                text=text,
                command=lambda t=tab_name: self.tabview.set(t),
                width=100,
                height=30,
            )
            btn.grid(row=0, column=i + 1, padx=5, pady=10)
            self.nav_buttons[tab_name] = btn

        # System Stats in top right
        self.stats_frame = ctk.CTkFrame(self.nav_frame, fg_color="transparent")
        self.stats_frame.grid(row=0, column=7, padx=20, pady=10, sticky="e")

        self.ai_status_label = ctk.CTkLabel(
            self.stats_frame, text="AI: 🔄 Loading...", font=("Consolas", 10), width=100
        )
        self.ai_status_label.pack(side="left", padx=5)

        self.cpu_label = ctk.CTkLabel(
            self.stats_frame, text="CPU: 0%", font=("Consolas", 10), width=60
        )
        self.cpu_label.pack(side="left", padx=5)
        self.ram_label = ctk.CTkLabel(
            self.stats_frame, text="RAM: 0%", font=("Consolas", 10), width=60
        )
        self.ram_label.pack(side="left", padx=5)

        # Main Content Area
        self.tabview = ctk.CTkTabview(self, fg_color="transparent")
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        for tab in [
            "Home",
            "Chat",
            "Tools",
            "To-Do",
            "Reminders",
            "Goals",
            "Analytics",
            "Zen",
            "Settings",
        ]:
            self.tabview.add(tab)
        self.tabview._segmented_button.grid_forget()  # Hide segmented button

        # Initialize instance attributes to None or default values
        self.dashboard_frame = None  # Added dashboard frame
        self.chat_frame = None
        self.input_frame = None
        self.entry = None
        self.btn_mic = None
        self.btn_send = None
        self.btn_clear = None
        self.btn_train = None
        self.btn_upload = None  # New upload button
        self.doc_status_label = None  # New label for document status
        self.settings_frame = None
        self.appearance_mode_menu = None
        self.scaling_menu = None
        self.voice_switch = None
        self.voice_menu = None
        self.tts_speed_slider = None
        self.theme_menu = None  # New attribute
        self.personality_menu = None  # New attribute
        self.todo_entry = None  # New attribute
        self.todo_list_frame = None  # New attribute
        self.reminder_entry = None  # New attribute
        self.reminder_time_entry = None  # New attribute
        self.reminder_list_frame = None  # New attribute
        self.goals_frame = None  # New attribute for Goals
        self.goals_list_frame = None  # New attribute for Goals list
        self.goal_title_entry = None  # New attribute for Goals
        self.goal_desc_entry = None  # New attribute for Goals
        self.analytics_frame = None  # New attribute for Analytics
        self.last_message_label = None  # Track the last message label for streaming
        self.wake_word_switch = None  # New switch for wake word
        self.font_menu = None
        self.font_size_menu = None

        # Initialize missing attributes
        self.memory_warning_shown = False

        self.build_dashboard()  # Build Dashboard
        self.build_chat()
        self.build_tools()
        self.build_todo_tab()  # Build To-Do tab
        self.build_reminders_tab()  # Build Reminders tab
        self.build_goals_tab()  # Build Goals tab
        self.build_analytics()  # Build Analytics tab
        self.build_zen_tab()  # Build Zen tab
        self.build_settings()

        self.update_stats()

        # Schedule the AI pre-loading to start after the GUI is up and running
        self.after(100, FireflyApp.start_ai_preload)

        # Start reminder checking thread
        reminders.start_reminder_thread(self)

        # Register cleanup on window close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_splash_screen(self):
        """Displays a frameless splash screen using the main event loop."""
        splash = ctk.CTkToplevel(self)

        # Force fullscreen and remove decorations
        # Note: removed overrideredirect(True) to avoid conflict with fullscreen
        splash.attributes("-topmost", True)
        splash.attributes("-fullscreen", True)  # Use fullscreen attribute

        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Main background canvas for absolute positioning
        canvas = tk.Canvas(
            splash,
            width=screen_width,
            height=screen_height,
            bg="#0f111a",
            highlightthickness=0,
        )
        canvas.pack(fill="both", expand=True)

        # Calculate center
        cx = screen_width // 2
        cy = screen_height // 2

        # Draw Text
        canvas.create_text(
            cx,
            cy - 100,
            text="Firefly AI",
            font=("Segoe UI", 80, "bold"),
            fill="#007acc",
        )
        canvas.create_text(
            cx,
            cy,
            text="Illuminating the darkness...",
            font=("Segoe UI", 24, "italic"),
            fill="#dcdcdc",
        )

        # Draw Progress Bar (Simulated with rectangle)
        bar_width = 600
        bar_height = 15
        bar_x1 = cx - bar_width // 2
        bar_y1 = cy + 50
        bar_x2 = cx + bar_width // 2
        bar_y2 = bar_y1 + bar_height

        # Background of bar
        canvas.create_rectangle(
            bar_x1, bar_y1, bar_x2, bar_y2, fill="#1e1e1e", outline=""
        )

        # Progress indicator (will be updated)
        progress_rect = canvas.create_rectangle(
            bar_x1, bar_y1, bar_x1, bar_y2, fill="#007acc", outline=""
        )

        # Credits
        canvas.create_text(
            cx,
            screen_height - 50,
            text="Developed by Trevor Wilson\nrtwjasmynbakery@gmail.com",
            font=("Segoe UI", 16),
            fill="#aaaaaa",
            justify="center",
        )

        # Force update
        splash.update()

        def increment_progress(value=0.0):
            if value < 1.0:
                # Update progress bar width
                current_width = bar_width * value
                canvas.coords(
                    progress_rect, bar_x1, bar_y1, bar_x1 + current_width, bar_y2
                )

                # Update every 50ms, total time approx 5 seconds
                self.after(50, increment_progress, value + 0.01)
            else:
                splash.destroy()
                self.deiconify()  # Show main window
                try:
                    # On some systems the zoomed state is lost when the window is hidden;
                    # reapply it after showing the window.
                    self.state("zoomed")
                except Exception as e:
                    logger.warning(f"Error re-applying zoomed state: {e}")

        # Start the animation
        self.after(500, increment_progress, 0.0)

    def on_closing(self):
        """Cleanup resources before closing the application."""
        global wake_word_active, document_context, chat_history

        # Stop wake word listener
        wake_word_active = False

        # Save current chat history
        save_chat_history(chat_history)

        # Clear document context to free memory
        document_context = ""

        # Destroy the window
        self.destroy()

    @staticmethod
    def start_ai_preload():
        """Starts the AI pre-loading in a background thread."""
        global ai_preload_thread
        if ai_preload_thread is None:
            ai_preload_thread = threading.Thread(target=preload_ai_model, daemon=True)
            ai_preload_thread.start()

    def load_settings(self):
        """Loads application settings from JSON file or returns defaults.

        Returns:
            Dictionary containing all application settings
        """
        defaults = {
            "appearance_mode": "Dark",
            "ui_scaling": "100%",
            "use_natural_voice": False,
            "selected_voice": "South Africa (Female)",
            "tts_speed": 175,
            "color_theme": "blue",  # Default theme
            "color_theme_name": "Ocean Blue",
            "personality": "Default",
            "font_family": "Segoe UI",
            "font_size": 12,
        }

        # Expected types for validation
        expected_types = {
            "appearance_mode": str,
            "ui_scaling": str,
            "use_natural_voice": bool,
            "selected_voice": str,
            "tts_speed": (int, float),
            "color_theme": str,
            "color_theme_name": str,
            "personality": str,
            "font_family": str,
            "font_size": (int, float),
        }

        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    loaded = json.load(f)

                # Validate loaded settings
                if isinstance(loaded, dict):
                    for key, expected_type in expected_types.items():
                        if key in loaded:
                            value = loaded[key]
                            # Check if value matches expected type
                            if not isinstance(value, expected_type):
                                logger.warning(
                                    f"Invalid type for {key}: expected {expected_type}, got {type(value)}. Using default."
                                )
                                loaded[key] = defaults[key]
                    defaults.update(loaded)
                else:
                    logger.warning(
                        "Settings file contains invalid format. Using defaults."
                    )
            except json.JSONDecodeError:
                logger.warning("Settings file is corrupted. Using defaults.")
            except Exception as e:
                logger.warning(f"Error loading settings: {e}")
        return defaults

    def save_settings(self, _event=None):
        """Saves current application settings to JSON file."""
        try:
            data = {
                "appearance_mode": self.appearance_mode_menu.get(),
                "ui_scaling": self.scaling_menu.get(),
                "use_natural_voice": self.use_natural_voice.get(),
                "selected_voice": self.selected_voice.get(),                                                                
                                                                                                   "tts_speed": self.tts_speed_slider.get(),
                "color_theme": config.THEMES[self.selected_theme.get()],
                "color_theme_name": self.selected_theme.get(),
                "personality": self.selected_personality.get(),
                "font_family": self.font_family.get(),
                "font_size": self.font_size.get(),
            }
            with open(self.settings_file, "w") as f:
                json.dump(data, f, indent=4)
        except (IOError, TypeError) as e:
            logger.warning(f"Error saving settings: {e}")

    @staticmethod
    def generate_completion(prompt):
        """Exposes the AI model to other modules for text generation."""
        global ai, AI_AVAILABLE
        if ai is None:
            if os.path.exists(config.model_path):
                if GPT4All is None:
                    AI_AVAILABLE = False

                    return "GPT4All library not installed."

                try:
                    ai = GPT4All(config.model_path, allow_download=False, device="cpu")

                    AI_AVAILABLE = True

                except Exception as e:
                    AI_AVAILABLE = False

                    return f"AI unavailable: {str(e)}"

            else:
                AI_AVAILABLE = False

                return "AI model not found."

        try:
            return ai.generate(prompt, max_tokens=400, temp=0.7).strip()
        except Exception as e:
            AI_AVAILABLE = False
            return f"AI generation error: {str(e)}"

    def build_dashboard(self):
        """Builds the Home Dashboard tab."""
        self.dashboard_frame = dashboard.DashboardFrame(self.tabview.tab("Home"), self)
        self.dashboard_frame.pack(fill="both", expand=True)

    def build_chat(self):
        """Builds the Chat tab interface."""
        self.chat_frame = ctk.CTkScrollableFrame(
            self.tabview.tab("Chat"), label_text="Conversation"
        )
        self.chat_frame.pack(fill="both", expand=True, padx=0, pady=(0, 10))

        self.input_frame = ctk.CTkFrame(self.tabview.tab("Chat"))
        self.input_frame.pack(fill="x", padx=0, pady=0)

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type a message...",
            height=40,
            font=("Consolas", 14),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        self.entry.bind("<Return>", lambda e: send_message())

        self.btn_mic = ctk.CTkButton(
            self.input_frame,
            text="🎤",
            width=40,
            height=40,
            command=lambda: trigger_voice_input(self),
        )
        self.btn_mic.pack(side="left", padx=5)
        ToolTip(self.btn_mic, "Use voice input (requires Sphinx)")

        self.btn_send = ctk.CTkButton(
            self.input_frame, text="Send ➤", width=80, height=40, command=send_message
        )
        self.btn_send.pack(side="left", padx=5)
        ToolTip(self.btn_send, "Send your message to the AI")

        self.btn_clear = ctk.CTkButton(
            self.input_frame,
            text="🧹",
            width=40,
            height=40,
            fg_color="#ff5555",
            hover_color="#cc0000",
            command=clear_chat,
        )
        self.btn_clear.pack(side="left", padx=(5, 10))
        ToolTip(self.btn_clear, "Clear the chat history")

        self.btn_train = ctk.CTkButton(
            self.input_frame,
            text="🧠",
            width=40,
            height=40,
            fg_color="#bd93f9",
            hover_color="#9a76cc",
            command=train_bot,
        )
        self.btn_train.pack(side="left", padx=(0, 10))
        ToolTip(self.btn_train, "Open the knowledge file to add custom facts")

        self.btn_upload = ctk.CTkButton(
            self.input_frame,
            text="📄",
            width=40,
            height=40,
            fg_color="#ffb86c",
            hover_color="#ff9900",
            command=upload_document,
        )
        self.btn_upload.pack(side="left", padx=(0, 10))
        ToolTip(self.btn_upload, "Upload a text file to chat with")

        self.doc_status_label = ctk.CTkLabel(
            self.tabview.tab("Chat"),
            text="No document loaded",
            font=("Arial", 10),
            text_color="gray",
        )
        self.doc_status_label.pack(anchor="e", padx=10)

    def update_doc_status(self, text):
        if self.doc_status_label:
            self.doc_status_label.configure(text=text)

    def build_tools(self):
        """Builds the Tools tab with grouped command buttons."""
        scroll = ctk.CTkScrollableFrame(
            self.tabview.tab("Tools"), label_text="Command Center"
        )
        scroll.pack(fill="both", expand=True)

        # Iterate over tool groups and add them to the scrollable frame
        for title, tools in self._get_tool_definitions():
            self._add_tool_group(scroll, title, tools)

    @staticmethod
    def _add_tool_group(parent, title, buttons):
        """Helper to create a section of tool buttons."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame, text=title, font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=10, pady=5
        )

        grid = ctk.CTkFrame(frame, fg_color="transparent")
        grid.pack(fill="x", padx=5, pady=5)

        for i, (txt, cmd) in enumerate(buttons):
            # Extract text and tooltip
            if isinstance(txt, tuple):
                btn_text, tooltip_text = txt
            else:
                btn_text = txt
                tooltip_text = txt

            btn = ctk.CTkButton(grid, text=btn_text, command=cmd, height=35)
            btn.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky="ew")
            ToolTip(btn, tooltip_text)

        for i in range(4):
            grid.columnconfigure(i, weight=1)

    def launch_office_app(self, app_name, command):
        """Attempts to launch a Microsoft Office application."""
        try:
            os.startfile(command)
            self.add_message("System", f"🚀 Opening {app_name}...", "ai")
        except FileNotFoundError:
            self.add_message(
                "System", f"❌ Could not find {app_name}. Is it installed?", "error"
            )
        except Exception as e:
            self.add_message("System", f"❌ Error opening {app_name}: {e}", "error")

    def _get_tool_definitions(self):
        """Returns the data structure defining all tools and their commands."""
        return [
            (
                " Office Suite",
                [
                    (
                        ("📝 Word", "Open Microsoft Word"),
                        lambda: self.launch_office_app("Microsoft Word", "winword"),
                    ),
                    (
                        ("📊 Excel", "Open Microsoft Excel"),
                        lambda: self.launch_office_app("Microsoft Excel", "excel"),
                    ),
                    (
                        ("📽️ PowerPoint", "Open Microsoft PowerPoint"),
                        lambda: self.launch_office_app(
                            "Microsoft PowerPoint", "powerpnt"
                        ),
                    ),
                    (
                        ("📨 Outlook", "Open Outlook"),
                        lambda: self.launch_office_app("Outlook", "outlook"),
                    ),
                    (
                        ("🗒️ Notepad", "Open Notepad"),
                        lambda: commands.trigger_notepad(self),
                    ),
                    (
                        ("📂 Files", "Organize files in a folder"),
                        lambda: commands.trigger_organize_files(self),
                    ),
                ],
            ),
            (
                "⚙️ System Control",
                [
                    (
                        ("📊 Task Mgr", "Open Task Manager"),
                        lambda: commands.trigger_task_manager(self),
                    ),
                    (
                        ("⚙️ Control Panel", "Open Control Panel"),
                        lambda: commands.trigger_control_panel(self),
                    ),
                    (
                        ("💻 CMD", "Open Command Prompt"),
                        lambda: commands.trigger_cmd(self),
                    ),
                    (
                        ("🔒 Lock", "Lock the workstation"),
                        lambda: commands.trigger_lock(self),
                    ),
                    (
                        ("🛑 Shutdown", "Shutdown the computer"),
                        lambda: commands.trigger_shutdown(self),
                    ),
                    (
                        ("🔄 Restart", "Restart the computer"),
                        lambda: commands.trigger_restart(self),
                    ),
                ],
            ),
            (
                "🛠️ Utilities",
                [
                    (
                        ("⏳ Timer", "Set a timer"),
                        lambda: commands.trigger_timer(self),
                    ),
                    (
                        ("🧮 Calc", "Open Calculator"),
                        lambda: commands.trigger_calc(self),
                    ),
                    (
                        ("📸 Screenshot", "Take a screenshot"),
                        lambda: commands.trigger_screenshot(self),
                    ),
                    (
                        ("⚖️ Converter", "Convert units"),
                        lambda: commands.trigger_unit_converter(self),
                    ),
                    (
                        ("🔍 File Search", "Search for files"),
                        lambda: commands.trigger_file_search(self),
                    ),
                    (
                        ("📝 Summarizer", "Summarize text"),
                        lambda: commands.trigger_summarizer(self),
                    ),
                    (
                        ("🍅 Pomodoro", "Focus Timer"),
                        lambda: commands.trigger_pomodoro(self),
                    ),
                    (
                        (" Spark", "Idea Incubator"),
                        lambda: commands.trigger_idea_incubator(self),
                    ),
                ],
            ),
        ]

    def build_todo_tab(self):
        """Builds the To-Do List tab."""
        todo_tab = self.tabview.tab("To-Do")

        # Input Frame
        input_frame = ctk.CTkFrame(todo_tab)
        input_frame.pack(fill="x", padx=10, pady=10)

        self.todo_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Add a new task...", height=40
        )
        self.todo_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        self.todo_entry.bind("<Return>", lambda e: self.add_todo_task())

        add_btn = ctk.CTkButton(
            input_frame,
            text="Add Task",
            width=100,
            height=40,
            command=self.add_todo_task,
        )
        add_btn.pack(side="left", padx=(5, 10))

        # List Frame
        self.todo_list_frame = ctk.CTkScrollableFrame(todo_tab, label_text="Your Tasks")
        self.todo_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Controls
        control_frame = ctk.CTkFrame(todo_tab, fg_color="transparent")
        control_frame.pack(fill="x", padx=10, pady=10)

        clear_btn = ctk.CTkButton(
            control_frame,
            text="Clear Completed",
            fg_color="#ff5555",
            hover_color="#cc0000",
            command=self.clear_completed_todos,
        )
        clear_btn.pack(side="right")

        self.refresh_todo_list()

    def add_todo_task(self):
        task = self.todo_entry.get().strip()  # type: ignore
        if task:
            database.add_task(task)
            self.todo_entry.delete(0, tk.END)  # type: ignore
            self.refresh_todo_list()

    def refresh_todo_list(self):
        for widget in self.todo_list_frame.winfo_children():  # type: ignore
            widget.destroy()

        todos = database.load_todos()
        for i, task in enumerate(todos):
            frame = ctk.CTkFrame(self.todo_list_frame)
            frame.pack(fill="x", pady=2)

            var = ctk.BooleanVar(value=task["completed"])

            def toggle(index=i):
                database.toggle_task(index)
                self.refresh_todo_list()

            chk = ctk.CTkCheckBox(
                frame, text=task["text"], variable=var, command=toggle
            )
            if task["completed"]:
                chk.configure(text_color="gray")
            chk.pack(side="left", padx=10, pady=5)

    def clear_completed_todos(self):
        database.delete_completed_tasks()
        self.refresh_todo_list()

    def build_reminders_tab(self):
        """Builds the Reminders tab."""
        reminders_tab = self.tabview.tab("Reminders")

        # Input Frame
        input_frame = ctk.CTkFrame(reminders_tab)
        input_frame.pack(fill="x", padx=10, pady=10)

        self.reminder_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Remind me to...", height=40
        )
        self.reminder_entry.pack(
            side="left", fill="x", expand=True, padx=(10, 5), pady=10
        )

        self.reminder_time_entry = ctk.CTkEntry(
            input_frame, placeholder_text="In (mins)...", width=100, height=40
        )
        self.reminder_time_entry.pack(side="left", padx=(0, 5), pady=10)

        add_btn = ctk.CTkButton(
            input_frame,
            text="Set Reminder",
            width=120,
            height=40,
            command=self.add_reminder,
        )
        add_btn.pack(side="left", padx=(5, 10))

        # List Frame
        self.reminder_list_frame = ctk.CTkScrollableFrame(
            reminders_tab, label_text="Upcoming Reminders"
        )
        self.reminder_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_reminder_list()

    def add_reminder(self):
        text = self.reminder_entry.get().strip()  # type: ignore
        time_str = self.reminder_time_entry.get().strip()  # type: ignore

        if not text or not time_str:
            return

        try:
            minutes = float(time_str)
            remind_at = datetime.datetime.now().timestamp() + (minutes * 60)
            database.add_reminder(text, remind_at)

            self.reminder_entry.delete(0, tk.END)  # type: ignore
            self.reminder_time_entry.delete(0, tk.END)  # type: ignore
            self.refresh_reminder_list()

            self.add_message(
                "System", f"🔔 Reminder set for {minutes} minutes from now.", "ai"
            )
        except ValueError:
            self.add_message(
                "System",
                "❌ Invalid time format. Please enter minutes as a number.",
                "error",
            )

    def refresh_reminder_list(self):
        for widget in self.reminder_list_frame.winfo_children():
            widget.destroy()

        all_reminders = database.load_reminders()
        # Filter out completed reminders for the list
        active_reminders = [r for r in all_reminders if not r["completed"]]

        if not active_reminders:
            ctk.CTkLabel(
                self.reminder_list_frame,
                text="No upcoming reminders.",
                text_color="gray",
            ).pack(pady=20)
            return

        for r in active_reminders:
            frame = ctk.CTkFrame(self.reminder_list_frame)
            frame.pack(fill="x", pady=2)

            dt = datetime.datetime.fromtimestamp(r["remind_at"])
            time_str = dt.strftime("%H:%M")

            ctk.CTkLabel(
                frame, text=f"⏰ {time_str}", font=("Consolas", 12, "bold"), width=60
            ).pack(side="left", padx=10)
            ctk.CTkLabel(frame, text=r["text"], font=("Segoe UI", 12)).pack(
                side="left", padx=10
            )

    def build_goals_tab(self):
        """Builds the Goals tab."""
        goals_tab = self.tabview.tab("Goals")

        # Input Frame
        input_frame = ctk.CTkFrame(goals_tab)
        input_frame.pack(fill="x", padx=10, pady=10)

        self.goal_title_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Goal title...", height=40
        )
        self.goal_title_entry.pack(
            side="left", fill="x", expand=True, padx=(10, 5), pady=10
        )

        self.goal_desc_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Description (optional)", height=40
        )
        self.goal_desc_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 5), pady=10
        )

        add_btn = ctk.CTkButton(
            input_frame,
            text="Add Goal",
            width=100,
            height=40,
            command=self.add_goal,
        )
        add_btn.pack(side="left", padx=(5, 10))

        # List Frame
        self.goals_list_frame = ctk.CTkScrollableFrame(
            goals_tab, label_text="Your Goals"
        )
        self.goals_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_goals_list()

    def add_goal(self):
        title = self.goal_title_entry.get().strip()
        desc = self.goal_desc_entry.get().strip()

        if not title:
            return

        if goals.add_goal(title, desc):
            self.goal_title_entry.delete(0, tk.END)
            self.goal_desc_entry.delete(0, tk.END)
            self.refresh_goals_list()
            self.add_message("System", f"🎯 Goal added: {title}", "ai")
        else:
            self.add_message("System", "❌ Failed to add goal.", "error")

    def refresh_goals_list(self):
        for widget in self.goals_list_frame.winfo_children():
            widget.destroy()

        all_goals = goals.load_goals()

        if not all_goals:
            ctk.CTkLabel(
                self.goals_list_frame,
                text="No goals set yet. Add your first goal above!",
                text_color="gray",
            ).pack(pady=20)
            return

        for g in all_goals:
            frame = ctk.CTkFrame(self.goals_list_frame)
            frame.pack(fill="x", pady=2)

            # Title and description
            title_label = ctk.CTkLabel(
                frame, text=g["title"], font=("Segoe UI", 14, "bold")
            )
            title_label.pack(anchor="w", padx=10, pady=5)

            if g["description"]:
                desc_label = ctk.CTkLabel(
                    frame,
                    text=g["description"],
                    font=("Segoe UI", 12),
                    text_color="gray",
                )
                desc_label.pack(anchor="w", padx=10, pady=(0, 5))

            # Progress bar
            progress_frame = ctk.CTkFrame(frame, fg_color="transparent")
            progress_frame.pack(fill="x", padx=10, pady=5)

            progress_label = ctk.CTkLabel(
                progress_frame,
                text=f"Progress: {g['progress']}%",
                font=("Segoe UI", 12),
            )
            progress_label.pack(side="left")

            progress_bar = ctk.CTkProgressBar(progress_frame, width=200, height=15)
            progress_bar.pack(side="right", padx=10)
            progress_bar.set(g["progress"] / 100.0)

            # Controls
            controls_frame = ctk.CTkFrame(frame, fg_color="transparent")
            controls_frame.pack(fill="x", padx=10, pady=5)

            update_btn = ctk.CTkButton(
                controls_frame,
                text="Update Progress",
                width=120,
                height=30,
                command=lambda gid=g["id"]: self.update_goal_progress(gid),
            )
            update_btn.pack(side="left", padx=5)

            toggle_btn = ctk.CTkButton(
                controls_frame,
                text="Mark Complete" if not g["completed"] else "Mark Incomplete",
                width=120,
                height=30,
                fg_color="#50fa7b" if g["completed"] else "#ffb86c",
                command=lambda gid=g["id"]: self.toggle_goal_completion(gid),
            )
            toggle_btn.pack(side="left", padx=5)

            delete_btn = ctk.CTkButton(
                controls_frame,
                text="Delete",
                width=80,
                height=30,
                fg_color="#ff5555",
                command=lambda gid=g["id"]: self.delete_goal(gid),
            )
            delete_btn.pack(side="right", padx=5)

    def update_goal_progress(self, goal_id):
        # Simple dialog to update progress
        progress = ctk.CTkInputDialog(
            text="Enter progress (0-100):", title="Update Progress"
        ).get_input()
        if progress:
            try:
                p = int(progress)
                if 0 <= p <= 100:
                    if goals.update_goal_progress(goal_id, p):
                        self.refresh_goals_list()
                        self.add_message("System", "🎯 Goal progress updated!", "ai")
                    else:
                        self.add_message(
                            "System", "❌ Failed to update progress.", "error"
                        )
                else:
                    self.add_message(
                        "System", "❌ Progress must be between 0 and 100.", "error"
                    )
            except ValueError:
                self.add_message("System", "❌ Invalid progress value.", "error")

    def toggle_goal_completion(self, goal_id):
        if goals.toggle_goal_completion(goal_id):
            self.refresh_goals_list()
            self.add_message("System", "🎯 Goal status updated!", "ai")
        else:
            self.add_message("System", "❌ Failed to update goal.", "error")

    def delete_goal(self, goal_id):
        if messagebox.askyesno("Confirm", "Delete this goal?"):
            if goals.delete_goal(goal_id):
                self.refresh_goals_list()
                self.add_message("System", "🗑️ Goal deleted.", "ai")
            else:
                self.add_message("System", "❌ Failed to delete goal.", "error")

    def build_settings(self):
        """Builds the Settings tab."""
        self.settings_frame = ctk.CTkFrame(self.tabview.tab("Settings"))
        self.settings_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        ctk.CTkLabel(
            self.settings_frame,
            text="Application Settings",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=20, anchor="w", padx=20)

        # Grid Layout for settings
        grid = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        grid.pack(fill="x", padx=20)

        # Appearance Mode
        ctk.CTkLabel(grid, text="Appearance Mode:", font=("Segoe UI", 14)).grid(
            row=0, column=0, padx=10, pady=15, sticky="w"
        )
        self.appearance_mode_menu = ctk.CTkOptionMenu(
            grid,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode,
        )
        self.appearance_mode_menu.grid(row=0, column=1, padx=10, pady=15)
        self.appearance_mode_menu.set(self.settings["appearance_mode"])
        ToolTip(self.appearance_mode_menu, "Change the application's color theme.")

        # Color Theme (New)
        ctk.CTkLabel(grid, text="Color Theme:", font=("Segoe UI", 14)).grid(
            row=1, column=0, padx=10, pady=15, sticky="w"
        )
        self.theme_menu = ctk.CTkOptionMenu(
            grid,
            variable=self.selected_theme,
            values=list(config.THEMES.keys()),
            command=self.change_color_theme,
        )
        self.theme_menu.grid(row=1, column=1, padx=10, pady=15)
        ToolTip(self.theme_menu, "Change the accent color of the application.")

        # AI Personality (New)
        ctk.CTkLabel(grid, text="AI Personality:", font=("Segoe UI", 14)).grid(
            row=2, column=0, padx=10, pady=15, sticky="w"
        )
        self.personality_menu = ctk.CTkOptionMenu(
            grid,
            variable=self.selected_personality,
            values=list(config.PERSONALITIES.keys()),
            command=self.save_settings,
        )
        self.personality_menu.grid(row=2, column=1, padx=10, pady=15)
        ToolTip(self.personality_menu, "Choose the AI's personality and tone.")

        # UI Scaling
        ctk.CTkLabel(grid, text="UI Scaling:", font=("Segoe UI", 14)).grid(
            row=3, column=0, padx=10, pady=15, sticky="w"
        )
        self.scaling_menu = ctk.CTkOptionMenu(
            grid,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling,
        )
        self.scaling_menu.grid(row=3, column=1, padx=10, pady=15)
        self.scaling_menu.set(self.settings["ui_scaling"])
        ToolTip(self.scaling_menu, "Adjust the size of all UI elements.")

        # Voice Settings
        ctk.CTkLabel(grid, text="Voice Engine:", font=("Segoe UI", 14)).grid(
            row=4, column=0, padx=10, pady=15, sticky="w"
        )
        self.voice_switch = ctk.CTkSwitch(
            grid,
            text="Use Natural Voice (Online)",
            variable=self.use_natural_voice,
            onvalue=True,
            offvalue=False,
            command=self.save_settings,
        )
        self.voice_switch.grid(row=4, column=1, padx=10, pady=15, sticky="w")
        ToolTip(
            self.voice_switch,
            "Use a more natural-sounding online voice (requires internet).",
        )

        ctk.CTkLabel(grid, text="Natural Voice Accent:", font=("Segoe UI", 14)).grid(
            row=5, column=0, padx=10, pady=15, sticky="w"
        )
        self.voice_menu = ctk.CTkOptionMenu(
            grid,
            variable=self.selected_voice,
            values=list(config.VOICE_OPTIONS.keys()),
            command=self.save_settings,
        )
        self.voice_menu.grid(row=5, column=1, padx=10, pady=15)
        ToolTip(self.voice_menu, "Select the accent for the natural voice.")

        # Wake Word
        ctk.CTkLabel(grid, text="Wake Word Detection:", font=("Segoe UI", 14)).grid(
            row=6, column=0, padx=10, pady=15, sticky="w"
        )
        self.wake_word_switch = ctk.CTkSwitch(
            grid,
            text="Listen for 'Hey Firefly'",
            variable=self.wake_word_enabled,
            onvalue=True,
            offvalue=False,
            command=self.toggle_wake_word,
        )
        self.wake_word_switch.grid(row=6, column=1, padx=10, pady=15, sticky="w")
        ToolTip(self.wake_word_switch, "Enable hands-free activation (Experimental).")

        # TTS Speed
        ctk.CTkLabel(grid, text="Offline Speed (TTS):", font=("Segoe UI", 14)).grid(
            row=7, column=0, padx=10, pady=15, sticky="w"
        )
        self.tts_speed_slider = ctk.CTkSlider(
            grid, from_=100, to=300, number_of_steps=20, command=self.change_tts_rate
        )
        self.tts_speed_slider.grid(row=7, column=1, padx=10, pady=15)
        self.tts_speed_slider.set(self.settings["tts_speed"])
        self.tts_speed_slider.bind("<ButtonRelease-1>", lambda _e: self.save_settings())
        ToolTip(
            self.tts_speed_slider,
            "Adjust the speed of the offline text-to-speech voice.",
        )

        if utils.tts_engine:
            utils.tts_engine.setProperty("rate", int(self.settings["tts_speed"]))

        # Font Settings
        ctk.CTkLabel(grid, text="Chat Font:", font=("Segoe UI", 14)).grid(
            row=8, column=0, padx=10, pady=15, sticky="w"
        )
        self.font_menu = ctk.CTkOptionMenu(
            grid,
            variable=self.font_family,
            values=[
                "Segoe UI",
                "Arial",
                "Consolas",
                "Times New Roman",
                "Helvetica",
                "Roboto",
            ],
            command=self.save_settings,
        )
        self.font_menu.grid(row=8, column=1, padx=10, pady=15)
        ToolTip(self.font_menu, "Change the font family for chat messages.")

        ctk.CTkLabel(grid, text="Font Size:", font=("Segoe UI", 14)).grid(
            row=9, column=0, padx=10, pady=15, sticky="w"
        )
        self.font_size_menu = ctk.CTkOptionMenu(
            grid,
            variable=self.font_size,
            values=[str(i) for i in range(10, 32, 2)],
            command=self.save_settings,
        )
        self.font_size_menu.grid(row=9, column=1, padx=10, pady=15)
        ToolTip(self.font_size_menu, "Change the font size for chat messages.")

        # About Section
        ctk.CTkLabel(
            self.settings_frame, text="About Firefly AI", font=("Segoe UI", 16, "bold")
        ).pack(pady=(40, 10), anchor="w", padx=20)
        about_text = "Version: 2.3\nDeveloped by: Trevor Wilson\nContact: rtwjasmynbakery@gmail.com\nPowered by: GPT4All, OpenCV, & CustomTkinter"
        ctk.CTkLabel(
            self.settings_frame, text=about_text, justify="left", font=("Consolas", 12)
        ).pack(anchor="w", padx=20)

    def toggle_wake_word(self):
        global wake_word_active
        if self.wake_word_enabled.get():
            wake_word_active = True
            threading.Thread(target=self.listen_for_wake_word, daemon=True).start()
        else:
            wake_word_active = False

    def listen_for_wake_word(self):
        """
        Continuously listens for the wake word 'Hey Firefly'.
        Uses a simple loop with the existing speech recognition if possible.
        """
        global wake_word_active
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        while wake_word_active:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    try:
                        audio = recognizer.listen(
                            source, timeout=2, phrase_time_limit=3
                        )
                        text = recognizer.recognize_sphinx(audio).lower()  # type: ignore

                        if "firefly" in text:
                            play_ui_sound("MenuPopup")
                            self.after(0, lambda: trigger_voice_input(self))
                            # Pause listening while processing command
                            while self.btn_mic.cget("state") == "disabled":
                                time.sleep(0.5)

                    except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
                        pass
            except Exception as e:
                logger.debug(f"Exception in wake word listener loop: {e}")

            # Small delay to prevent CPU hogging
            time.sleep(0.1)

    def build_analytics(self):
        """Builds the Analytics tab."""
        self.analytics_frame = analytics.AnalyticsFrame(self.tabview.tab("Analytics"), self)

    def build_zen_tab(self):
        """Builds the Zen tab for mindfulness exercises."""
        zen_tab = self.tabview.tab("Zen")

        # Main frame for centering content
        center_frame = ctk.CTkFrame(zen_tab, fg_color="transparent")
        center_frame.pack(expand=True)

        self.zen_canvas = tk.Canvas(
            center_frame,
            width=300,
            height=300,
            bg=self._apply_appearance_mode(
                ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
            ),
            highlightthickness=0,
        )
        self.zen_canvas.pack(pady=20)

        self.zen_circle = self.zen_canvas.create_oval(
            100, 100, 200, 200, fill="#007acc", outline=""
        )

        self.zen_label = ctk.CTkLabel(
            center_frame, text="Press Start to begin.", font=("Segoe UI", 18)
        )
        self.zen_label.pack(pady=10)

        self.zen_button = ctk.CTkButton(
            center_frame,
            text="Start",
            width=120,
            height=40,
            font=("Segoe UI", 16),
            command=self.start_breathing_exercise,
        )
        self.zen_button.pack(pady=20)

        # Initialize breathing exercise state variables
        self.breathing_cycles_completed = 0
        self.max_breathing_cycles = 10

    def start_breathing_exercise(self):
        """Controls the animation sequence for the breathing exercise."""
        self.zen_button.configure(state="disabled", text="In Progress...")
        self.breathing_cycles_completed = 0  # Reset counter for a new session

        min_radius, max_radius = 50, 150
        center_x, center_y = 150, 150

        def update_circle(radius):
            self.zen_canvas.coords(
                self.zen_circle,
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            )

        def animate_phase(
            current_radius, target_radius, step, duration_ms, next_phase_func
        ):
            if (step > 0 and current_radius < target_radius) or (
                step < 0 and current_radius > target_radius
            ):
                new_radius = current_radius + step
                update_circle(new_radius)
                self.after(
                    duration_ms,
                    lambda: animate_phase(
                        new_radius, target_radius, step, duration_ms, next_phase_func
                    ),
                )
            else:
                update_circle(target_radius)
                if next_phase_func:
                    next_phase_func()

        def phase_inhale():
            self.zen_label.configure(
                text=f"Breathe In... ({self.breathing_cycles_completed + 1}/{self.max_breathing_cycles})"
            )
            animate_phase(min_radius, max_radius, 1, 25, phase_hold_inhaled)

        def phase_hold_inhaled():
            self.zen_label.configure(text="Hold...")
            self.after(2000, phase_exhale)

        def phase_exhale():
            self.zen_label.configure(text="Breathe Out...")
            animate_phase(max_radius, min_radius, -1, 35, phase_hold_exhaled)

        def phase_hold_exhaled():
            self.breathing_cycles_completed += 1
            if self.breathing_cycles_completed >= self.max_breathing_cycles:
                self.zen_label.configure(text="Exercise Complete!")
                self.zen_button.configure(state="normal", text="Start")
                update_circle(min_radius)  # Reset circle size
            else:
                self.zen_label.configure(text="Hold...")
                self.after(2000, phase_inhale)  # Loop back to inhale

        # Start the cycle
        phase_inhale()

    def add_message(self, _sender, message, tag, streaming=False):
        """Adds a message bubble to the chat display.

        Args:
            _sender: The sender of the message (unused, for API consistency).
            message: The message content
            tag: Message type (user, ai, error)
            streaming: If True, creates a placeholder for real-time updates
        """
        # Remove emojis from the message
        message = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27ff]", "", message).strip()

        # Set alignment and color based on message type
        align = "e" if tag == "user" else "w"
        color = "#1f538d" if tag == "user" else "#2b2b2b"
        if tag == "error":
            color = "#ff5555"

        # Create message bubble frame
        bubble = ctk.CTkFrame(self.chat_frame, fg_color=color)
        bubble.pack(pady=5, padx=10, anchor=align)

        # Check for code blocks (render in special frame)
        parts = re.split(r"(```.*?```)", message, flags=re.DOTALL)

        # If streaming and message is empty, create placeholder for updates
        if streaming and not message:
            lbl = ctk.CTkLabel(
                bubble,
                text="",
                font=(self.font_family.get(), self.font_size.get()),
                wraplength=600,
                justify="left",
            )
            lbl.pack(padx=10, pady=5, anchor="w")
            self.last_message_label = lbl
            return

        # Process each part of the message (code blocks and regular text)
        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                # Code block - display in dark themed frame
                code_content = part[3:-3].strip()
                code_frame = ctk.CTkFrame(bubble, fg_color="#1e1e1e", corner_radius=5)
                code_frame.pack(padx=5, pady=5, fill="x")

                code_font = ("Consolas", 11)
                code_label = ctk.CTkLabel(
                    code_frame,
                    text=code_content,
                    font=code_font,
                    justify="left",
                    text_color="#d4d4d4",
                )
                code_label.pack(padx=10, pady=5, anchor="w")
            else:
                # Normal text
                if part.strip():
                    lbl = ctk.CTkLabel(
                        bubble,
                        text=part.strip(),
                        font=(self.font_family.get(), self.font_size.get()),
                        wraplength=600,
                        justify="left",
                    )
                    lbl.pack(padx=10, pady=5, anchor="w")
                    if streaming:
                        self.last_message_label = lbl

        # Play sound for AI responses
        if tag == "ai" and not streaming:
            play_ui_sound("WindowsDing")

        # Auto scroll
        self.after_idle(lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def update_last_message(self, token):
        """Updates the last AI message with a new token during streaming.
        Handles switching between normal text and code blocks dynamically.
        """
        if not self.last_message_label:
            return

        # Check if the token triggers a code block toggle
        if "```" in token:
            bubble = self.last_message_label.master
            parts = token.split("```")

            for i, part in enumerate(parts):
                # Update current active label with text before/after the delimiter
                if part:
                    current_text = self.last_message_label.cget("text")
                    self.last_message_label.configure(text=current_text + part)

                # If there are more parts, it means we hit a delimiter
                if i < len(parts) - 1:
                    # Determine if the current active label is in a code frame
                    is_in_code = (
                        isinstance(self.last_message_label.master, ctk.CTkFrame)
                        and self.last_message_label.master != bubble
                    )

                    if not is_in_code:
                        # Start code block
                        code_frame = ctk.CTkFrame(
                            bubble, fg_color="#1e1e1e", corner_radius=5
                        )
                        code_frame.pack(padx=5, pady=5, fill="x")
                        self.last_message_label = ctk.CTkLabel(
                            code_frame,
                            text="",
                            font=("Consolas", 11),
                            justify="left",
                            text_color="#d4d4d4",
                        )
                        self.last_message_label.pack(padx=10, pady=5, anchor="w")
                    else:
                        # End code block, return to normal text
                        self.last_message_label = ctk.CTkLabel(
                            bubble,
                            text="",
                            font=(self.font_family.get(), self.font_size.get()),
                            wraplength=600,
                            justify="left",
                        )
                        self.last_message_label.pack(padx=10, pady=5, anchor="w")
        else:
            # Normal append to the current active label
            current_text = self.last_message_label.cget("text")
            self.last_message_label.configure(text=current_text + token)

        self.after_idle(lambda: self.chat_frame._parent_canvas.yview_moveto(1.0))

    def clear_chat(self):
        """Clears all messages from the chat display and shows a random greeting."""
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        self.add_message("AI", random.choice(GREETINGS), "ai")  # Use random greeting

    def reload_chat(self):
        """Reloads chat history from file and displays it."""
        global chat_history
        chat_history = load_chat_history()
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
        if chat_history:
            for role, msg in chat_history:
                tag = "user" if role == "User" else "ai"
                self.add_message(role, msg, tag)
        else:
            self.add_message("AI", random.choice(GREETINGS), "ai")

    def export_chat(self):
        """Exports chat history to a text file."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="firefly_chat_history.txt",
        )
        if filename:
            if export_chat_history(filename, chat_history):
                self.add_message(
                    "System", f"✅ Chat history exported to {filename}", "ai"
                )
            else:
                self.add_message("System", "❌ Failed to export chat history", "error")

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        self.save_settings()

    def change_color_theme(self, new_theme_name: str):
        theme_color = config.THEMES.get(new_theme_name, "blue")
        ctk.set_default_color_theme(theme_color)
        self.save_settings()
        # Note: CustomTkinter requires a restart to fully apply a new color theme to existing widgets,
        # but we can save it for the next launch.
        messagebox.showinfo(
            "Restart Required",
            "Please restart Firefly for the new color theme to take full effect.",
        )

    def change_scaling(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
        self.save_settings()

    @staticmethod
    def change_tts_rate(value):
        if utils.tts_engine:
            utils.tts_engine.setProperty("rate", int(value))

    def update_ai_status(self, status):
        """Updates the AI status indicator in the sidebar.

        Args:
            status: One of 'loading', 'ready', 'error', 'processing'
        """
        status_messages = {
            "loading": "AI: 🔄 Loading...",
            "ready": "AI: ✅ Ready",
            "error": "AI: ❌ Error",
            "processing": "AI: ⚙️ Thinking...",
        }
        if hasattr(self, "ai_status_label"):
            self.ai_status_label.configure(
                text=status_messages.get(status, "AI: Unknown")
            )

    def update_stats(self):
        """Updates CPU, RAM, and memory usage display every 2 seconds."""
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            if hasattr(self, "cpu_label") and self.cpu_label:
                self.cpu_label.configure(text=f"CPU: {cpu}%")
            if hasattr(self, "ram_label") and self.ram_label:
                self.ram_label.configure(text=f"RAM: {ram}%")

            # Memory warning if RAM usage is high
            if ram > 90 and not self.memory_warning_shown:
                self.after(
                    0,
                    lambda: self.add_message(
                        "System",
                        "⚠️ High memory usage detected (>90%). Performance may be affected.",
                        "error",
                    ),
                )
                self.memory_warning_shown = True
            elif ram < 85:
                self.memory_warning_shown = False

        except Exception as e:
            logger.warning(f"Error updating stats: {e}")
        self.after(2000, self.update_stats)


def main():
    global app
    # Initialize the database before starting the app
    database.initialize_database()

    utils.initialize_tts()
    app = FireflyApp()

    # Load chat history into UI or show greeting
    if chat_history:
        # Display previous conversation history
        for role, msg in chat_history:
            tag = "user" if role == "User" else "ai"
            app.add_message(role, msg, tag)
    else:
        # No previous history, show appropriate greeting
        if AI_AVAILABLE:
            app.add_message("AI", random.choice(GREETINGS), "ai")
        else:
            # AI unavailable - show fallback greeting with command hints
            app.add_message("AI", random.choice(FALLBACK_GREETINGS), "ai")

    app.mainloop()


if __name__ == "__main__":
    main()
