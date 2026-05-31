frappe.ui.form.on('PDC Cheque', {
    refresh: function(frm) {
        if (frm.is_new()) return;

        // Apply invoice filter for the table
        frm.set_query('reference_name', 'custom_invoices', function() {
            let filter_field = frm.doc.party_type === "Customer" ? "customer" : "supplier";
            let filters = {
                docstatus: 1,
                outstanding_amount: ['>', 0]
            };
            filters[filter_field] = frm.doc.party;
            return { filters: filters };
        });

        frm.set_query('reference_doctype', 'custom_invoices', function() {
            return {
                filters: {
                    name: ['in', ['Sales Invoice', 'Purchase Invoice']]
                }
            };
        });

        let s = frm.doc.status;
        if (!s || s === 'Draft') {
            let action_label = frm.doc.party_type === "Supplier" ? 'Mark as Issued' : 'Mark as Received';
            let action_status = frm.doc.party_type === "Supplier" ? 'Issued' : 'Received';
            
            frm.add_custom_button(action_label, () => {
                frappe.confirm('Record payment for these invoices?', () => {
                    frm.set_value('status', action_status);
                    frm.save();
                });
            }).addClass('btn-primary');
        } 
        else if (s === 'Received' || s === 'Issued') {
            let action_label = frm.doc.party_type === "Supplier" ? 'Mark as Cleared' : 'Mark as Deposited';
            let action_status = frm.doc.party_type === "Supplier" ? 'Cleared' : 'Deposited';
            
            frm.add_custom_button(action_label, () => {
                frm.set_value('status', action_status);
                frm.save();
            }).addClass('btn-warning');
            
            frm.add_custom_button('Cancel Cheque', () => {
                frappe.confirm('Cancel this cheque?', () => {
                    frm.set_value('status', 'Cancelled');
                    frm.save();
                });
            }).addClass('btn-danger');
        } 
        else if (s === 'Deposited' || s === 'Cleared') {
            if (s === 'Deposited') {
                frm.add_custom_button('Mark as Cleared', () => {
                    if (!frm.doc.custom_clearance_date) {
                        frappe.msgprint(__("Please enter the <b>Clearance Date</b> first."));
                        return;
                    }
                    frm.set_value('status', 'Cleared');
                    frm.save();
                }).addClass('btn-success');
            }

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
        if (!frm.doc.party || !frm.doc.amount) {
            frappe.msgprint(__("Please select a <b>Party</b> and enter an <b>Amount</b> first."));
            return;
        }

        frappe.call({
            method: "pdc_cheque_management.pdc_banking_automation.api.fetch_outstanding_invoices",
            args: {
                party_type: frm.doc.party_type,
                party: frm.doc.party,
                company: frm.doc.company,
                amount: frm.doc.amount,
                currency: frm.doc.currency
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    frm.clear_table("custom_invoices");
                    r.message.forEach(d => {
                        let row = frm.add_child("custom_invoices");
                        row.reference_doctype = d.reference_doctype;
                        row.reference_name = d.reference_name;
                        row.outstanding_amount = d.outstanding_amount;
                        row.allocated_amount = d.allocated_amount;
                    });
                    frm.refresh_field("custom_invoices");
                    frappe.show_alert({message: __("Invoices fetched and allocated."), indicator: 'green'});
                } else {
                    frappe.msgprint(__("No outstanding invoices found for this party."));
                }
            }
        });
    }
});