"""
Email client module for Firefly AI.
Provides email reading functionality with a GUI.
"""

import imaplib
import email
import threading
import customtkinter as ctk
import os
from dotenv import load_dotenv
from . import config


def read_latest_email(app):
    """Reads and displays the latest email from the configured email account."""
    app.add_message("You", "Read Email 📧", "user")
    app.add_message("System", "📧 Fetching latest email...", "ai")

    def fetch_email():
        try:
            email_address = config.EMAIL_ACCOUNT
            password = config.EMAIL_PASSWORD
            imap_server = config.IMAP_SERVER

            if not email_address or not password:
                app.after(
                    0,
                    app.add_message,
                    "System",
                    "❌ Email credentials not configured. Check your .env file.",
                    "error",
                )
                return

            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_address, password)
            mail.select("inbox")

            # Search for emails
            _, messages = mail.search(None, "ALL")
            email_ids = messages[0].split()

            if not email_ids:
                app.after(
                    0,
                    app.add_message,
                    "System",
                    "📭 No emails in inbox.",
                    "ai",
                )
                mail.close()
                mail.logout()
                return

            # Get latest email
            latest_id = email_ids[-1]
            _, msg_data = mail.fetch(latest_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            # Extract email details
            from_addr = msg.get("From", "Unknown")
            subject = msg.get("Subject", "No Subject")
            body = ""

            # Extract email body
            if msg.is_multipart():
                for part in msg.get_payload():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            # Truncate body if too long
            body = body[:300] + "..." if len(body) > 300 else body

            email_text = f"From: {from_addr}\nSubject: {subject}\n\n{body}"

            app.after(
                0,
                app.add_message,
                "System",
                f"📧 Latest Email:\n\n{email_text}",
                "ai",
            )

            mail.close()
            mail.logout()

        except imaplib.IMAP4.error as e:
            app.after(
                0,
                app.add_message,
                "System",
                f"❌ Email login failed: {e}. Ensure you're using an App Password.",
                "error",
            )
        except Exception as e:
            app.after(
                0,
                app.add_message,
                "System",
                f"❌ Email error: {e}",
                "error",
            )

    # Run in background thread
    threading.Thread(target=fetch_email, daemon=True).start()


def open_email_reader(app):
    """Open the email reader interface."""
    # Close existing instance if open
    if hasattr(app, 'email_reader_instance') and app.email_reader_instance:
        app.email_reader_instance.destroy()
    
    reader = EmailReader(app)
    app.email_reader_instance = reader
    reader.grab_set()


class EmailReader(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Email Reader - Firefly AI")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkLabel(self, text="📧 Email Reader", font=("Segoe UI", 16, "bold"))
        header.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        
        # Email list
        self.email_list = ctk.CTkScrollableFrame(self)
        self.email_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="Loading emails...")
        self.status_label.grid(row=2, column=0, pady=5, padx=10, sticky="w")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(self, text="Refresh", command=self.load_emails)
        refresh_btn.grid(row=3, column=0, pady=10, padx=10, sticky="e")
        
        # Load emails
        self.load_emails()
    
    def load_emails(self):
        """Load and display emails."""
        # Clear existing
        for widget in self.email_list.winfo_children():
            widget.destroy()
        
        self.status_label.configure(text="Fetching emails...")
        
        def fetch():
            try:
                emails = self.fetch_emails()
                self.after(0, lambda: self.display_emails(emails))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(text=f"Error: {str(e)}"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def fetch_emails(self):
        """Fetch recent emails."""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        email_address = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_PASSWORD")
        imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        
        if not email_address or not password:
            raise Exception("Email credentials not configured. Check your .env file.")
        
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select("inbox")
        
        _, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        
        emails = []
        for i in range(min(10, len(email_ids))):  # Last 10 emails
            latest_id = email_ids[-(i+1)]
            _, msg_data = mail.fetch(latest_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            from_addr = msg.get("From", "Unknown")
            subject = msg.get("Subject", "No Subject")
            date = msg.get("Date", "Unknown")
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.get_payload():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            
            body = body[:200] + "..." if len(body) > 200 else body
            
            emails.append({
                'from': from_addr,
                'subject': subject,
                'date': date,
                'body': body
            })
        
        mail.close()
        mail.logout()
        return emails
    
    def display_emails(self, emails):
        """Display emails in the list."""
        if not emails:
            ctk.CTkLabel(self.email_list, text="No emails found.").pack(pady=20)
            self.status_label.configure(text="")
            return
        
        for email_data in emails:
            frame = ctk.CTkFrame(self.email_list)
            frame.pack(fill="x", padx=5, pady=5)
            
            # From and Subject
            from_label = ctk.CTkLabel(frame, text=f"From: {email_data['from']}", font=("Segoe UI", 12, "bold"))
            from_label.pack(anchor="w", padx=10, pady=2)
            
            subject_label = ctk.CTkLabel(frame, text=f"Subject: {email_data['subject']}", font=("Segoe UI", 10))
            subject_label.pack(anchor="w", padx=10, pady=2)
            
            # Body preview
            body_label = ctk.CTkLabel(frame, text=email_data['body'], font=("Segoe UI", 9), wraplength=700, justify="left")
            body_label.pack(anchor="w", padx=10, pady=5)
        
        self.status_label.configure(text=f"Loaded {len(emails)} emails")
