import frappe
import json
from frappe.utils import flt, getdate, today

@frappe.whitelist()
def process_bank_statement(file_url):
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    
    rows = []
    if file_doc.file_name.endswith('.csv'):
        from frappe.utils.csvutils import read_csv_content
        content = file_doc.get_content()
        rows = read_csv_content(content)
    elif file_doc.file_name.endswith('.xlsx') or file_doc.file_name.endswith('.xls'):
        from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
        rows = read_xlsx_file_from_attached_file(file_doc.name)
    else:
        frappe.throw("Unsupported file format. Please upload CSV or Excel.")

    if not rows or len(rows) < 2:
        frappe.throw("Empty or invalid bank statement file.")

    # Find column indices dynamically
    headers = [str(x).strip().lower() for x in rows[0]]
    
    try:
        col_cheque = headers.index('chequeno.')
        col_desc = headers.index('description')
        col_crdr = headers.index('cr/dr')
        col_amount = headers.index('transaction amount(inr)')
    except ValueError as e:
        frappe.throw(f"Missing required columns in statement. Ensure 'ChequeNo.', 'Description', 'Cr/Dr', 'Transaction Amount(INR)' exist. Error: {e}")

    results = []
    
    active_pdcs = frappe.get_all("PDC Cheque", 
        filters={"status": ["in", ["Deposited", "Issued"]], "docstatus": 1},
        fields=["name", "party", "amount", "cheque_no", "payment_entry", "deposit_journal_entry", "status"]
    )
    pdc_map = {pdc.cheque_no.strip(): pdc for pdc in active_pdcs if pdc.cheque_no}

    for row in rows[1:]:
        if not row or len(row) <= col_desc or not row[col_desc]: continue
        
        cheque_val = str(row[col_cheque]).strip() if len(row) > col_cheque and row[col_cheque] else ""
        desc_val = str(row[col_desc]).strip().upper()
        cr_dr = str(row[col_crdr]).strip().upper() if len(row) > col_crdr and row[col_crdr] else ""
        amount_val = flt(row[col_amount]) if len(row) > col_amount else 0
        
        if amount_val <= 0: continue

        # 1. PDC Detection Logic
        if cheque_val and cheque_val != "-" and cheque_val != "None":
            matched_pdc = pdc_map.get(cheque_val)
            if matched_pdc and flt(matched_pdc.amount) == amount_val:
                results.append({
                    "match_type": "PDC",
                    "pdc_id": matched_pdc.name,
                    "party": matched_pdc.party,
                    "amount": amount_val,
                    "cheque_no": cheque_val,
                    "payment_entry": matched_pdc.payment_entry,
                    "status": "Ready to Clear",
                    "reason": "Exact cheque match"
                })
                continue
                
        # 2. NEFT Detection Logic
        if "NEFT" in desc_val or "RTGS" in desc_val or "IMPS" in desc_val or "UTR" in desc_val:
            results.append({
                "match_type": "NEFT",
                "pdc_id": "",
                "party": "Unassigned",
                "amount": amount_val,
                "cheque_no": cr_dr,
                "payment_entry": "",
                "status": "Unprocessed NEFT",
                "reason": desc_val
            })

    return results

@frappe.whitelist()
def clear_pdc(pdc_id, clearance_date):
    doc = frappe.get_doc("PDC Cheque", pdc_id)
    if doc.status in ["Deposited", "Issued"]:
        doc.status = "Cleared"
        doc.custom_clearance_date = clearance_date
        doc.save(ignore_permissions=True)
        return {"status": "success", "message": f"Cheque {pdc_id} marked as Cleared."}
    return {"status": "error", "message": "Cheque is not in Deposited or Issued status."}

@frappe.whitelist()
def fetch_outstanding_invoices(party_type, party, company, amount):
    doctype = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
    party_field = "customer" if party_type == "Customer" else "supplier"

    invoices = frappe.get_all(doctype,
        filters={
            party_field: party,
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
        if remaining_amount <= 0: break
        allocated = min(flt(inv.outstanding_amount), remaining_amount)
        allocation.append({
            "reference_doctype": doctype,
            "reference_name": inv.name,
            "outstanding_amount": inv.outstanding_amount,
            "allocated_amount": allocated
        })
        remaining_amount -= allocated

    return allocation