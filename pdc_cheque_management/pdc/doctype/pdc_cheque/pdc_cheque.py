import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, flt, format_currency

class PDCCheque(Document):
    def validate(self):
        # This logic runs before every save
        self.process_status_change()

    def process_status_change(self):
        # --- 1. RECEIVED ---
        if self.status == "Received" and not self.payment_entry:
            self.create_payment_entry()

        # --- 2. DEPOSITED ---
        elif self.status == "Deposited" and not self.deposit_journal_entry:
            self.create_deposit_journal_entry()

        # --- 3. BOUNCED or CANCELLED ---
        elif self.status in ["Bounced", "Cancelled"]:
            self.handle_bounce_or_cancel()

        # --- 4. CLEARED ---
        elif self.status == "Cleared" and self.deposit_journal_entry:
            self.update_clearance_date()

    def create_payment_entry(self):
        if not self.custom_invoices:
            frappe.throw("❌ Please add invoices in the table or fetch outstanding invoices.")

        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Receive"
        pe.party_type = "Customer"
        pe.party = self.customer
        pe.company = self.company
        pe.posting_date = today()
        pe.paid_to = self.holding_account
        pe.paid_amount = self.amount
        pe.received_amount = self.amount
        pe.reference_no = self.cheque_no
        pe.reference_date = self.cheque_date

        total_allocated = 0
        for row in self.custom_invoices:
            pe.append("references", {
                "reference_doctype": "Sales Invoice", 
                "reference_name": row.sales_invoice, 
                "allocated_amount": row.allocated_amount
            })
            total_allocated += flt(row.allocated_amount)

        if total_allocated > self.amount:
            frappe.throw(f"❌ Cannot allocate more than Cheque Amount ({self.amount})")
        
        pe.insert(ignore_permissions=True)
        pe.submit()
        self.payment_entry = pe.name
        frappe.msgprint(f"✅ Payment Entry {pe.name} created.")

    def create_deposit_journal_entry(self):
        je = frappe.new_doc("Journal Entry")
        je.company = self.company
        je.posting_date = today()
        je.voucher_type = "Bank Entry"
        je.cheque_no = self.cheque_no
        je.cheque_date = self.cheque_date
        
        je.append("accounts", {"account": self.main_bank_account, "debit_in_account_currency": self.amount})
        je.append("accounts", {"account": self.holding_account, "credit_in_account_currency": self.amount})
        
        je.insert(ignore_permissions=True)
        je.submit()
        self.deposit_journal_entry = je.name
        frappe.msgprint(f"✅ Deposit Journal Entry {je.name} created.")

    def handle_bounce_or_cancel(self):
        has_cancelled = False
        if self.deposit_journal_entry:
            try:
                d_je = frappe.get_doc("Journal Entry", self.deposit_journal_entry)
                if d_je.docstatus == 1:
                    d_je.cancel()
                    has_cancelled = True
            except: pass

        if self.payment_entry:
            try:
                p_pe = frappe.get_doc("Payment Entry", self.payment_entry)
                if p_pe.docstatus == 1:
                    p_pe.cancel()
                    has_cancelled = True
            except: pass

        if self.status == "Bounced" and flt(self.bank_charges) > 0 and not self.bounce_journal_entry:
            acc = self.custom_bank_charges_account or "BANK CHARGES - FEPL"
            cje = frappe.new_doc("Journal Entry")
            cje.company = self.company
            cje.posting_date = self.bounce_date or today()
            cje.voucher_type = "Bank Entry"
            cje.append("accounts", {"account": acc, "debit_in_account_currency": self.bank_charges})
            cje.append("accounts", {"account": self.main_bank_account, "credit_in_account_currency": self.bank_charges})
            cje.insert(ignore_permissions=True)
            cje.submit()
            self.bounce_journal_entry = cje.name

        if has_cancelled:
            self.payment_entry = None
            self.deposit_journal_entry = None

    def update_clearance_date(self):
        actual_date = self.custom_clearance_date or today()
        if getdate(actual_date) < getdate(self.cheque_date):
            frappe.throw(f"❌ Clearance Date cannot be before Cheque Date.")
        frappe.db.set_value("Journal Entry", self.deposit_journal_entry, "clearance_date", actual_date)
