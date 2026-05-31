import frappe

@frappe.whitelist()
def check_supplier():
    s = frappe.get_doc("Supplier", "KAMAYA ELECTRIC (M) SDN. BHD. COMPANY")
    account = s.default_payable_account or frappe.get_value("Company", "NexGen Enterprises", "default_payable_account")
    account_currency = frappe.get_value("Account", account, "account_currency")
    
    return {
        "supplier_currency": s.default_currency,
        "payable_account": account,
        "account_currency": account_currency
    }