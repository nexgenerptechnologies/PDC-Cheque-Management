frappe.ui.form.on('PDC Cheque', {
    refresh: function(frm) {
        if (frm.is_new()) return;

        // Apply invoice filter for the table
        frm.set_query('sales_invoice', 'custom_invoices', function() {
            return {
                filters: {
                    customer: frm.doc.customer,
                    docstatus: 1,
                    outstanding_amount: ['>', 0]
                }
            };
        });

        // Get Outstanding Invoices Button
        if (frm.doc.customer && frm.doc.amount && (!frm.doc.status || ['Draft', 'Received'].includes(frm.doc.status))) {
            frm.add_custom_button(__('Get Outstanding Invoices'), () => {
                frm.events.get_outstanding_invoices(frm);
            }, __('Actions')).addClass('btn-info');
        }

        let s = frm.doc.status;
        if (!s || s === 'Draft') {
            frm.add_custom_button('Mark as Received', () => {
                frappe.confirm('Record payment for these invoices?', () => {
                    frm.set_value('status', 'Received');
                    frm.save();
                });
            }).addClass('btn-primary');
        } 
        else if (s === 'Received') {
            frm.add_custom_button('Mark as Deposited', () => {
                frm.set_value('status', 'Deposited');
                frm.save();
            }).addClass('btn-warning');
            
            frm.add_custom_button('Cancel Cheque', () => {
                frappe.confirm('Cancel this cheque?', () => {
                    frm.set_value('status', 'Cancelled');
                    frm.save();
                });
            }).addClass('btn-danger');
        } 
        else if (s === 'Deposited') {
            frm.add_custom_button('Mark as Cleared', () => {
                if (!frm.doc.custom_clearance_date) {
                    frappe.msgprint(__("Please enter the <b>Clearance Date</b> first."));
                    return;
                }
                frm.set_value('status', 'Cleared');
                frm.save();
            }).addClass('btn-success');

            frm.add_custom_button('Mark as Bounced', () => {
                frappe.prompt([
                    {label:'Bounce Date', fieldname:'bounce_date', fieldtype:'Date', reqd:1, default:frappe.datetime.get_today()},
                    {label:'Reason', fieldname:'bounce_reason', fieldtype:'Small Text', reqd:1},
                    {label:'Charges', fieldname:'bank_charges', fieldtype:'Currency', default:0}
                ], (v) => {
                    frm.set_value('bounce_date', v.bounce_date);
                    frm.set_value('bounce_reason', v.bounce_reason);
                    frm.set_value('bank_charges', v.bank_charges || 0);
                    frm.set_value('status', 'Bounced');
                    frm.save();
                }, 'Cheque Bounce');
            }).addClass('btn-danger');
        }
    },

    get_outstanding_invoices: function(frm) {
        frappe.call({
            method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents",
            args: {
                args: {
                    "posting_date": frm.doc.cheque_date || frappe.datetime.get_today(),
                    "company": frm.doc.company,
                    "party_type": "Customer",
                    "party": frm.doc.customer,
                    "bank_account": frm.doc.holding_account,
                    "received_amount": frm.doc.amount,
                    "payment_type": "Receive"
                }
            },
            callback: function(r) {
                if (r.message) {
                    frm.clear_table("custom_invoices");
                    let total_allocated = 0;
                    let cheque_amount = frm.doc.amount;

                    r.message.forEach(d => {
                        if (total_allocated < cheque_amount) {
                            let amount_to_allocate = Math.min(d.outstanding_amount, cheque_amount - total_allocated);
                            let row = frm.add_child("custom_invoices");
                            row.sales_invoice = d.voucher_no;
                            row.outstanding_amount = d.outstanding_amount;
                            row.allocated_amount = amount_to_allocate;
                            total_allocated += amount_to_allocate;
                        }
                    });
                    frm.refresh_field("custom_invoices");
                }
            }
        });
    }
});
