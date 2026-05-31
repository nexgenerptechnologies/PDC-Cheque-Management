# PDC Cheque Management for ERPNext

<div align="center">
  <h3>An enterprise-grade Post-Dated Cheque (PDC) lifecycle management application for Frappe & ERPNext.</h3>
</div>

**PDC Cheque Management** is a powerful, bi-directional banking automation tool designed to eliminate manual data entry, streamline bank reconciliations, and handle complex multi-currency allocations natively within ERPNext. Whether you are receiving PDCs from Customers or issuing PDCs to Suppliers, this app handles the entire accounting lifecycle automatically.

---

## ðŸŒŸ Key Features

### 1. Bi-Directional Party Engine
Seamlessly manage both Accounts Receivable (Customers) and Accounts Payable (Suppliers) from a single unified interface. The system intelligently adapts its behavior based on the direction of money flow.

### 2. Intelligent Holding Accounts
Configure default Temporary Bank/Cash holding accounts for both Receivables (e.g., *Cheque In Hand*) and Payables (e.g., *PDCs Issued*). The UI dynamically auto-switches to the correct holding ledger the moment you select the Party Type.

### 3. Flawless Multi-Currency & Ledger Integration
* Automatically detects the Supplier/Customer's underlying Account Currency.
* Natively converts foreign currency invoices against your Base Currency ledger accounts using historical conversion rates.
* Perfectly mirrors standard ERPNext Payment Entry logic, ensuring **Exchange Gain/Loss** journal entries are generated accurately and effortlessly in the background.

### 4. Automated Payment Entry Generation
When a cheque is marked as "Received" or "Issued," the engine auto-generates the corresponding Payment Entry, automatically calculating allocations and intelligently mapping paid_from and paid_to accounts based on the transaction type.

### 5. Bulk PDC Clearance Tool
Tired of clearing cheques one by one? Use the built-in **PDC Clearance Tool** to filter cheques by Date, Bank, or Status. Mark dozens of cheques as "Cleared" or "Deposited" with a single click, automating your daily banking workflows instantly.

### 6. Full Cheque Lifecycle Tracking
Track complete status histories including:
* Draft
* Received / Issued
* Deposited
* Cleared
* Cancelled
* Bounced (with automated Bounce Date & Reason tracking)

---

## ðŸ› ï¸ Installation

From your Frappe bench, run the following commands:

`ash
bench get-app https://github.com/nexgenerptechnologies/PDC-Cheque-Management.git
bench --site [your-site-name] install-app pdc_cheque_management
bench --site [your-site-name] migrate
`

## ðŸ“ License

This project is licensed under the MIT License.
## Support & Contact

If you have any questions, encounter any issues, or require customizations, our support team at **Nexgen ERP Technologies** is ready to help!

* 💬 **WhatsApp:** [Click to chat with us (+91-9811920503)](https://wa.me/919811920503)
* 📧 **Email:** [nexgenerptechnologies@gmail.com](mailto:nexgenerptechnologies@gmail.com)

## Legal

* [Terms of Service](TERMS_OF_SERVICE.md)
* [Privacy Policy](PRIVACY_POLICY.md)