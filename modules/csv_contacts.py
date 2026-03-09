"""
CSV Contacts module for Firefly AI.
Provides functionality to import and export contacts from/to CSV files.
"""

import csv
import os
from tkinter import filedialog, messagebox
from . import contacts


def import_contacts_from_csv(parent):
    """
    Open a file dialog to import contacts from a CSV file.
    
    Args:
        parent: Parent window for the file dialog
    """
    file_path = filedialog.askopenfilename(
        parent=parent,
        title="Select CSV file to import contacts",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not file_path:
        return
    
    try:
        imported_count = 0
        failed_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect if the first row is a header
            reader = csv.reader(f)
            first_row = next(reader, None)
            
            if not first_row:
                messagebox.showwarning("Error", "CSV file is empty")
                return
            
            # Check if first row looks like headers
            is_header = all(col.lower() in ['name', 'email', 'phone', 'address', 'contact', 'mail'] 
                           for col in first_row)
            
            # Reset reader
            f.seek(0)
            reader = csv.reader(f)
            
            # Skip header if detected
            if is_header:
                next(reader)
            
            # Process rows
            for row in reader:
                try:
                    if len(row) < 1:
                        continue
                    
                    name = row[0].strip() if row[0] else ""
                    email = row[1].strip() if len(row) > 1 else ""
                    phone = row[2].strip() if len(row) > 2 else ""
                    address = row[3].strip() if len(row) > 3 else ""
                    
                    if name:
                        success = contacts.add_contact(name, email, phone, address)
                        if success:
                            imported_count += 1
                        else:
                            failed_count += 1
                            
                except Exception as e:
                    failed_count += 1
                    print(f"Error importing row: {e}")
        
        message = f"✅ Imported {imported_count} contacts successfully"
        if failed_count > 0:
            message += f"\n⚠️ Failed to import {failed_count} contacts (duplicates or invalid)"
        
        messagebox.showinfo("Import Complete", message)
        
    except Exception as e:
        messagebox.showerror("Import Error", f"Error importing CSV: {str(e)}")


def export_contacts_to_csv(parent):
    """
    Open a file dialog to export contacts to a CSV file.
    
    Args:
        parent: Parent window for the file dialog
    """
    file_path = filedialog.asksaveasfilename(
        parent=parent,
        title="Save contacts as CSV",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not file_path:
        return
    
    try:
        contact_list = contacts.load_contacts()
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Name', 'Email', 'Phone', 'Address'])
            
            # Write contacts
            for contact in contact_list:
                writer.writerow([
                    contact.get('name', ''),
                    contact.get('email', ''),
                    contact.get('phone', ''),
                    contact.get('address', '')
                ])
        
        messagebox.showinfo("Export Complete", f"✅ Exported {len(contact_list)} contacts to CSV")
        
    except Exception as e:
        messagebox.showerror("Export Error", f"Error exporting contacts: {str(e)}")
