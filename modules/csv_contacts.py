# --- Standard Library Imports ---
import csv
import os
import threading
from tkinter import filedialog

# --- Local Imports ---
from . import contacts as contact_manager

def import_contacts_from_csv(app):
    """
    Opens a file dialog to select a CSV file and imports contacts from it.
    """
    file_path = filedialog.askopenfilename(
        title="Select Contacts CSV",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )

    if not file_path:
        return

    def _run():
        try:
            app.after(0, lambda: app.add_message("System", f"🔄 Importing contacts from {os.path.basename(file_path)}...", "ai"))
            
            imported_count = 0
            existing_contacts = {c['phone'] for c in contact_manager.load_contacts() if 'phone' in c}
            
            with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Normalize headers to lowercase for easier matching
                headers = [h.lower() for h in reader.fieldnames or []]
                
                # Find the best matching columns for name and phone
                name_col = next((h for h in headers if 'name' in h), None)
                phone_col = next((h for h in headers if 'phone' in h or 'mobile' in h or 'cell' in h), None)
                
                if not name_col or not phone_col:
                    app.after(0, lambda: app.add_message("System", "❌ Error: Could not identify 'Name' or 'Phone' columns in CSV.", "error"))
                    return

                # Map back to original case-sensitive headers
                original_name_col = [h for h in reader.fieldnames if h.lower() == name_col][0]
                original_phone_col = [h for h in reader.fieldnames if h.lower() == phone_col][0]

                for row in reader:
                    name = row.get(original_name_col, "").strip()
                    phone = row.get(original_phone_col, "").strip()
                    
                    # Basic cleanup of phone number (keep only digits and +)
                    if phone:
                        phone = "".join(filter(lambda x: x.isdigit() or x == '+', phone))

                    if name and phone and phone not in existing_contacts:
                        contact_manager.add_contact(name, phone)
                        existing_contacts.add(phone)
                        imported_count += 1

            if imported_count > 0:
                msg = f"✅ Successfully imported {imported_count} new contact(s) from CSV."
                # Refresh the calendar view if it's open
                if hasattr(app, 'calendar_view_instance') and app.calendar_view_instance:
                    app.calendar_view_instance.update_contacts_list()
            else:
                msg = "ℹ️ No new contacts found to import."

            app.after(0, lambda: app.add_message("System", msg, "ai"))

        except Exception as e:
            error_msg = f"❌ An error occurred during CSV import: {e}"
            app.after(0, lambda: app.add_message("System", error_msg, "error"))

    threading.Thread(target=_run, daemon=True).start()
