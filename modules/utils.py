# --- Standard Library Imports ---
import os
import re
import asyncio
import threading
import time
import winsound  # Added for UI sound effects

# --- Third-Party Imports ---
import tkinter as tk
import requests
import pyttsx3
import speech_recognition as sr
import edge_tts
import vlc
import cv2  # Added for camera check

# --- Local Imports ---
from . import config

# --- Global Variables ---
tts_engine = None
is_listening = False


# --- ToolTip Class ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            font=("tahoma", "8", "normal"),
        )
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


# --- UI Sound Effects ---
def play_ui_sound(sound_alias):
    """Plays a system sound using winsound."""
    try:
        winsound.PlaySound(sound_alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception as e:
        print(f"Error playing sound {sound_alias}: {e}")


# --- Camera Helper ---
def get_working_camera():
    """
    Attempts to find a working camera index.
    Prioritizes index 1 (external), then 0 (internal).
    Returns the index or None if no camera is found.
    """
    for index in [1, 0]:
        try:
            cap = cv2.VideoCapture(
                index, cv2.CAP_DSHOW
            )  # Use DirectShow on Windows for better compatibility
            if not cap.isOpened():
                cap = cv2.VideoCapture(index)  # Fallback to default backend

            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                if ret:
                    return index
        except Exception:
            continue
    return None


# --- Core Communication Functions ---
def respond(app, text, display_text=None, speak=True, tag="ai"):
    """Unified response handler: updates GUI and speaks text."""
    msg = display_text if display_text else text
    if app:
        app.after(0, app.add_message, "System", msg, tag)

    if speak:
        # This function is now safe to call from any thread.
        speak_text(app, text)


def initialize_tts():
    """Initializes the pyttsx3 engine."""
    global tts_engine
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        if len(voices) > 1:
            engine.setProperty("voice", voices[1].id)  # Default to female
        engine.setProperty("rate", 175)
        tts_engine = engine
        print("TTS engine initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize TTS engine: {e}")
        tts_engine = None


def _perform_speech(text, use_natural, voice_id):
    """The actual blocking speech synthesis. This should always run in a background thread."""
    clean_text = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27ff]", "", text).strip()
    if not clean_text:
        return

    if use_natural:
        try:

            async def _gen_audio():
                output_file = os.path.join(config.BASE_DIR, "temp_tts.mp3")
                communicate = edge_tts.Communicate(clean_text, voice_id)
                await communicate.save(output_file)
                return output_file

            mp3_file = asyncio.run(_gen_audio())

            p = vlc.MediaPlayer(mp3_file)
            p.play()
            time.sleep(0.3)
            while p.is_playing():
                time.sleep(0.1)
            p.release()
            try:
                os.remove(mp3_file)
            except OSError:
                pass
            return
        except Exception as e:
            print(f"Natural Voice Error (Falling back to offline): {e}")

    # Fallback to offline engine
    if not tts_engine:
        print("TTS engine not available")
        return
    try:
        tts_engine.say(clean_text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")


def speak_text(app, text):
    """
    Reads settings from the GUI and starts the speech synthesis in a background thread
    to avoid blocking the main loop. This function is safe to call from any thread.
    """

    def start_speech_thread():
        # This inner function runs on the main thread via app.after
        use_natural = app.use_natural_voice.get()
        voice_key = app.selected_voice.get()
        voice_id = config.VOICE_OPTIONS.get(voice_key, "en-ZA-LeahNeural")

        # Start the actual blocking speech in a new thread
        thread = threading.Thread(
            target=_perform_speech, args=(text, use_natural, voice_id), daemon=True
        )
        thread.start()

    if app:
        # Schedule the GUI-accessing part to run on the main thread
        app.after(0, start_speech_thread)


def listen_for_voice(app, send_message_func):
    """Listens to microphone and converts speech to text."""
    global is_listening
    if is_listening:
        return
    is_listening = True

    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            app.after(0, app.add_message, "System", "Listening... 🎤", "ai")
            try:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                text = r.recognize_sphinx(audio)

                def process_voice():
                    try:
                        app.entry.delete(0, tk.END)
                        app.entry.insert(0, text)
                        send_message_func(voice_mode=True)
                    except Exception as e:
                        app.after(
                            0,
                            app.add_message,
                            "System",
                            f"Error processing voice: {str(e)}",
                            "error",
                        )

                app.after(0, process_voice)
            except sr.WaitTimeoutError:
                app.after(
                    0,
                    app.add_message,
                    "System",
                    "No speech detected. Please try again.",
                    "error",
                )
            except sr.UnknownValueError:
                app.after(
                    0,
                    app.add_message,
                    "System",
                    "Could not understand audio. Please try again.",
                    "error",
                )
            except sr.RequestError as e:
                app.after(
                    0,
                    app.add_message,
                    "System",
                    f"Voice recognition service error: {str(e)}",
                    "error",
                )
            except Exception as e:
                app.after(
                    0, app.add_message, "System", f"Voice Error: {str(e)}", "error"
                )
    except Exception as e:
        app.after(0, app.add_message, "System", f"Microphone error: {str(e)}", "error")
    finally:
        is_listening = False


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
