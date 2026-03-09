# --- Standard Library Imports ---
import os
import pickle
import threading

# --- Third-Party Imports ---
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Local Imports ---
from . import config
from . import contacts as contact_manager

# --- Scopes and Credentials ---
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
CLIENT_SECRET_FILE = os.path.join(config.BASE_DIR, 'client_secret.json')
TOKEN_FILE = os.path.join(config.BASE_DIR, 'token.pickle')

def get_google_credentials():
    """
    Handles the OAuth 2.0 flow to get user credentials.
    A browser window will open for the user to grant permission.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                return None # Abort if client_secret.json is missing
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
            
    return creds

def fetch_contacts(app):
    """
    Fetches contacts from the Google People API and adds them to the local contacts list.
    This function runs in a background thread to keep the UI responsive.
    """
    def _run():
        try:
            app.after(0, lambda: app.add_message("System", "🔄 Starting Google Contacts import...", "ai"))
            
            creds = get_google_credentials()
            if not creds:
                app.after(0, lambda: app.add_message("System", "❌ Error: `client_secret.json` not found. Please follow setup instructions.", "error"))
                return

            service = build('people', 'v1', credentials=creds)

            # Call the People API
            results = service.people().connections().list(
                resourceName='people/me',
                pageSize=500,  # Get up to 500 contacts
                personFields='names,phoneNumbers'
            ).execute()
            
            connections = results.get('connections', [])

            if not connections:
                app.after(0, lambda: app.add_message("System", "ℹ️ No contacts found in your Google account.", "ai"))
                return

            imported_count = 0
            existing_contacts = {c['phone'] for c in contact_manager.load_contacts() if 'phone' in c}

            for person in connections:
                names = person.get('names', [])
                phone_numbers = person.get('phoneNumbers', [])
                
                if names and phone_numbers:
                    name = names[0].get('displayName')
                    phone = phone_numbers[0].get('value')

                    # Basic cleanup of phone number
                    if phone:
                        phone = "".join(filter(str.isdigit, phone))

                    # Add if we have a name, phone, and it's not a duplicate
                    if name and phone and phone not in existing_contacts:
                        contact_manager.add_contact(name, phone)
                        existing_contacts.add(phone) # Add to our set to prevent duplicates within the same import
                        imported_count += 1
            
            if imported_count > 0:
                msg = f"✅ Successfully imported {imported_count} new contact(s) from Google."
                # The calendar view needs to be told to refresh its list
                if hasattr(app, 'calendar_view_instance') and app.calendar_view_instance:
                    app.calendar_view_instance.update_contacts_list()
            else:
                msg = "ℹ️ All Google Contacts are already in your list."

            app.after(0, lambda: app.add_message("System", msg, "ai"))

        except Exception as e:
            error_msg = f"❌ An error occurred during Google Contact import: {e}"
            app.after(0, lambda: app.add_message("System", error_msg, "error"))

    # Run the entire process in a background thread
    threading.Thread(target=_run, daemon=True).start()
