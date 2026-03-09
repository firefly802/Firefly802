# --- Standard Library Imports ---
import tkinter as tk
import customtkinter as ctk

# --- Local Imports ---
from . import notes

class NotesManager(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Notes Manager")
        self.geometry("900x600")
        
        self.parent = parent
        self.selected_note_id = None

        self.init_ui()
        self.load_notes_list()

    def init_ui(self):
        # Main Layout: List on Left, Editor on Right
        self.grid_columnconfigure(0, weight=1) # List
        self.grid_columnconfigure(1, weight=3) # Editor
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel: Notes List ---
        left_frame = ctk.CTkFrame(self, width=250)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left_frame, text="My Notes", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=10)

        self.notes_listbox = tk.Listbox(left_frame, bg="#2b2b2b", fg="white", border=0, selectbackground="#007acc", font=("Segoe UI", 12))
        self.notes_listbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.notes_listbox.bind("<<ListboxSelect>>", self.on_note_select)

        ctk.CTkButton(left_frame, text="+ New Note", command=self.new_note).grid(row=2, column=0, pady=10, padx=10, sticky="ew")

        # --- Right Panel: Editor ---
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # Title Entry
        self.title_entry = ctk.CTkEntry(right_frame, placeholder_text="Note Title", font=("Segoe UI", 16, "bold"), height=40)
        self.title_entry.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Content Text Area
        self.content_text = ctk.CTkTextbox(right_frame, font=("Consolas", 12), wrap="word")
        self.content_text.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Action Buttons
        btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkButton(btn_frame, text="Save", command=self.save_note, width=100).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Delete", command=self.delete_note, fg_color="#ff5555", hover_color="#cc0000", width=100).pack(side="right", padx=5)

    def load_notes_list(self):
        self.notes_listbox.delete(0, tk.END)
        self.all_notes = notes.load_notes()
        for note in self.all_notes:
            self.notes_listbox.insert(tk.END, note['title'])

    def on_note_select(self, event):
        selection = self.notes_listbox.curselection()
        if selection:
            index = selection[0]
            note = self.all_notes[index]
            self.selected_note_id = note['id']
            
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, note['title'])
            
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0", note['content'])

    def new_note(self):
        self.selected_note_id = None
        self.notes_listbox.selection_clear(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)
        self.title_entry.focus_set()

    def save_note(self):
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()

        if not title:
            return

        if self.selected_note_id:
            notes.update_note(self.selected_note_id, title, content)
        else:
            notes.add_note(title, content)
        
        self.load_notes_list()
        self.new_note() # Clear after save

    def delete_note(self):
        if self.selected_note_id:
            if tk.messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?"):
                notes.delete_note(self.selected_note_id)
                self.load_notes_list()
                self.new_note()

def trigger_notes_manager(app):
    # Close existing instance if it's open
    if hasattr(app, 'notes_manager_instance') and app.notes_manager_instance:
        app.notes_manager_instance.destroy()
        
    manager = NotesManager(app)
    app.notes_manager_instance = manager
    manager.grab_set()
