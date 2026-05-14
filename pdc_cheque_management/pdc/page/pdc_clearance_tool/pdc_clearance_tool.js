frappe.pages['pdc-clearance-tool'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'PDC Clearance Tool',
		single_column: true
	});

	page.set_primary_action('Upload Bank Statement', () => {
		new frappe.ui.FileUploader({
			method: 'pdc_cheque_management.pdc.api.process_bank_statement',
			on_success: (file) => {
				render_results(page, file.message);
			}
		});
	});

	let render_results = (page, results) => {
		let html = `
			<table class="table table-hover border">
				<thead>
					<tr class="bg-light">
						<th>Customer</th>
						<th>Payment Entry</th>
						<th>Deposit JE</th>
						<th>Cheque No</th>
						<th>Amount</th>
						<th>Status</th>
						<th>Action</th>
					</tr>
				</thead>
				<tbody>
					${results.map(r => `
						<tr>
							<td>${r.customer}</td>
							<td><a href="/app/payment-entry/${r.payment_entry}">${r.payment_entry || ''}</a></td>
							<td><a href="/app/journal-entry/${r.deposit_journal_entry}">${r.deposit_journal_entry || ''}</a></td>
							<td>${r.cheque_no}</td>
							<td>${format_currency(r.amount)}</td>
							<td><span class="label label-success">${r.status}</span></td>
							<td>
								<button class="btn btn-xs btn-primary btn-clear" data-id="${r.pdc_id}">Mark as Cleared</button>
								<button class="btn btn-xs btn-danger btn-decline" data-id="${r.pdc_id}">Decline</button>
							</td>
						</tr>
					`).join('')}
				</tbody>
			</table>
		`;
		
		$(page.body).find(".results-area").remove();
		$('<div class="results-area" style="margin-top: 20px;">' + html + '</div>').appendTo(page.body);

		$(page.body).find(".btn-clear").on("click", function() {
			let id = $(this).data("id");
			frappe.call({
				method: 'pdc_cheque_management.pdc.api.clear_pdc',
				args: { pdc_id: id, clearance_date: frappe.datetime.get_today() },
				callback: (r) => {
					if (r.message.status === 'success') {
						$(this).closest("tr").fadeOut();
						frappe.show_alert(r.message.message);
					}
				}
			});
		});

		$(page.body).find(".btn-decline").on("click", function() {
			$(this).closest("tr").css("opacity", "0.5");
			frappe.show_alert("Match declined.");
		});
	};
}
