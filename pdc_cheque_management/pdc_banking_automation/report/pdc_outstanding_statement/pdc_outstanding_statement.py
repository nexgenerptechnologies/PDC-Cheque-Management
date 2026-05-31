import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("Gross Outstanding"),
            "fieldname": "gross_outstanding",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("PDC Received (Not Cleared)"),
            "fieldname": "pdc_received",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": _("Net Outstanding"),
            "fieldname": "net_outstanding",
            "fieldtype": "Currency",
            "width": 150
        }
    ]

def get_data(filters):
    conditions = []
    values = {}
    
    if filters.get("customer"):
        conditions.append("customer = %(customer)s")
        values["customer"] = filters.get("customer")
    if filters.get("company"):
        conditions.append("company = %(company)s")
        values["company"] = filters.get("company")

    where_clause = ""
    if conditions:
        where_clause = " AND " + " AND ".join(conditions)

    # 1. Get Gross Outstanding (From Sales Invoices)
    query_invoices = (
        "SELECT customer, SUM(outstanding_amount) as gross_outstanding "
        "FROM `tabSales Invoice` "
        "WHERE docstatus = 1 AND outstanding_amount > 0 " + where_clause + " "
        "GROUP BY customer"
    )
    invoices = frappe.db.sql(query_invoices, values, as_dict=1)

    # 2. Get PDC Received (Status Received or Deposited)
    query_pdcs = (
        "SELECT customer, SUM(amount) as pdc_received "
        "FROM `tabPDC Cheque` "
        "WHERE docstatus < 2 AND status IN ('Received', 'Deposited') " + where_clause + " "
        "GROUP BY customer"
    )
    pdcs = frappe.db.sql(query_pdcs, values, as_dict=1)

    # Map them together
    customer_data = {}
    
    for inv in invoices:
        customer_data[inv.customer] = {
            "customer": inv.customer,
            "gross_outstanding": inv.gross_outstanding,
            "pdc_received": 0,
            "net_outstanding": inv.gross_outstanding
        }

    for pdc in pdcs:
        if pdc.customer in customer_data:
            customer_data[pdc.customer]["pdc_received"] = pdc.pdc_received
            customer_data[pdc.customer]["net_outstanding"] = customer_data[pdc.customer]["gross_outstanding"] - pdc.pdc_received
        else:
            customer_data[pdc.customer] = {
                "customer": pdc.customer,
                "gross_outstanding": 0,
                "pdc_received": pdc.pdc_received,
                "net_outstanding": -pdc.pdc_received
            }

    return list(customer_data.values())
