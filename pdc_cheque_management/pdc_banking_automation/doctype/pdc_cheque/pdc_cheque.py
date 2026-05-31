import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, flt

class PDCCheque(Document):
    def validate(self):
        # Fetch defaults if empty
        if not self.holding_account:
            if self.party_type == "Supplier":
                self.holding_account = frappe.db.get_single_value("PDC Banking Settings", "default_payable_holding_account")
            else:
                self.holding_account = frappe.db.get_single_value("PDC Banking Settings", "default_holding_account")
        if not self.main_bank_account:
            self.main_bank_account = frappe.db.get_single_value("PDC Banking Settings", "default_main_bank_account")
            
        # This logic runs before every save
        self.process_status_change()

    def process_status_change(self):
        # --- 1. RECEIVED or ISSUED ---
        if self.status in ["Received", "Issued"] and not self.payment_entry:
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
            frappe.throw("Please add invoices in the table or fetch outstanding invoices.")

        pe = frappe.new_doc("Payment Entry")
        pe.payment_type = "Pay" if self.party_type == "Supplier" else "Receive"
        pe.party_type = self.party_type
        pe.party = self.party
        pe.company = self.company
        pe.posting_date = today()
        
        party_currency = frappe.db.get_value(self.party_type, self.party, "default_currency") or frappe.db.get_value("Company", self.company, "default_currency")
        party_amount = self.amount
        
        if self.currency != party_currency:
            try:
                from erpnext.setup.utils import get_exchange_rate
                rate = get_exchange_rate(self.currency, party_currency)
                party_amount = flt(self.amount) * flt(rate)
            except Exception:
                pass
                
        if self.party_type == "Supplier":
            pe.paid_from = self.holding_account
            pe.paid_amount = self.amount
            pe.received_amount = party_amount
        else:
            pe.paid_to = self.holding_account
            pe.received_amount = self.amount
            pe.paid_amount = party_amount
            
        pe.reference_no = self.cheque_no
        pe.reference_date = self.cheque_date

        total_allocated = 0
        for row in self.custom_invoices:
            pe.append("references", {
                "reference_doctype": row.reference_doctype, 
                "reference_name": row.reference_name, 
                "allocated_amount": row.allocated_amount
            })
            total_allocated += flt(row.allocated_amount)

        if flt(total_allocated, 2) > flt(party_amount, 2):
            frappe.throw(f"Cannot allocate more than Cheque Amount Equivalent ({party_amount} {party_currency})")
        
        pe.setup_party_account_field()
        pe.set_missing_values()
        
        pe.insert(ignore_permissions=True)
        pe.submit()
        self.payment_entry = pe.name
        frappe.msgprint(f"Payment Entry {pe.name} created.")

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
        frappe.msgprint(f"Deposit Journal Entry {je.name} created.")

    def handle_bounce_or_cancel(self):
        has_cancelled = False
        if self.deposit_journal_entry:
            try:
                d_je = frappe.get_doc("Journal Entry", self.deposit_journal_entry)
                if d_je.docstatus == 1:
                    # Reset clearance date if it was cleared
                    if d_je.clearance_date:
                        d_je.db_set("clearance_date", None)
                    d_je.cancel()
                    has_cancelled = True
            except Exception as e:
                frappe.msgprint(f"Failed to cancel Deposit Journal Entry: {str(e)}")

        if self.payment_entry:
            try:
                p_pe = frappe.get_doc("Payment Entry", self.payment_entry)
                if p_pe.docstatus == 1:
                    p_pe.cancel()
                    has_cancelled = True
            except Exception as e:
                frappe.msgprint(f"Failed to cancel Payment Entry: {str(e)}")

        if self.status == "Bounced" and flt(self.bank_charges) > 0 and not self.bounce_journal_entry:
            acc = self.custom_bank_charges_account or frappe.db.get_single_value("PDC Banking Settings", "default_bank_charges_account")
            if not acc:
                frappe.throw("Please configure Default Bank Charges Account in PDC Banking Settings.")
            cje = frappe.new_doc("Journal Entry")
            cje.company = self.company
            cje.posting_date = self.bounce_date or today()
            cje.voucher_type = "Bank Entry"
            cje.cheque_no = self.cheque_no
            cje.cheque_date = self.cheque_date
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
            frappe.throw(f"ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚ÂÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Clearance Date cannot be before Cheque Date.")
        frappe.db.set_value("Journal Entry", self.deposit_journal_entry, "clearance_date", actual_date)



