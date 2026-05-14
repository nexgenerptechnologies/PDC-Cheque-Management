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

    get_outstanding_invoices_btn: function(frm) {
        if (!frm.doc.customer || !frm.doc.amount) {
            frappe.msgprint(__("Please select a <b>Customer</b> and enter an <b>Amount</b> first."));
            return;
        }

        frappe.call({
            method: "pdc_cheque_management.pdc_cheque_management.api.fetch_outstanding_invoices",
            args: {
                customer: frm.doc.customer,
                company: frm.doc.company,
                amount: frm.doc.amount
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    frm.clear_table("custom_invoices");
                    r.message.forEach(d => {
                        let row = frm.add_child("custom_invoices");
                        row.sales_invoice = d.sales_invoice;
                        row.outstanding_amount = d.outstanding_amount;
                        row.allocated_amount = d.allocated_amount;
                    });
                    frm.refresh_field("custom_invoices");
                    frappe.show_alert({message: __("Invoices fetched and allocated."), indicator: 'green'});
                } else {
                    frappe.msgprint(__("No outstanding invoices found for this customer."));
                }
            }
        });
    }
});
