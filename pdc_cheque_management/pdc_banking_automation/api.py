import frappe
from frappe.utils import flt

@frappe.whitelist()
def fetch_outstanding_invoices(party_type, party, company, amount, currency="INR"):
    doctype = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
    party_field = "customer" if party_type == "Customer" else "supplier"

    company_currency = frappe.db.get_value("Company", company, "default_currency")
    
    from erpnext.accounts.party import get_party_account
    party_account = get_party_account(party_type, party, company)
        
    account_currency = frappe.db.get_value("Account", party_account, "account_currency")
    if not account_currency:
        account_currency = company_currency

    invoices = frappe.get_all(doctype,
        filters={party_field: party, "company": company, "docstatus": 1, "outstanding_amount": [">", 0]},
        fields=["name", "outstanding_amount", "conversion_rate", "posting_date", "due_date", "currency"],
        order_by="due_date asc"
    )

    party_amount = flt(amount)
    if currency != account_currency:
        try:
            from erpnext.setup.utils import get_exchange_rate
            rate = get_exchange_rate(currency, account_currency)
            party_amount = flt(amount) * flt(rate)
        except Exception:
            pass

    remaining_amount = party_amount
    allocation = []

    for inv in invoices:
        if remaining_amount <= 0:
            break

        if account_currency == company_currency and inv.currency != company_currency:
            inv_outstanding = flt(inv.outstanding_amount) * flt(inv.conversion_rate or 1.0)
            inv_curr = company_currency
        else:
            inv_outstanding = flt(inv.outstanding_amount)
            inv_curr = inv.currency

        if inv_outstanding <= 0:
            continue

        allocated = min(inv_outstanding, remaining_amount)
        if allocated > 0:
            allocation.append({
                "reference_doctype": doctype,
                "reference_name": inv.name,
                "outstanding_amount": inv_outstanding,
                "allocated_amount": allocated,
                "invoice_currency": inv_curr
            })
            remaining_amount -= allocated

    return allocation
@frappe.whitelist()
def get_pdc_cheques(filters):
    if isinstance(filters, str):
        import json
        filters = json.loads(filters)
        
    query_filters = {"docstatus": ["<", 2]}
    if filters.get("from_date"):
        query_filters["cheque_date"] = [">=", filters.get("from_date")]
    if filters.get("to_date"):
        if "cheque_date" in query_filters:
            query_filters["cheque_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
        else:
            query_filters["cheque_date"] = ["<=", filters.get("to_date")]
    if filters.get("status"):
        query_filters["status"] = filters.get("status")
    if filters.get("party_type") and filters.get("party"):
        query_filters["party_type"] = filters.get("party_type")
        query_filters["party"] = filters.get("party")

    return frappe.get_all("PDC Cheque", filters=query_filters, fields=["name", "cheque_no", "cheque_date", "party", "amount", "currency", "status"], order_by="cheque_date asc")

@frappe.whitelist()
def bulk_update_cheques(cheque_names, target_status, action_date):
    if isinstance(cheque_names, str):
        import json
        cheque_names = json.loads(cheque_names)
        
    for name in cheque_names:
        doc = frappe.get_doc("PDC Cheque", name)
        if not doc.party:
            frappe.throw(f"Cheque {doc.cheque_no or doc.name} is missing a Party. Please open it and assign a Party first.")
        if not doc.custom_invoices:
            frappe.throw(f"Cheque {doc.cheque_no or doc.name} is missing Allocated Invoices. Please open it and allocate invoices first.")
        if target_status == "Cleared" or target_status == "Deposited":
            doc.custom_clearance_date = action_date
        elif target_status == "Bounced":
            doc.bounce_date = action_date
            
        doc.status = target_status
        doc.save()
        
    return {"status": "success"}