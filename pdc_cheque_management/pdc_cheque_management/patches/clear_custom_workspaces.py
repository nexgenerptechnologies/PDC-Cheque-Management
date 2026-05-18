import frappe

def execute():
    # Remove any customized (is_standard=0) workspaces that might be overriding the app's workspace
    # Also remove any variations like PDC Management Dashboard if they were created during our testing
    workspaces_to_clear = [
        "PDC Cheque Management",
        "pdc_cheque_management",
        "PDC Management Dashboard"
    ]
    
    for ws in workspaces_to_clear:
        try:
            frappe.db.delete("Workspace", {"name": ["like", f"%{ws}%"]})
        except Exception:
            pass

    frappe.db.commit()
    frappe.clear_cache()
