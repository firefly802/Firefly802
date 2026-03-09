import customtkinter as ctk
import imaplib
import email
from email.header import decode_header
import threading
import os
from . import config

class EmailReader(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Inbox - Firefly AI 📧")
        self.geometry("900x600")
        self.attributes("-topmost", True)
        
        # Configure Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Header ---
        self.header = ctk.CTkFrame(self)
        self.header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.refresh_btn = ctk.CTkButton(self.header, text="🔄 Refresh Inbox", command=self.load_emails)
        self.refresh_btn.pack(side="left", padx=10, pady=10)
        
        self.status_lbl = ctk.CTkLabel(self.header, text="Ready", text_color="gray")
        self.status_lbl.pack(side="left", padx=10)

        # --- Email List Area ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Recent Emails")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Load emails automatically on open
        self.load_emails()

    def load_emails(self):
        """Clears the list and starts the fetch thread."""
        # Clear existing widgets
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        self.status_lbl.configure(text="Connecting to server...", text_color="#4fc1ff")
        self.refresh_btn.configure(state="disabled")
        
        # Run network operations in background
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        try:
            # Check credentials
            if not config.EMAIL_ACCOUNT or not config.EMAIL_PASSWORD:
                self.after(0, lambda: self.status_lbl.configure(text="❌ Missing Credentials in .env", text_color="#ff5555"))
                return

            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
            mail.login(config.EMAIL_ACCOUNT, config.EMAIL_PASSWORD)
            mail.select("inbox")
            
            # Search for all emails
            status, messages = mail.search(None, "ALL")
            if not messages or not messages[0]:
                self.after(0, lambda: self.status_lbl.configure(text="📭 Inbox is empty"))
                return

            email_ids = messages[0].split()
            
            # Get last 15 emails (newest first)
            latest_ids = email_ids[-15:]
            latest_ids.reverse() 
            
            self.after(0, lambda: self.status_lbl.configure(text=f"Fetching {len(latest_ids)} emails..."))

            for eid in latest_ids:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        try:
                            msg = email.message_from_bytes(response_part[1])
                            # Schedule UI update on main thread
                            self.after(0, lambda m=msg: self.add_email_item(m))
                        except Exception as e:
                            print(f"Error parsing email {eid}: {e}")
            
            mail.close()
            mail.logout()
            self.after(0, lambda: self.status_lbl.configure(text=f"✅ Updated: {len(latest_ids)} emails found", text_color="#98c379"))
            
        except imaplib.IMAP4.error as e:
            self.after(0, lambda: self.status_lbl.configure(text="❌ Login Failed. Check Password.", text_color="#ff5555"))
        except Exception as e:
            self.after(0, lambda: self.status_lbl.configure(text=f"❌ Error: {str(e)}", text_color="#ff5555"))
        finally:
            self.after(0, lambda: self.refresh_btn.configure(state="normal"))

    def add_email_item(self, msg):
        """Adds a single email card to the scrollable list."""
        try:
            # Decode Subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8", errors="replace")
            
            # Decode Sender
            sender = msg.get("From", "Unknown")
            
            # Create Card
            card = ctk.CTkFrame(self.scroll_frame, fg_color=config.BUTTON_BG)
            card.pack(fill="x", pady=5, padx=5)
            
            # Layout
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            ctk.CTkLabel(info_frame, text=sender, font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=subject, font=("Segoe UI", 12), anchor="w", text_color="gray").pack(fill="x")
            
            # Read Button
            ctk.CTkButton(card, text="Read", width=60, height=30, 
                         command=lambda: self.read_email(msg, subject)).pack(side="right", padx=10, pady=10)
                         
        except Exception as e:
            print(f"Error adding email item: {e}")

    def read_email(self, msg, subject):
        """Opens a popup to read the email body."""
        body = "Could not extract text."
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(errors="replace")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(errors="replace")
        except Exception as e:
            body = f"Error reading body: {e}"

        # Popup Window
        win = ctk.CTkToplevel(self)
        win.title(f"Reading: {subject[:30]}...")
        win.geometry("700x500")
        win.attributes("-topmost", True)
        
        ctk.CTkLabel(win, text=subject, font=("Segoe UI", 16, "bold"), wraplength=680).pack(pady=10, padx=10)
        
        textbox = ctk.CTkTextbox(win, font=("Consolas", 12))
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("0.0", body)
        textbox.configure(state="disabled") # Read-only
        
        ctk.CTkButton(win, text="Close", command=win.destroy).pack(pady=10)

def open_email_reader(app):
    EmailReader(app)
