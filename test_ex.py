import frappe
from erpnext.setup.utils import get_exchange_rate

from frappe import whitelist_for_tests
@whitelist_for_tests()
def test_exchange_rate():
    return get_exchange_rate('USD', 'INR')
