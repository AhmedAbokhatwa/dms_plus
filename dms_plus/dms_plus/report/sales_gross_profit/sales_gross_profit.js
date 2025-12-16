// Copyright (c) 2025, dms_plus developers and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Gross Profit"] = {
	"filters": [
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person",
			"width": "100px"
		},
		{
			"fieldname": "customer_name",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": "100px"
		},
		{
			"fieldname": "sales_order_name",
			"label": __("Sales Order"),
			"fieldtype": "Link",
			"options": "Sales Order",
			"width": "100px"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width": "100px"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80px"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80px"
		},
		{
			"fieldname": "group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": "\nSales Person\nCustomer",
			"width": "80px"
		}
	],

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname == "gross_profit") {
			let profit = data[column.fieldname];
			if (profit < 0) {
				value = "<span style='color: red; font-weight: bold;'>" + value + "</span>";
			} else {
				value = "<span style='color: green; font-weight: bold;'>" + value + "</span>";
			}
		}

		if (column.fieldname == "gross_profit_percent") {
			let percent = data[column.fieldname];
			if (percent < 0) {
				value = "<span style='color: red; font-weight: bold;'>" + value + "</span>";
			} else if (percent >= 0 && percent < 20) {
				value = "<span style='color: orange; font-weight: bold;'>" + value + "</span>";
			} else {
				value = "<span style='color: green; font-weight: bold;'>" + value + "</span>";
			}
		}

		return value;
	},

	"after_datatable_render": function (datatable) {
		// Add custom styling and interactions
		setup_report_interactions(datatable);
	},

	"onload": function (report) {
		// Add custom buttons and actions
		report.page.add_inner_button(__("Refresh"), function () {
			report.refresh();
		});

		report.page.add_inner_button(__("Export to Excel"), function () {
			export_to_excel(report);
		});
	}
};

function setup_report_interactions(datatable) {
	// Highlight rows based on profit margin
	datatable.datamanager.data.forEach(row => {
		if (row.gross_profit < 0) {
			row._row_index = row._row_index || datatable.datamanager.data.indexOf(row);
		}
	});
}

function export_to_excel(report) {
	let data = report.data;
	let columns = report.columns;

	if (!data || data.length === 0) {
		frappe.msgprint(__("No data to export"));
		return;
	}

	// Create CSV content
	let csv_content = "data:text/csv;charset=utf-8,";

	// Add headers
	let headers = columns.map(col => col.label).join(",");
	csv_content += headers + "\n";

	// Add data rows
	data.forEach(row => {
		let row_data = columns.map(col => {
			let value = row[col.fieldname] || "";
			// Escape quotes in CSV
			if (typeof value === 'string' && value.includes(',')) {
				value = '"' + value.replace(/"/g, '""') + '"';
			}
			return value;
		}).join(",");
		csv_content += row_data + "\n";
	});

	// Create download link
	let encoded_uri = encodeURI(csv_content);
	let link = document.createElement("a");
	link.setAttribute("href", encoded_uri);
	link.setAttribute("download", "sales_gross_profit_" + frappe.datetime.get_datetime_as_string().split(" ")[0] + ".csv");
	link.click();

	frappe.msgprint(__("Report exported successfully"));
}

// Grouping functionality
frappe.query_reports["Sales Gross Profit"].apply_grouping = function (data, group_by) {
	if (!group_by) return data;

	let grouped = {};

	data.forEach(row => {
		let key = row[group_by] || "Unassigned";
		if (!grouped[key]) {
			grouped[key] = [];
		}
		grouped[key].push(row);
	});

	let grouped_data = [];

	for (let group_key in grouped) {
		// Add group header
		grouped_data.push({
			"group_header": group_key,
			"is_group_header": true
		});

		// Add group items
		grouped_data = grouped_data.concat(grouped[group_key]);

		// Add group summary
		let group_summary = calculate_group_summary(grouped[group_key]);
		grouped_data.push(group_summary);
	}

	return grouped_data;
};

function calculate_group_summary(group_data) {
	let total_qty = 0;
	let total_selling = 0;
	let total_buying = 0;
	let total_landing_costs = 0;
	let total_gross_profit = 0;

	group_data.forEach(row => {
		total_qty += parseFloat(row.qty) || 0;
		total_selling += parseFloat(row.total) || 0;
		total_buying += parseFloat(row.buying_amount) || 0;
		total_landing_costs += parseFloat(row.landing_costs) || 0;
		total_gross_profit += parseFloat(row.gross_profit) || 0;
	});

	let gross_profit_percent = total_selling ? (total_gross_profit / total_selling) * 100 : 0;

	return {
		"sales_person": "--- Group Total ---",
		"customer_name": "",
		"sales_order_name": "",
		"qty": total_qty,
		"total": total_selling,
		"buying_amount": total_buying,
		"landing_costs": total_landing_costs,
		"gross_profit": total_gross_profit,
		"gross_profit_percent": gross_profit_percent.toFixed(2),
		"is_group_summary": true
	};
}

// Hook to handle group by filter change
frappe.query_reports["Sales Gross Profit"].on_filter_change = function (report) {
	let group_by = frappe.query_report.get_filter_value("group_by");

	if (group_by) {
		let grouped_data = frappe.query_reports["Sales Gross Profit"].apply_grouping(
			report.data,
			group_by
		);

		// Re-render the datatable with grouped data
		report.datatable.rowmanager.rows = [];
		report.datatable.datamanager.data = grouped_data;
		report.datatable.render();
	}
};
