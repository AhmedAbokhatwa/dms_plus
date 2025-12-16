frappe.ui.form.on('Company', {
	setup(frm) {
	frm.set_query("default_in_transit_warehouse", function () {
			return {
				filters: {
					warehouse_type: "Shipment",
					is_group: 0,
					company: frm.doc.company_name,
				},
			};
		});
	},
})
