import frappe
import json
from frappe.utils import flt, getdate

@frappe.whitelist()
def process_bank_statement(file_url):
    # In a real scenario, we would parse CSV/Excel from file_url
    # For this demonstration, we'll assume the user uploaded a file 
    # and we are extracting rows.
    
    # Placeholder: List of deposited PDCs to check against
    deposited_pdcs = frappe.get_all("PDC Cheque", 
        filters={"status": "Deposited", "docstatus": 1},
        fields=["name", "customer", "amount", "cheque_no", "payment_entry", "deposit_journal_entry"]
    )
    
    # Mock data representing what was found in the bank statement
    # In production, this would come from the uploaded file
    matches = []
    for pdc in deposited_pdcs:
        matches.append({
            "pdc_id": pdc.name,
            "customer": pdc.customer,
            "amount": pdc.amount,
            "cheque_no": pdc.cheque_no,
            "payment_entry": pdc.payment_entry,
            "deposit_journal_entry": pdc.deposit_journal_entry,
            "status": "Matched",
            "reason": "Exact amount found in statement"
        })
        
    return matches

@frappe.whitelist()
def clear_pdc(pdc_id, clearance_date):
    doc = frappe.get_doc("PDC Cheque", pdc_id)
    if doc.status == "Deposited":
        doc.status = "Cleared"
        doc.custom_clearance_date = clearance_date
        doc.save(ignore_permissions=True)
        return {"status": "success", "message": f"Cheque {pdc_id} marked as Cleared."}
    return {"status": "error", "message": "Cheque is not in Deposited status."}

@frappe.whitelist()
def get_customer_account(company, customer):
    from erpnext.accounts.party import get_party_account
    return get_party_account("Customer", customer, company)

@frappe.whitelist()
def fetch_outstanding_invoices(customer, company, amount):
    """
    Manually fetches outstanding invoices and calculates allocation.
    This replaces the buggy ERPNext internal call.
    """
    invoices = frappe.get_all("Sales Invoice",
        filters={
            "customer": customer,
            "company": company,
            "docstatus": 1,
            "outstanding_amount": [">", 0]
        },
        fields=["name", "outstanding_amount", "posting_date", "due_date"],
        order_by="due_date asc"
    )

    remaining_amount = flt(amount)
    allocation = []

    for inv in invoices:
        if remaining_amount <= 0:
            break
        
        allocated = min(flt(inv.outstanding_amount), remaining_amount)
        allocation.append({
            "sales_invoice": inv.name,
            "outstanding_amount": inv.outstanding_amount,
            "allocated_amount": allocated
        })
        remaining_amount -= allocated

    return allocation
