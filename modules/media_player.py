import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import threading

# Try to import VLC, but handle if it's missing
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False

class VideoPlayerFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.instance = None
        self.player = None
        
        self.create_widgets()

    def create_widgets(self):
        # Control Bar
        controls = ctk.CTkFrame(self)
        controls.pack(side="bottom", fill="x", padx=10, pady=10)

        ctk.CTkButton(controls, text="Open Video", command=self.open_file).pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(controls, text="Play", command=self.toggle_play, state="disabled")
        self.play_btn.pack(side="left", padx=5)
        ctk.CTkButton(controls, text="Stop", command=self.stop).pack(side="left", padx=5)
        
        # Video Area
        self.video_canvas = tk.Canvas(self, bg="black")
        self.video_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        if not VLC_AVAILABLE:
            ctk.CTkLabel(self, text="VLC Python module not found.\nPlease install python-vlc to use the video player.", 
                         text_color="red").place(relx=0.5, rely=0.5, anchor="center")

    def open_file(self):
        if not VLC_AVAILABLE:
            return
            
        file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv"), ("All Files", "*.*")])
        if file_path:
            if not self.instance:
                self.instance = vlc.Instance()
                self.player = self.instance.media_player_new()
                
                # Set window handle
                if os.name == "nt":
                    self.player.set_hwnd(self.video_canvas.winfo_id())
                else:
                    self.player.set_xwindow(self.video_canvas.winfo_id())

            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            self.play_btn.configure(state="normal", text="Play")
            self.play()

    def toggle_play(self):
        if self.player:
            if self.player.is_playing():
                self.player.pause()
                self.play_btn.configure(text="Play")
            else:
                self.player.play()
                self.play_btn.configure(text="Pause")

    def play(self):
        if self.player:
            self.player.play()
            self.play_btn.configure(text="Pause")

    def stop(self):
        if self.player:
            self.player.stop()
            self.play_btn.configure(text="Play")


class MusicPlayerFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.instance = None
        self.player = None
        
        self.create_widgets()

    def create_widgets(self):
        # Song Info
        self.info_label = ctk.CTkLabel(self, text="No song selected", font=("Segoe UI", 16))
        self.info_label.pack(pady=20)

        # Controls
        controls = ctk.CTkFrame(self)
        controls.pack(pady=20)

        ctk.CTkButton(controls, text="Open Music", command=self.open_file).pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(controls, text="Play", command=self.toggle_play, state="disabled")
        self.play_btn.pack(side="left", padx=5)
        ctk.CTkButton(controls, text="Stop", command=self.stop).pack(side="left", padx=5)

        if not VLC_AVAILABLE:
            ctk.CTkLabel(self, text="VLC Python module not found.\nPlease install python-vlc to use the music player.", 
                         text_color="red").pack(pady=10)

    def open_file(self):
        if not VLC_AVAILABLE:
            return

        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")])
        if file_path:
            if not self.instance:
                self.instance = vlc.Instance()
                self.player = self.instance.media_player_new()

            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            
            self.info_label.configure(text=os.path.basename(file_path))
            self.play_btn.configure(state="normal", text="Pause")
            self.player.play()

    def toggle_play(self):
        if self.player:
            if self.player.is_playing():
                self.player.pause()
                self.play_btn.configure(text="Play")
            else:
                self.player.play()
                self.play_btn.configure(text="Pause")

    def stop(self):
        if self.player:
            self.player.stop()
            self.play_btn.configure(text="Play")
