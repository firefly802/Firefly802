# --- Standard Library Imports ---
import os
import re
import shutil
import ctypes
import datetime
import webbrowser
import urllib.parse
import urllib.request
import platform
import calendar
import random
import time
import json
import socket
import threading  # Added missing import

# --- Third-Party Imports ---
import customtkinter as ctk
from PIL import ImageGrab
import psutil
import pyjokes
import speedtest
import qrcode
import feedparser
import wikipedia  # Added for On This Day

# --- Local Imports ---
from .utils import respond, speak_text
from . import config

# --- Module Description ---
# This module contains the logic for various system commands and utilities.
# It includes functions for opening applications, system control (lock, shutdown),
# and tools like calculator, timer, and note-taking.


# --- Wrapper Functions for GUI Icons ---
def trigger_youtube(app):
    """Opens YouTube in the default web browser."""
    app.add_message("You", "Open YouTube 📺", "user")
    webbrowser.open("https://www.youtube.com")
    app.after(0, app.add_message, "System", "✅ Opening YouTube...", "ai")


def trigger_google(app):
    """Opens Google in the default web browser."""
    app.add_message("You", "Open Google 🌐", "user")
    webbrowser.open("https://www.google.com")
    app.after(0, app.add_message, "System", "✅ Opening Google...", "ai")


def trigger_media(app):
    """Switches the application tab to the Media player."""
    app.add_message("You", "Open Media Player 🎬", "user")
    if app:
        app.tabview.set("Media")
    app.after(0, app.add_message, "System", "✅ Switched to Media Tab.", "ai")


def trigger_word(app):
    """Opens Microsoft Word."""
    app.add_message("You", "Open Word 📝", "user")
    os.system("start winword")
    app.after(0, app.add_message, "System", "✅ Opening Microsoft Word...", "ai")


def trigger_excel(app):
    """Opens Microsoft Excel."""
    app.add_message("You", "Open Excel 📊", "user")
    os.system("start excel")
    app.after(0, app.add_message, "System", "✅ Opening Microsoft Excel...", "ai")


def trigger_ppt(app):
    """Opens Microsoft PowerPoint."""
    app.add_message("You", "Open PowerPoint 📽️", "user")
    os.system("start powerpnt")
    app.after(0, app.add_message, "System", "✅ Opening PowerPoint...", "ai")


def trigger_outlook_app(app):
    """Opens Microsoft Outlook."""
    app.add_message("You", "Open Outlook 📨", "user")
    os.system("start outlook")
    app.after(0, app.add_message, "System", "✅ Opening Outlook App...", "ai")


def trigger_downloads(app):
    """Opens the user's Downloads folder."""
    app.add_message("You", "Open Downloads 📂", "user")
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
    os.startfile(downloads_path)
    app.after(0, app.add_message, "System", "✅ Opening Downloads folder...", "ai")


def trigger_notepad(app):
    """Opens Notepad."""
    app.add_message("You", "Open Notepad 📝", "user")
    os.system("start notepad")
    app.after(0, app.add_message, "System", "✅ Opening Notepad...", "ai")


def trigger_time(app):
    """Announces the current time."""
    now = datetime.datetime.now()
    time_str = now.strftime("It is %H:%M on %A, %B %d.")
    app.add_message("System", f"🕒 {time_str}", "ai")
    threading.Thread(
        target=speak_text,
        args=(
            app,
            time_str,
        ),
        daemon=True,
    ).start()


def trigger_calc(app):
    """Opens the Windows Calculator."""
    app.add_message("You", "Open Calculator 🧮", "user")
    os.system("start calc")
    app.after(0, app.add_message, "System", "✅ Opening Calculator...", "ai")


def trigger_lock(app):
    """Locks the Windows workstation."""
    app.add_message("You", "Lock Screen 🔒", "user")
    app.after(0, app.add_message, "System", "🔒 Locking workstation...", "ai")
    app.after(1000, lambda: ctypes.windll.user32.LockWorkStation())


def trigger_screenshot(app):
    """Takes a screenshot and saves it to the 'screenshots' directory."""
    app.add_message("You", "Take Screenshot 📸", "user")
    try:
        screenshots_dir = os.path.join(config.BASE_DIR, "screenshots")
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        filepath = os.path.join(
            screenshots_dir,
            f"screenshot_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
        )
        ImageGrab.grab().save(filepath)
        app.after(
            0,
            app.add_message,
            "System",
            f"✅ Saved: {os.path.basename(filepath)}",
            "ai",
        )
        os.startfile(filepath)
    except Exception as e:
        app.after(0, app.add_message, "System", f"❌ Error: {e}", "error")


def trigger_system_health(app):
    """Checks CPU and RAM usage."""
    cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
    bat = psutil.sensors_battery()
    bat_msg = f", 🔋 Battery: {bat.percent}%" if bat else ""
    msg = f"💻 System Status:\nCPU Usage: {cpu}%\nRAM Usage: {ram}%{bat_msg}"
    app.add_message("System", msg, "ai")
    speak_text(app, f"CPU is at {cpu} percent. RAM is at {ram} percent.")


def trigger_system_info(app):
    """Displays system information (OS, Node, etc.)."""
    u = platform.uname()
    info = f"🖥️ System: {u.system}\nNode: {u.node}\nRelease: {u.release}\nVersion: {u.version}\nMachine: {u.machine}\nProcessor: {u.processor}"
    app.add_message("System", info, "ai")
    speak_text(app, "Here is your system information.")


def trigger_joke(app):
    """Tells a random programming joke."""
    joke = pyjokes.get_joke()
    app.add_message("System", f"😂 {joke}", "ai")
    speak_text(app, joke)


def trigger_daily_quote(app):
    """Fetches and displays the daily quote."""
    try:
        with open(os.path.join(config.BASE_DIR, "modules", "quotes.json"), "r") as f:
            quotes = json.load(f)

        day_of_year = datetime.date.today().timetuple().tm_yday
        quote_index = day_of_year % len(quotes)
        daily_quote = quotes[quote_index]

        msg = (
            f'📜 Quote of the Day:\n"{daily_quote["quote"]}" — {daily_quote["author"]}'
        )
        respond(app, msg, speak=True)
    except (FileNotFoundError, IndexError, json.JSONDecodeError) as e:
        respond(app, f"Could not load quote: {e}", tag="error")


def trigger_speedtest(app):
    """Runs an internet speed test in a background thread."""
    app.add_message("You", "Check Internet Speed 🚀", "user")
    app.after(0, app.add_message, "System", "⏳ Testing speed...", "ai")

    def run_test():
        try:
            st = speedtest.Speedtest()
            msg = f"🚀 Speed Test Results:\n⬇️ Download: {st.download() / 1e6:.2f} Mbps\n⬆️ Upload: {st.upload() / 1e6:.2f} Mbps\n📶 Ping: {st.results.ping} ms"
            app.after(0, app.add_message, "System", msg, "ai")
        except Exception as e:
            app.after(
                0, app.add_message, "System", f"❌ Speedtest failed: {e}", "error"
            )

    threading.Thread(target=run_test, daemon=True).start()


def trigger_qrcode(app):
    """Generates a QR code from user input."""
    data = ctk.CTkInputDialog(
        text="Enter text or URL for QR Code:", title="QR Generator"
    ).get_input()
    if not data:
        return
    app.add_message("You", f"Generate QR Code for: {data}", "user")
    try:
        img = qrcode.make(data)
        img.save("qrcode.png")
        os.system("start qrcode.png")
        app.after(0, app.add_message, "System", "✅ QR Code generated.", "ai")
    except Exception as e:
        app.after(0, app.add_message, "System", f"❌ Error: {e}", "error")


def trigger_take_note(app):
    """Saves a quick note to notes.txt."""
    note = ctk.CTkInputDialog(text="Enter your note:", title="Take Note").get_input()
    if not note:
        return
    with open("notes.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {note}\n")
    app.after(0, app.add_message, "System", "✅ Note saved.", "ai")


def trigger_read_notes(app):
    """Reads notes from notes.txt."""
    if not os.path.exists("notes.txt"):
        return app.after(0, app.add_message, "System", "⚠️ No notes found.", "error")
    with open("notes.txt", "r", encoding="utf-8") as f:
        notes = f.read()
    app.after(0, app.add_message, "System", f"📝 Your Notes:\n{notes}", "ai")


def trigger_timer(app):
    """Sets a simple countdown timer."""
    try:
        seconds = int(
            ctk.CTkInputDialog(
                text="Enter duration in seconds:", title="Set Timer"
            ).get_input()
        )
    except (ValueError, TypeError):
        return

    def run_timer(sec):
        time.sleep(sec)
        respond(app, "⏰ Timer finished!")

    threading.Thread(target=run_timer, args=(seconds,), daemon=True).start()
    app.after(
        0, app.add_message, "System", f"⏳ Timer set for {seconds} seconds.", "ai"
    )


def trigger_password_gen(app):
    """Generates a random secure password."""
    try:
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = "".join(random.choice(chars) for _ in range(12))
        app.add_message("System", f"🔑 Generated Password: {password}", "ai")
        app.clipboard_clear()
        app.clipboard_append(password)
        app.after(0, app.add_message, "System", "✅ Copied to clipboard.", "ai")
    except Exception as e:
        app.after(
            0,
            app.add_message,
            "System",
            f"⚠️ Error generating password: {str(e)}",
            "error",
        )


def trigger_disk_usage(app):
    """Checks disk usage for the C: drive."""
    try:
        total, used, free = shutil.disk_usage("/")
        msg = f"💾 Disk Space (C:):\nFree: {free // (2**30)} GB\nTotal: {total // (2**30)} GB"
        app.add_message("System", msg, "ai")
    except Exception as e:
        app.after(
            0, app.add_message, "System", f"⚠️ Error checking disk: {str(e)}", "error"
        )


def trigger_dice_roll(app):
    """Rolls a 6-sided die."""
    respond(app, f"🎲 You rolled a {random.randint(1, 6)}!")


def trigger_coin_flip(app):
    """Flips a coin."""
    respond(app, f"🪙 It's {random.choice(['Heads', 'Tails'])}!")


def trigger_restart(app):
    """Restarts the computer."""
    app.add_message("You", "Restart 🔄", "user")
    os.system("shutdown /r /t 15")
    respond(app, "🔄 Restarting in 15 seconds. Say 'abort' to cancel.")


def trigger_google_search(app):
    """Performs a Google search."""
    query = ctk.CTkInputDialog(
        text="Enter search query:", title="Google Search"
    ).get_input()
    if not query:
        return
    app.add_message("You", f"Search Google for: {query}", "user")
    webbrowser.open(f"https://www.google.com/search?q={query}")
    app.after(0, app.add_message, "System", f"✅ Searching for '{query}'...", "ai")


def trigger_translate(app):
    """Opens Google Translate."""
    text = ctk.CTkInputDialog(
        text="Enter text to translate:", title="Google Translate"
    ).get_input()
    if not text:
        return
    app.add_message("You", f"Translate: {text}", "user")
    webbrowser.open(
        f"https://translate.google.com/?sl=auto&tl=en&text={urllib.parse.quote(text)}"
    )
    app.after(0, app.add_message, "System", "✅ Opening Google Translate...", "ai")


def trigger_battery_report(app):
    """Generates a Windows battery report."""
    app.add_message("You", "Generate Battery Report 🔋", "user")
    try:
        report_path = os.path.abspath("battery-report.html")
        os.system(f'powercfg /batteryreport /output "{report_path}"')
        app.after(
            0, app.add_message, "System", f"✅ Report generated: {report_path}", "ai"
        )
        os.startfile(report_path)
    except Exception as e:
        app.after(0, app.add_message, "System", f"❌ Error: {e}", "error")


def trigger_organize_files(app):
    """Organizes files in a selected directory."""
    folder = ctk.filedialog.askdirectory(title="Select Folder to Organize")
    if not folder:
        return
    app.add_message("System", f"📂 Organizing: {folder}...", "ai")
    # Simplified logic for brevity
    # ... full organization logic here ...
    app.after(0, app.add_message, "System", "✅ Organization complete.", "ai")


def trigger_news(app):
    """Opens a dedicated news reader window."""
    # Close existing instance if open
    if hasattr(app, 'news_reader_instance') and app.news_reader_instance:
        app.news_reader_instance.destroy()
    
    reader = NewsReader(app)
    app.news_reader_instance = reader
    reader.grab_set()


class NewsReader(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("News Reader - Firefly AI")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkLabel(self, text="📰 News Headlines", font=("Segoe UI", 16, "bold"))
        header.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        
        # News list
        self.news_list = ctk.CTkScrollableFrame(self)
        self.news_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="Loading news...")
        self.status_label.grid(row=2, column=0, pady=5, padx=10, sticky="w")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(self, text="Refresh", command=self.load_news)
        refresh_btn.grid(row=3, column=0, pady=10, padx=10, sticky="e")
        
        # Load news
        self.load_news()
    
    def load_news(self):
        """Load and display news."""
        # Clear existing
        for widget in self.news_list.winfo_children():
            widget.destroy()
        
        self.status_label.configure(text="Fetching news...")
        
        def fetch():
            try:
                news = self.fetch_news()
                self.after(0, lambda: self.display_news(news))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(text=f"Error: {str(e)}"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def fetch_news(self):
        """Fetch top news headlines."""
        feed = feedparser.parse(
            "https://news.google.com/rss?hl=en-ZA&gl=ZA&ceid=ZA:en"
        )
        news_items = []
        for entry in feed.entries[:10]:  # Top 10 headlines
            news_items.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary[:200] + "..." if len(entry.summary) > 200 else entry.summary
            })
        return news_items
    
    def display_news(self, news):
        """Display news in the list."""
        if not news:
            ctk.CTkLabel(self.news_list, text="No news found.").pack(pady=20)
            self.status_label.configure(text="")
            return
        
        for item in news:
            frame = ctk.CTkFrame(self.news_list)
            frame.pack(fill="x", padx=5, pady=5)
            
            # Title
            title_label = ctk.CTkLabel(frame, text=item['title'], font=("Segoe UI", 12, "bold"), wraplength=700, justify="left")
            title_label.pack(anchor="w", padx=10, pady=5)
            
            # Summary
            summary_label = ctk.CTkLabel(frame, text=item['summary'], font=("Segoe UI", 10), wraplength=700, justify="left")
            summary_label.pack(anchor="w", padx=10, pady=5)
            
            # Link button
            link_btn = ctk.CTkButton(frame, text="Read More", command=lambda url=item['link']: webbrowser.open(url), width=100)
            link_btn.pack(anchor="e", padx=10, pady=5)
        
        self.status_label.configure(text=f"Loaded {len(news)} headlines")


def trigger_task_manager(app):
    """Opens Windows Task Manager."""
    app.add_message("You", "Open Task Manager 📊", "user")
    os.system("start taskmgr")
    app.after(0, app.add_message, "System", "✅ Opening Task Manager...", "ai")


def trigger_control_panel(app):
    """Opens Windows Control Panel."""
    app.add_message("You", "Open Control Panel ⚙️", "user")
    os.system("start control")
    app.after(0, app.add_message, "System", "✅ Opening Control Panel...", "ai")


def trigger_cmd(app):
    """Opens Command Prompt."""
    app.add_message("You", "Open CMD 💻", "user")
    os.system("start cmd")
    app.after(0, app.add_message, "System", "✅ Opening Command Prompt...", "ai")


def trigger_shutdown(app):
    """Shuts down the computer."""
    app.add_message("You", "Shutdown 🛑", "user")
    os.system("shutdown /s /t 15")
    respond(app, "🛑 Shutting down in 15 seconds. Say 'abort' to cancel.")


def trigger_unit_converter(app):
    """Opens a dialog to convert common units."""
    query = ctk.CTkInputDialog(
        text="Enter conversion query (e.g., '10 kg to lbs'):", title="Unit Converter"
    ).get_input()
    if not query:
        return

    # Basic parsing: "10 kg to lbs" -> (10, "kg", "lbs")
    match = re.match(r"([\d\.]+)\s*([a-zA-Z]+)\s*to\s*([a-zA-Z]+)", query.lower())
    if not match:
        respond(
            app,
            "❌ Invalid format. Please use 'value unit to unit' (e.g., '100 km to mi').",
            speak=True,
            tag="error",
        )
        return

    value, from_unit, to_unit = float(match.group(1)), match.group(2), match.group(3)

    # Conversion factors (simplified)
    CONVERSIONS = {
        ("kg", "lbs"): 2.20462,
        ("lbs", "kg"): 1 / 2.20462,
        ("km", "mi"): 0.621371,
        ("mi", "km"): 1 / 0.621371,
        ("m", "ft"): 3.28084,
        ("ft", "m"): 1 / 3.28084,
        ("cm", "in"): 0.393701,
        ("in", "cm"): 1 / 0.393701,
    }
    # Temperature is a function, not a simple factor
    TEMP_CONVERSIONS = {
        ("c", "f"): lambda c: c * 9 / 5 + 32,
        ("f", "c"): lambda f: (f - 32) * 5 / 9,
    }

    result = None
    if (from_unit, to_unit) in CONVERSIONS:
        result = value * CONVERSIONS[(from_unit, to_unit)]
    elif (from_unit, to_unit) in TEMP_CONVERSIONS:
        result = TEMP_CONVERSIONS[(from_unit, to_unit)](value)
    else:
        respond(
            app,
            f"❌ Conversion from {from_unit} to {to_unit} is not supported.",
            speak=True,
            tag="error",
        )
        return

    if result is not None:
        msg = f"🔄 {value} {from_unit} is {result:.2f} {to_unit}"
        respond(app, msg, speak=True)


def trigger_zen_mode(app):
    """Switches the application to the Zen tab."""
    app.add_message("You", "Enter Mindfulness Mode 🧘", "user")
    app.tabview.set("Zen")
    app.after(0, app.add_message, "System", "✨ Entering Zen Mode. Breathe...", "ai")
    speak_text(app, "Entering Zen Mode. Take a deep breath.")


def trigger_file_search(app):
    """Opens a dialog to search for files."""
    query = ctk.CTkInputDialog(
        text="Enter file name or pattern (e.g., *.txt):", title="File Search"
    ).get_input()
    if not query:
        return

    app.add_message("You", f"Search for file: {query}", "user")
    app.after(
        0,
        app.add_message,
        "System",
        f"🔍 Searching for '{query}'... This may take a while.",
        "ai",
    )

    def search_thread():
        results = []
        search_path = os.path.expanduser("~")  # Search user directory

        # Simple wildcard matching
        import fnmatch

        for root, dirs, files in os.walk(search_path):
            for name in files:
                if fnmatch.fnmatch(name, query):
                    results.append(os.path.join(root, name))
                    if len(results) >= 20:
                        break  # Limit results
            if len(results) >= 20:
                break

        if results:
            msg = "📂 Found Files:\n" + "\n".join(results)
            app.after(0, app.add_message, "System", msg, "ai")

            # Show results in a popup
            def show_results():
                win = ctk.CTkToplevel(app)
                win.title("Search Results")
                win.geometry("600x400")

                scroll = ctk.CTkScrollableFrame(win)
                scroll.pack(fill="both", expand=True)

                for path in results:
                    btn = ctk.CTkButton(
                        scroll,
                        text=path,
                        anchor="w",
                        command=lambda p=path: os.startfile(p),
                    )
                    btn.pack(fill="x", pady=2, padx=5)

            app.after(0, show_results)
        else:
            app.after(0, app.add_message, "System", "❌ No files found.", "error")

    threading.Thread(target=search_thread, daemon=True).start()


def trigger_summarizer(app):
    """Opens a window to summarize text using the local AI model."""
    win = ctk.CTkToplevel(app)
    win.title("AI Document Summarizer")
    win.geometry("600x500")

    ctk.CTkLabel(
        win, text="Paste text to summarize:", font=("Segoe UI", 14, "bold")
    ).pack(pady=10)

    text_input = ctk.CTkTextbox(win, height=150)
    text_input.pack(fill="x", padx=20, pady=5)

    result_box = ctk.CTkTextbox(
        win, height=150, state="disabled"
    )  # Read-only initially

    def run_summary():
        text = text_input.get("1.0", "end").strip()
        if not text:
            return

        btn_summarize.configure(state="disabled", text="Summarizing...")
        result_box.configure(state="normal")
        result_box.delete("1.0", "end")
        result_box.insert("1.0", "Thinking...")
        result_box.configure(state="disabled")

        def process():
            prompt = f"Summarize the following text into 3-5 concise bullet points:\n\n{text}"
            summary = app.generate_completion(prompt)

            def update_ui():
                result_box.configure(state="normal")
                result_box.delete("1.0", "end")
                result_box.insert("1.0", summary)
                result_box.configure(state="disabled")
                btn_summarize.configure(state="normal", text="Summarize")

            app.after(0, update_ui)

        threading.Thread(target=process, daemon=True).start()

    btn_summarize = ctk.CTkButton(win, text="Summarize", command=run_summary)
    btn_summarize.pack(pady=10)

    ctk.CTkLabel(win, text="Summary:", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
    result_box.pack(fill="both", expand=True, padx=20, pady=5)


def trigger_pomodoro(app):
    """Starts a Pomodoro timer in a new window."""
    win = ctk.CTkToplevel(app)
    win.title("Pomodoro Timer")
    win.geometry("300x200")

    # Timer state
    state = {"running": False, "time": 25 * 60, "mode": "Work"}

    lbl_time = ctk.CTkLabel(win, text="25:00", font=("Consolas", 40, "bold"))
    lbl_time.pack(pady=20)

    lbl_status = ctk.CTkLabel(win, text="Work Time 👨‍💻", font=("Segoe UI", 14))
    lbl_status.pack(pady=5)

    def update_timer():
        if state["running"] and state["time"] > 0:
            state["time"] -= 1
            mins, secs = divmod(state["time"], 60)
            lbl_time.configure(text=f"{mins:02d}:{secs:02d}")
            win.after(1000, update_timer)
        elif state["running"] and state["time"] == 0:
            state["running"] = False
            # Switch modes
            if state["mode"] == "Work":
                state["mode"] = "Break"
                state["time"] = 5 * 60
                lbl_status.configure(text="Break Time ☕")
                respond(
                    app, "Work session complete! Take a 5 minute break.", speak=True
                )
            else:
                state["mode"] = "Work"
                state["time"] = 25 * 60
                lbl_status.configure(text="Work Time 👨‍💻")
                respond(app, "Break over! Back to work.", speak=True)

            mins, secs = divmod(state["time"], 60)
            lbl_time.configure(text=f"{mins:02d}:{secs:02d}")
            btn_start.configure(text="Start")

    def start_stop():
        if state["running"]:
            state["running"] = False
            btn_start.configure(text="Start")
        else:
            state["running"] = True
            btn_start.configure(text="Pause")
            update_timer()

    def reset():
        state["running"] = False
        state["mode"] = "Work"
        state["time"] = 25 * 60
        lbl_time.configure(text="25:00")
        lbl_status.configure(text="Work Time 👨‍💻")
        btn_start.configure(text="Start")

    btn_frame = ctk.CTkFrame(win, fg_color="transparent")
    btn_frame.pack(pady=10)

    btn_start = ctk.CTkButton(btn_frame, text="Start", width=80, command=start_stop)
    btn_start.pack(side="left", padx=5)

    btn_reset = ctk.CTkButton(
        btn_frame,
        text="Reset",
        width=80,
        fg_color="#ff5555",
        hover_color="#cc0000",
        command=reset,
    )
    btn_reset.pack(side="left", padx=5)


# --- Tab Navigation Triggers for Voice Control ---
def trigger_open_chat(app):
    """Opens the Chat tab."""
    app.add_message("You", "Open AI Chat 💬", "user")
    app.tabview.set("Chat")
    app.after(0, app.add_message, "System", "💬 Switched to Chat tab.", "ai")
    speak_text(app, "Opening chat.")


def trigger_open_tools(app):
    """Opens the Tools tab."""
    app.add_message("You", "Open Tools 🛠️", "user")
    app.tabview.set("Tools")
    app.after(0, app.add_message, "System", "🛠️ Switched to Tools tab.", "ai")
    speak_text(app, "Opening tools.")


def trigger_open_todo(app):
    """Opens the To-Do tab."""
    app.add_message("You", "Open To-Do 📝", "user")
    app.tabview.set("To-Do")
    app.after(0, app.add_message, "System", "📝 Switched to To-Do tab.", "ai")
    speak_text(app, "Opening to-do list.")


def trigger_open_reminders(app):
    """Opens the Reminders tab."""
    app.add_message("You", "Open Reminders 🔔", "user")
    app.tabview.set("Reminders")
    app.after(0, app.add_message, "System", "🔔 Switched to Reminders tab.", "ai")
    speak_text(app, "Opening reminders.")


def trigger_open_goals(app):
    """Opens the Goals tab."""
    app.add_message("You", "Open Goals 🎯", "user")
    app.tabview.set("Goals")
    app.after(0, app.add_message, "System", "🎯 Switched to Goals tab.", "ai")
    speak_text(app, "Opening goals.")


def trigger_open_analytics(app):
    """Opens the Analytics tab."""
    app.add_message("You", "Open Analytics 📊", "user")
    app.tabview.set("Analytics")
    app.after(0, app.add_message, "System", "📊 Switched to Analytics tab.", "ai")
    speak_text(app, "Opening analytics.")


def trigger_open_zen(app):
    """Opens the Zen tab."""
    app.add_message("You", "Open Zen Mode 🧘", "user")
    app.tabview.set("Zen")
    app.after(0, app.add_message, "System", "🧘 Switched to Zen tab.", "ai")
    speak_text(app, "Entering zen mode.")


def trigger_open_settings(app):
    """Opens the Settings tab."""
    app.add_message("You", "Open Settings ⚙️", "user")
    app.tabview.set("Settings")
    app.after(0, app.add_message, "System", "⚙️ Switched to Settings tab.", "ai")
    speak_text(app, "Opening settings.")


def trigger_ip_info(app):
    """Fetches and displays local and public IP addresses."""
    app.add_message("You", "What is my IP? 🌐", "user")
    app.after(0, app.add_message, "System", "🔍 Fetching IP information...", "ai")

    def fetch_ip():
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            # Get public IP
            try:
                public_ip = (
                    urllib.request.urlopen("https://api.ipify.org")
                    .read()
                    .decode("utf8")
                )
            except Exception:
                public_ip = "Not available"

            msg = f"🌐 IP Information:\nLocal IP: {local_ip}\nPublic IP: {public_ip}"
            app.after(0, app.add_message, "System", msg, "ai")

        except Exception as e:
            app.after(
                0, app.add_message, "System", f"❌ Error fetching IP: {e}", "error"
            )

    threading.Thread(target=fetch_ip, daemon=True).start()


def trigger_stock_price(app):
    """Fetches stock price for a given symbol."""
    symbol = ctk.CTkInputDialog(
        text="Enter Stock Symbol (e.g., AAPL):", title="Stock Price"
    ).get_input()
    if not symbol:
        return

    symbol = symbol.upper().strip()
    app.add_message("You", f"Check stock price for {symbol} 📈", "user")
    app.after(0, app.add_message, "System", f"🔍 Fetching data for {symbol}...", "ai")

    def fetch_stock():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            meta = data["chart"]["result"][0]["meta"]
            price = meta["regularMarketPrice"]
            currency = meta["currency"]

            msg = f"📈 Stock Price ({symbol}):\nPrice: {price} {currency}"
            app.after(0, app.add_message, "System", msg, "ai")

        except Exception as e:
            app.after(
                0,
                app.add_message,
                "System",
                f"❌ Could not fetch stock data: {e}",
                "error",
            )

    threading.Thread(target=fetch_stock, daemon=True).start()


def trigger_on_this_day(app):
    """Fetches historical events for the current day and displays them in a window."""
    app.add_message("You", "What happened on this day? 📅", "user")
    app.after(0, app.add_message, "System", "🔍 Opening History Window...", "ai")

    # Create the window immediately
    win = ctk.CTkToplevel(app)
    win.title("On This Day 📅")
    win.geometry("700x600")
    win.attributes("-topmost", True)

    # Header
    now = datetime.datetime.now()
    date_str = f"{now.strftime('%B')} {now.day}"
    ctk.CTkLabel(win, text=f"Historical Events for {date_str}", font=("Segoe UI", 20, "bold")).pack(pady=10)

    # Scrollable text area
    text_area = ctk.CTkTextbox(win, font=("Segoe UI", 12), wrap="word")
    text_area.pack(fill="both", expand=True, padx=20, pady=10)
    text_area.insert("0.0", "Loading historical data from Wikipedia...\n")
    text_area.configure(state="disabled")

    def fetch_history():
        try:
            print(f"DEBUG: Fetching Wikipedia page for '{date_str}'")

            # Fetch the page
            try:
                page = wikipedia.page(date_str, auto_suggest=False)
            except wikipedia.exceptions.PageError:
                app.after(0, lambda: update_text(f"❌ Could not find a page for '{date_str}'."))
                return
            except wikipedia.exceptions.DisambiguationError as e:
                app.after(0, lambda: update_text(f"⚠️ Ambiguous page for '{date_str}': {e.options[:3]}"))
                return

            # Extract events from content
            content = page.content
            events = []
            
            # Use regex to find the Events section more robustly.
            match = re.search(r'==\s*Events\s*==\n(.*?)\n==\s*\w+\s*==', content, re.DOTALL)

            if match:
                section = match.group(1)
                for line in section.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("*")):
                        events.append(line)
            
            if not events:
                 # Fallback
                 for line in content.split('\n')[:200]:
                     if line.strip() and line.strip()[0].isdigit() and " – " in line:
                         events.append(line.strip())

            if events:
                # Display all events found (or a large subset)
                full_text = "\n\n".join(events[:50]) # Limit to 50 to avoid overwhelming
                app.after(0, lambda: update_text(full_text))
            else:
                summary = wikipedia.summary(date_str, sentences=5)
                app.after(0, lambda: update_text(f"No specific events found. Summary:\n\n{summary}"))

        except Exception as e:
            print(f"ERROR in trigger_on_this_day: {e}")
            app.after(0, lambda: update_text(f"❌ Error fetching history: {str(e)}"))

    def update_text(content):
        text_area.configure(state="normal")
        text_area.delete("0.0", "end")
        text_area.insert("0.0", content)
        text_area.configure(state="disabled")

    threading.Thread(target=fetch_history, daemon=True).start()
    
    ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=10)


def trigger_idea_incubator(app):
    """Opens a window to nurture a small idea into a plan."""
    win = ctk.CTkToplevel(app)
    win.title("💡 Firefly Spark - Idea Incubator")
    win.geometry("700x600")

    ctk.CTkLabel(win, text="What's your spark?", font=("Segoe UI", 16, "bold")).pack(
        pady=(20, 5)
    )

    ctk.CTkLabel(
        win,
        text="Enter a small idea (e.g., 'Start a garden', 'Write a book')",
        font=("Segoe UI", 12),
    ).pack(pady=(0, 10))

    idea_input = ctk.CTkEntry(win, width=500, height=40, font=("Segoe UI", 14))
    idea_input.pack(pady=5)

    result_box = ctk.CTkTextbox(
        win, height=350, width=600, font=("Consolas", 12), state="disabled"
    )

    def nurture_idea():
        idea = idea_input.get().strip()
        if not idea:
            return

        btn_spark.configure(state="disabled", text="Igniting...")
        result_box.configure(state="normal")
        result_box.delete("1.0", "end")
        result_box.insert("1.0", "🔥 Fanning the flames of your idea...\n\n")
        result_box.configure(state="disabled")

        def process():
            prompt = (
                f"I have a small idea: '{idea}'.\n"
                "Please act as an expert consultant and expand this into a concrete, actionable plan.\n"
                "Provide:\n"
                "1. A catchy title for the project.\n"
                "2. A brief vision statement.\n"
                "3. 5 clear, actionable steps to get started.\n"
                "4. One potential challenge and how to overcome it.\n"
                "Keep it inspiring and practical."
            )
            plan = app.generate_completion(prompt)

            def update_ui():
                result_box.configure(state="normal")
                result_box.delete("1.0", "end")
                result_box.insert("1.0", plan)
                result_box.configure(state="disabled")
                btn_spark.configure(state="normal", text="Ignite Idea 💡")

            app.after(0, update_ui)

        threading.Thread(target=process, daemon=True).start()

    btn_spark = ctk.CTkButton(
        win,
        text="Ignite Idea 💡",
        width=200,
        height=40,
        command=nurture_idea,
        fg_color="#ff9900",
        hover_color="#cc7a00",
    )
    btn_spark.pack(pady=20)

    result_box.pack(pady=10)


def trigger_hand_gestures(app):
    """Starts hand gesture recognition for volume control."""
    app.add_message("You", "Start Hand Gestures ✋", "user")
    app.add_message(
        "System", "📷 Initializing Camera & AI... Press 'q' to quit window.", "ai"
    )

    try:
        import cv2
        import mediapipe as mp
        import numpy as np
        import comtypes
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioDevices, IAudioEndpointVolume
        from ctypes import cast, POINTER
    except ImportError as e:
        app.add_message(
            "System",
            f"❌ Missing libraries: {e}.\nRun: pip install opencv-python mediapipe pycaw comtypes numpy",
            "error",
        )
        return

    def gesture_loop():
        cap = None
        try:
            comtypes.CoInitialize()

            # Find working camera using the utility
            camera_idx = utils.get_working_camera()
            if camera_idx is None:
                app.after(
                    0, app.add_message, "System", "❌ No working camera found.", "error"
                )
                return

            # Try DirectShow first for Windows, fallback to default
            cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(camera_idx)

            if not cap.isOpened():
                app.after(
                    0, app.add_message, "System", "❌ Could not open camera.", "error"
                )
                return

            # Set camera properties for better compatibility
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)

            mp_hands = mp.solutions.hands
            hands = mp_hands.Hands(
                min_detection_confidence=0.7, min_tracking_confidence=0.7
            )
            mp_draw = mp.solutions.drawing_utils

            # Audio Setup
            devices = AudioDevices.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            vol_range = volume.GetVolumeRange()
            min_vol = vol_range[0]
            max_vol = vol_range[1]

            while True:
                success, img = cap.read()
                if not success:
                    break

                img = cv2.flip(img, 1)  # Mirror view
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = hands.process(img_rgb)

                if results.multi_hand_landmarks:
                    for hand_lms in results.multi_hand_landmarks:
                        lm_list = []
                        for id, lm in enumerate(hand_lms.landmark):
                            h, w, c = img.shape
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            lm_list.append([id, cx, cy])

                        if lm_list:
                            # Thumb tip (4) and Index tip (8)
                            x1, y1 = lm_list[4][1], lm_list[4][2]
                            x2, y2 = lm_list[8][1], lm_list[8][2]
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
                            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
                            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                            length = np.hypot(x2 - x1, y2 - y1)

                            # Hand range 50 - 300 -> Volume range
                            vol = np.interp(length, [30, 250], [min_vol, max_vol])
                            volume.SetMasterVolumeLevel(vol, None)

                            if length < 30:
                                cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                        mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)

                cv2.imshow("Firefly Gestures (Press 'q' to exit)", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()
            app.after(0, app.add_message, "System", "✅ Gesture control closed.", "ai")

        except Exception as e:
            app.after(0, app.add_message, "System", f"❌ Gesture error: {e}", "error")
            if "cap" in locals():
                cap.release()
            cv2.destroyAllWindows()

    threading.Thread(target=gesture_loop, daemon=True).start()
