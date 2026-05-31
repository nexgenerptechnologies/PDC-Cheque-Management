frappe.pages['pdc-clearance-tool'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'PDC Clearance Tool',
		single_column: true
	});

	page.body.html('<div id="pdc-filters"></div><div id="pdc-results" style="margin-top: 20px;"></div>');

	let filter_group = new frappe.ui.FieldGroup({
		parent: page.body.find('#pdc-filters'),
		fields: [
			{ fieldname: 'from_date', fieldtype: 'Date', label: 'From Date' },
			{ fieldname: 'to_date', fieldtype: 'Date', label: 'To Date' },
			{ fieldtype: 'Column Break' },
			{ fieldname: 'status', fieldtype: 'Select', label: 'Status', options: '\nDraft\nReceived\nDeposited\nIssued\nCleared\nCancelled\nBounced', default: 'Deposited' },
			{ fieldtype: 'Column Break' },
			{ fieldname: 'party', fieldtype: 'Dynamic Link', label: 'Party', options: 'party_type' },
			{ fieldname: 'party_type', fieldtype: 'Select', label: 'Party Type', options: '\nCustomer\nSupplier' }
		]
	});
	filter_group.make();

	page.set_primary_action('Get Cheques', () => {
		let filters = filter_group.get_values();
		frappe.call({
			method: 'pdc_cheque_management.pdc_banking_automation.api.get_pdc_cheques',
			args: { filters: filters },
			callback: (r) => {
				render_results(page, r.message || []);
			}
		});
	});

	page.add_inner_button('Bulk Update', () => {
		let selected = get_selected_cheques(page);
		if (!selected.length) {
			frappe.msgprint('Please select at least one cheque to update.');
			return;
		}
		
		let d = new frappe.ui.Dialog({
			title: 'Bulk Update Cheques',
			fields: [
				{ fieldname: 'target_status', fieldtype: 'Select', label: 'New Status', options: 'Cleared\nDeposited\nBounced', reqd: 1 },
				{ fieldname: 'action_date', fieldtype: 'Date', label: 'Clearance / Bounce Date', reqd: 1, default: frappe.datetime.get_today() }
			],
			primary_action_label: 'Update',
			primary_action: (values) => {
				frappe.call({
					method: 'pdc_cheque_management.pdc_banking_automation.api.bulk_update_cheques',
					args: {
						cheque_names: selected,
						target_status: values.target_status,
						action_date: values.action_date
					},
					freeze: true,
					freeze_message: 'Updating Cheques...',
					callback: (r) => {
						d.hide();
						if (r.message && r.message.status === 'success') {
							frappe.show_alert({message: 'Cheques successfully updated!', indicator: 'green'});
							page.get_primary_action_btn().click();
						}
					}
				});
			}
		});
		d.show();
	});

	let render_results = (page, results) => {
		let html = `
			<table class="table table-hover table-bordered">
				<thead>
					<tr class="bg-light">
						<th style="width: 40px;"><input type="checkbox" id="select-all-pdc"></th>
						<th>Cheque No</th>
						<th>Date</th>
						<th>Party</th>
						<th>Amount</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
					${results.map(r => `
						<tr>
							<td><input type="checkbox" class="pdc-checkbox" data-name="${r.name}"></td>
							<td><a href="/app/pdc-cheque/${r.name}">${r.cheque_no || r.name}</a></td>
							<td>${frappe.datetime.str_to_user(r.cheque_date)}</td>
							<td>${r.party || ''}</td>
							<td>${format_currency(r.amount, r.currency)}</td>
							<td><span class="indicator ${r.status === 'Cleared' ? 'green' : (r.status === 'Bounced' ? 'red' : 'orange')}">${r.status}</span></td>
						</tr>
					`).join('')}
					${results.length === 0 ? '<tr><td colspan="6" class="text-center text-muted">No cheques found</td></tr>' : ''}
				</tbody>
			</table>
		`;
		
		page.body.find('#pdc-results').html(html);

		page.body.find('#select-all-pdc').on('change', function() {
			let checked = $(this).prop('checked');
			page.body.find('.pdc-checkbox').prop('checked', checked);
		});
	};

	let get_selected_cheques = (page) => {
		let selected = [];
		page.body.find('.pdc-checkbox:checked').each(function() {
			selected.push($(this).data('name'));
		});
		return selected;
	};
};