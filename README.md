# PDC Cheque Management

An advanced ERPNext v15/v16 application for managing Post-Dated Cheques (PDC) with automated invoice allocation.

## Features
- **Fetch Outstanding Invoices**: Automatically retrieve and allocate cheque amounts to unpaid invoices.
- **Automated Workflow**: Handles status transitions from Received to Deposited, Cleared, or Bounced.
- **Automated Accounting**: Automatically creates Payment Entries and Journal Entries based on cheque status.
- **Bank Charges Tracking**: Records bank charges for bounced cheques.
- **Premium UI**: Custom styling for clear status visibility and better user experience.

## Installation
1. Clone the repository to your `apps` folder:
   ```bash
   git clone https://github.com/nexgenerptechnologies/PDC-Cheque-Management.git
   ```
2. Install the app on your site:
   ```bash
   bench --site [your-site-name] install-app pdc_cheque_management
   ```
3. Migrate the site:
   ```bash
   bench --site [your-site-name] migrate
   ```

## License
MIT
