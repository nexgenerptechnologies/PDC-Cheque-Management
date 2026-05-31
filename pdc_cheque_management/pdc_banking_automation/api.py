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
        fields=["name", "outstanding_amount", "base_outstanding_amount", "posting_date", "due_date", "currency"],
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