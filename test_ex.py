import frappe
from erpnext.setup.utils import get_exchange_rate

@frappe.whitelist()
def test_exchange_rate():
    return get_exchange_rate('USD', 'INR')