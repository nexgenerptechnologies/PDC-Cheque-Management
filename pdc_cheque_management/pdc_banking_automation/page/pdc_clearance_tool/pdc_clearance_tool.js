frappe.pages['pdc-clearance-tool'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'PDC Clearance Tool',
		single_column: true
	});

	page.set_primary_action('Upload Bank Statement', () => {
		new frappe.ui.FileUploader({
			method: 'pdc_cheque_management.pdc_banking_automation.api.process_bank_statement',
			on_success: (file) => {
				render_results(page, file.message);
			}
		});
	});

	let render_results = (page, results) => {
		let pdc_html = results.filter(r => r.match_type === 'PDC').map(r => `
			<tr>
				<td>${r.party}</td>
				<td><a href="/app/payment-entry/${r.payment_entry}">${r.payment_entry || ''}</a></td>
				<td>${r.cheque_no}</td>
				<td>${format_currency(r.amount)}</td>
				<td><span class="label label-success">${r.status}</span></td>
				<td>
					<button class="btn btn-xs btn-primary btn-clear" data-id="${r.pdc_id}">Mark as Cleared</button>
				</td>
			</tr>
		`).join('');

		let neft_html = results.filter(r => r.match_type === 'NEFT').map(r => `
			<tr>
				<td>${r.cheque_no} (Type)</td>
				<td>${r.reason}</td>
				<td>${format_currency(r.amount)}</td>
				<td><span class="label label-warning">${r.status}</span></td>
				<td>
					<button class="btn btn-xs btn-default btn-draft" data-amt="${r.amount}" data-desc="${r.reason}" data-type="${r.cheque_no}">Create Draft</button>
				</td>
			</tr>
		`).join('');

		let html = `
			<ul class="nav nav-tabs" style="margin-top:20px;">
				<li class="active"><a data-toggle="tab" href="#pdc-matches">PDC Matches (${results.filter(r => r.match_type === 'PDC').length})</a></li>
				<li><a data-toggle="tab" href="#neft-matches">NEFT Found (${results.filter(r => r.match_type === 'NEFT').length})</a></li>
			</ul>
			<div class="tab-content" style="padding-top:15px;">
				<div id="pdc-matches" class="tab-pane fade in active">
					<table class="table table-hover border">
						<thead><tr class="bg-light"><th>Party</th><th>Payment Entry</th><th>Cheque No</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead>
						<tbody>${pdc_html || '<tr><td colspan="6" class="text-center">No PDC matches found</td></tr>'}</tbody>
					</table>
				</div>
				<div id="neft-matches" class="tab-pane fade">
					<table class="table table-hover border">
						<thead><tr class="bg-light"><th>Cr/Dr</th><th>Description</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead>
						<tbody>${neft_html || '<tr><td colspan="5" class="text-center">No NEFT transactions found</td></tr>'}</tbody>
					</table>
				</div>
			</div>
		`;
		
		$(page.body).find(".results-area").remove();
		$('<div class="results-area">' + html + '</div>').appendTo(page.body);

		$(page.body).find(".btn-clear").on("click", function() {
			let id = $(this).data("id");
			frappe.call({
				method: 'pdc_cheque_management.pdc_banking_automation.api.clear_pdc',
				args: { pdc_id: id, clearance_date: frappe.datetime.get_today() },
				callback: (r) => {
					if (r.message.status === 'success') {
						$(this).closest("tr").fadeOut();
						frappe.show_alert(r.message.message);
					}
				}
			});
		});

		$(page.body).find(".btn-draft").on("click", function() {
			let amt = $(this).data("amt");
			let desc = $(this).data("desc");
			let type = $(this).data("type");
			let ptype = type === 'CR' ? 'Receive' : 'Pay';
			frappe.new_doc("Payment Entry", {
				payment_type: ptype,
				paid_amount: amt,
				received_amount: amt,
				remarks: desc,
				reference_no: desc.substring(0, 49)
			});
		});
	};
}