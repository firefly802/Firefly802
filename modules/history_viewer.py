import customtkinter as ctk
import json
import os
from tkinter import filedialog, messagebox
from . import config

class HistoryViewer(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Chat History Archive 📜")
        self.geometry("800x600")
        self.attributes("-topmost", True)
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header ---
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.header, text="Conversation History", font=("Segoe UI", 18, "bold")).pack(side="left", padx=10, pady=10)
        
        self.btn_export = ctk.CTkButton(self.header, text="💾 Export to Text", command=self.export_history)
        self.btn_export.pack(side="right", padx=10)
        
        self.btn_clear = ctk.CTkButton(self.header, text="🗑️ Clear History", fg_color="#ff5555", hover_color="#cc0000", command=self.clear_history)
        self.btn_clear.pack(side="right", padx=10)

        # --- Content Area ---
        self.text_area = ctk.CTkTextbox(self, font=("Consolas", 12), wrap="word")
        self.text_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Load Data
        self.load_history()

    def load_history(self):
        """Reads the history JSON and populates the text area."""
        self.text_area.configure(state="normal")
        self.text_area.delete("0.0", "end")
        
        if not os.path.exists(config.CHAT_HISTORY_FILE):
            self.text_area.insert("0.0", "No history found.")
            self.text_area.configure(state="disabled")
            return

        try:
            with open(config.CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if not data:
                self.text_area.insert("0.0", "History is empty.")
            else:
                for role, message in data:
                    # Formatting
                    if role.lower() == "user":
                        self.text_area.insert("end", f"👤 You:\n{message}\n\n")
                    else:
                        self.text_area.insert("end", f"🤖 Firefly:\n{message}\n\n")
                    self.text_area.insert("end", "-" * 40 + "\n\n")
                    
        except Exception as e:
            self.text_area.insert("0.0", f"Error loading history: {e}")
            
        self.text_area.configure(state="disabled")

    def export_history(self):
        """Exports the current history to a user-selected file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="firefly_chat_history.txt"
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    # Get text from the text widget directly so it matches what the user sees
                    content = self.text_area.get("0.0", "end")
                    f.write(content)
                messagebox.showinfo("Export Successful", f"Saved to {filename}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    def clear_history(self):
        """Clears the history file and the display."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all chat history? This cannot be undone."):
            try:
                # Overwrite with empty list
                with open(config.CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump([], f)
                self.load_history() # Refresh UI
                messagebox.showinfo("Success", "History cleared.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear history: {e}")

def open_history_viewer(app):
    HistoryViewer(app)
