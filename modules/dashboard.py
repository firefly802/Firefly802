# --- Standard Library Imports ---
import datetime
import threading
import os
import customtkinter as ctk
import requests

# --- Local Imports ---
from . import appointments
from . import todo
from . import config
from . import calendar_manager  # Import calendar_manager
from . import notes_manager  # Import notes_manager
from . import database  # Import database for analytics
from . import email_client  # Import email_client
from . import commands  # Import commands
from . import goals  # Import goals


def get_weather_sa(city: str) -> str:
    """
    Fetches weather information for a given city using OpenWeatherMap API.
    Falls back to a simple weather stub if API is not available.
    
    Args:
        city: The city name to fetch weather for
        
    Returns:
        A formatted weather string
    """
    try:
        # Try using OpenWeatherMap API
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        
        if api_key:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                temp = data.get("main", {}).get("temp", "N/A")
                description = data.get("weather", [{}])[0].get("description", "N/A")
                humidity = data.get("main", {}).get("humidity", "N/A")
                return f"Weather in {city}: {description.capitalize()}, {temp}°C, Humidity: {humidity}%"
        
        # Fallback: Return a generic message
        return f"Weather in {city}: Unable to fetch weather data. Please check your internet connection or configure OpenWeatherMap API."
        
    except requests.RequestException as e:
        return f"Weather in {city}: Connection error - {str(e)}"
    except Exception as e:
        return f"Weather in {city}: Error - {str(e)}"


class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app_instance):
        super().__init__(parent, label_text="Dashboard")
        self.app = app_instance

        # Grid Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        # --- Header Section (Greeting & Date) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        self.greeting_label = ctk.CTkLabel(
            self.header_frame, text="Welcome Back!", font=("Segoe UI", 24, "bold")
        )
        self.greeting_label.pack(anchor="w")

        self.date_label = ctk.CTkLabel(
            self.header_frame, text="", font=("Segoe UI", 16)
        )
        self.date_label.pack(anchor="w")

        # --- Weather Section ---
        self.weather_frame = ctk.CTkFrame(self)
        self.weather_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=10)

        ctk.CTkLabel(
            self.weather_frame, text="🌍 Weather", font=("Segoe UI", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")
        self.weather_label = ctk.CTkLabel(
            self.weather_frame, text="Loading...", justify="left", font=("Consolas", 12)
        )
        self.weather_label.pack(pady=10, padx=10, anchor="w")

        # --- Quick Actions ---
        self.actions_frame = ctk.CTkFrame(self)
        self.actions_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=10)

        ctk.CTkLabel(
            self.actions_frame, text="⚡ Quick Actions", font=("Segoe UI", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")

        btn_grid = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        btn_grid.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Configure grid for buttons (3 columns for more options)
        for i in range(3):
            btn_grid.columnconfigure(i, weight=1)
        
        # Row 1: Core Productivity
        ctk.CTkButton(
            btn_grid, text="New Task", command=lambda: self.app.tabview.set("To-Do")
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid,
            text="View Calendar",
            command=lambda: calendar_manager.trigger_calendar_view(self.app),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid, text="Set Reminder", command=lambda: self.app.tabview.set("Reminders")
        ).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Row 2: Communication & Info
        ctk.CTkButton(
            btn_grid,
            text="My Notes",
            command=lambda: notes_manager.trigger_notes_manager(self.app),
        ).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid,
            text="Check Email",
            command=lambda: email_client.open_email_reader(self.app),
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid, text="Read News", command=lambda: commands.trigger_news(self.app)
        ).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        
        # Row 3: Tools & Analytics
        ctk.CTkButton(
            btn_grid, text="Google Search", command=lambda: commands.trigger_google_search(self.app)
        ).grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid, text="Tools", command=lambda: self.app.tabview.set("Tools")
        ).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid, text="Analytics", command=lambda: self.app.tabview.set("Analytics")
        ).grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        
        # Row 4: Goals & Wellness
        ctk.CTkButton(
            btn_grid, text="My Goals", command=lambda: self.app.tabview.set("Goals")
        ).grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid, text="Zen Mode", command=lambda: self.app.tabview.set("Zen")
        ).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(
            btn_grid, text="Settings", command=lambda: self.app.tabview.set("Settings")
        ).grid(row=3, column=2, padx=5, pady=5, sticky="ew")

        # --- Today's Schedule ---
        self.schedule_frame = ctk.CTkFrame(self)
        self.schedule_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)

        ctk.CTkLabel(
            self.schedule_frame,
            text="📅 Today's Schedule",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=10, padx=10, anchor="w")
        self.schedule_container = ctk.CTkFrame(
            self.schedule_frame, fg_color="transparent"
        )
        self.schedule_container.pack(fill="x", padx=10, pady=5)
        self.schedule_status = ctk.CTkLabel(
            self.schedule_container, text="No appointments today.", text_color="gray"
        )
        self.schedule_status.pack(anchor="w")

        # --- Top Priorities (To-Do) ---
        self.todo_frame = ctk.CTkFrame(self)
        self.todo_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        ctk.CTkLabel(
            self.todo_frame, text="📝 Top Priorities", font=("Segoe UI", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")
        self.todo_container = ctk.CTkFrame(self.todo_frame, fg_color="transparent")
        self.todo_container.pack(fill="x", padx=10, pady=5)
        self.todo_status = ctk.CTkLabel(
            self.todo_container, text="No pending tasks.", text_color="gray"
        )
        self.todo_status.pack(anchor="w")

        # --- Productivity Insights ---
        self.productivity_frame = ctk.CTkFrame(self)
        self.productivity_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)

        ctk.CTkLabel(
            self.productivity_frame, text="📊 Productivity Insights", font=("Segoe UI", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")
        self.productivity_container = ctk.CTkFrame(self.productivity_frame, fg_color="transparent")
        self.productivity_container.pack(fill="x", padx=10, pady=5)
        self.productivity_status = ctk.CTkLabel(
            self.productivity_container, text="Loading insights...", text_color="gray"
        )
        self.productivity_status.pack(anchor="w")

        # --- AI Suggestions ---
        self.ai_suggestions_frame = ctk.CTkFrame(self)
        self.ai_suggestions_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        ctk.CTkLabel(
            self.ai_suggestions_frame, text="🤖 AI Suggestions", font=("Segoe UI", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")
        self.ai_suggestions_container = ctk.CTkFrame(self.ai_suggestions_frame, fg_color="transparent")
        self.ai_suggestions_container.pack(fill="x", padx=10, pady=5)
        self.ai_suggestions_status = ctk.CTkLabel(
            self.ai_suggestions_container, text="Generating suggestions...", text_color="gray"
        )
        self.ai_suggestions_status.pack(anchor="w")

    def refresh_data(self):
        # Update Greeting & Date
        now = datetime.datetime.now()
        hour = now.hour
        if 0 <= hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 18:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"

        self.greeting_label.configure(text=f"{greeting}, User!")
        self.date_label.configure(text=now.strftime("%A, %B %d, %Y"))

        # Start background threads for data fetching
        threading.Thread(target=self._fetch_weather, daemon=True).start()
        self._load_schedule()
        self._load_todos()
        self._load_productivity_insights()
        threading.Thread(target=self._load_ai_suggestions, daemon=True).start()

    def _fetch_weather(self):
        try:
            weather_info = get_weather_sa("johannesburg")
            clean_weather = weather_info.replace("Weather in Johannesburg:", "").strip()
            self.after(0, lambda: self.weather_label.configure(text=clean_weather))
        except Exception as e:
            self.after(
                0, lambda: self.weather_label.configure(text="Weather unavailable.")
            )

    def _load_schedule(self):
        # Clear existing widgets
        for widget in self.schedule_container.winfo_children():
            widget.destroy()

        today_str = datetime.date.today().isoformat()
        appts = appointments.get_appointments_for_date(today_str)

        if not appts:
            ctk.CTkLabel(
                self.schedule_container,
                text="No appointments scheduled for today.",
                text_color="gray",
            ).pack(anchor="w", pady=5)
        else:
            for appt in appts:
                row = ctk.CTkFrame(
                    self.schedule_container, fg_color="#2b2b2b", corner_radius=6
                )
                row.pack(fill="x", pady=2)

                time_lbl = ctk.CTkLabel(
                    row,
                    text=appt["time"],
                    font=("Consolas", 14, "bold"),
                    width=60,
                    text_color=config.ACCENT_COLOR,
                )
                time_lbl.pack(side="left", padx=10, pady=5)

                desc_lbl = ctk.CTkLabel(
                    row, text=appt["description"], font=("Segoe UI", 12)
                )
                desc_lbl.pack(side="left", padx=10, pady=5)

    def _load_todos(self):
        # Clear existing widgets
        for widget in self.todo_container.winfo_children():
            widget.destroy()

        todos = todo.load_todos()
        # Filter for incomplete tasks and take top 5
        pending_todos = [t for t in todos if not t["completed"]][:5]

        if not pending_todos:
            ctk.CTkLabel(
                self.todo_container,
                text="All caught up! No pending tasks.",
                text_color="gray",
            ).pack(anchor="w", pady=5)
        else:
            for i, task in enumerate(pending_todos):
                row = ctk.CTkFrame(self.todo_container, fg_color="transparent")
                row.pack(fill="x", pady=2)

                # Use a checkbox for interactivity
                # We need to find the index in the full list to toggle correctly
                # Since load_todos returns all, we can find the index by ID or just iterate
                # Ideally, toggle_task should take an ID, but the current implementation takes an index.
                # Let's fix todo.py to toggle by ID for robustness, but for now, we'll use a workaround.

                # Workaround: We need the index in the FULL list for the current todo.py implementation
                full_index = next(
                    (idx for idx, t in enumerate(todos) if t["id"] == task["id"]), -1
                )

                if full_index != -1:
                    chk = ctk.CTkCheckBox(
                        row,
                        text=task["text"],
                        font=("Segoe UI", 12),
                        command=lambda idx=full_index: self._complete_task(idx),
                    )
                    chk.pack(side="left", anchor="w")

    def _complete_task(self, index):
        # Toggle the task
        todo.toggle_task(index)
        # Refresh the dashboard to remove the completed task
        self._load_todos()
        # Also refresh the main app's todo tab if it's open/visible (optional but good practice)
        if hasattr(self.app, "refresh_todo_list"):
            self.app.refresh_todo_list()

    def _load_productivity_insights(self):
        """Load and display productivity metrics."""
        try:
            # Get data from database
            all_todos = database.load_todos()
            pending_todos = [t for t in all_todos if not t.get("completed", False)]
            completed_total = len([t for t in all_todos if t.get("completed", False)])
            
            # Goals
            all_goals = goals.load_goals()
            active_goals = len([g for g in all_goals if not g.get("completed", False)])
            
            # Reminders
            all_reminders = database.load_reminders()
            active_reminders = len([r for r in all_reminders if not r.get("completed", False)])
            
            insights_text = f"✅ Total tasks completed: {completed_total}\n📋 Pending tasks: {len(pending_todos)}\n🎯 Active goals: {active_goals}\n🔔 Active reminders: {active_reminders}"
            
            self.productivity_status.configure(text=insights_text)
        except Exception as e:
            self.productivity_status.configure(text=f"Insights unavailable: {str(e)}")

    def _load_ai_suggestions(self):
        """Generate AI-powered productivity suggestions."""
        try:
            # Gather context from user's data
            all_todos = database.load_todos()
            pending_todos = [t for t in all_todos if not t.get("completed", False)]
            completed_today = len([t for t in all_todos if t.get("completed", False) and t.get("date_completed") == datetime.date.today().isoformat()])
            
            all_goals = goals.load_goals()
            active_goals = [g for g in all_goals if not g.get("completed", False)]
            
            all_reminders = database.load_reminders()
            active_reminders = [r for r in all_reminders if not r.get("completed", False)]
            
            # Build prompt for AI
            prompt = f"Based on the user's current productivity data:\n"
            prompt += f"- Pending tasks: {len(pending_todos)}\n"
            prompt += f"- Tasks completed today: {completed_today}\n"
            prompt += f"- Active goals: {len(active_goals)}\n"
            prompt += f"- Active reminders: {len(active_reminders)}\n"
            prompt += "Provide 2-3 concise, actionable suggestions to improve productivity for a work-from-home professional. Keep each suggestion under 50 words."
            
            # Generate suggestion using AI
            if hasattr(self.app, 'generate_ai_response'):
                suggestion = self.app.generate_ai_response(prompt)
            else:
                suggestion = "AI suggestions unavailable."
            
            self.ai_suggestions_status.configure(text=suggestion)
        except Exception as e:
            self.ai_suggestions_status.configure(text=f"Suggestions unavailable: {str(e)}")
