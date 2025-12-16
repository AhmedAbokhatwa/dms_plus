// Copyright (c) 2025, dms_plus developers and contributors
// For license information, please see license.txt

let statuses = [];
frappe.query_reports["Pipeline Report"] = {
	filters: [
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
			reqd: 0
		},
		{
			fieldname: "quotation_status",
			label: __("Quotation Status"),
			fieldtype: "Select",
			options: [""],
			default: "",
			reqd: 0
		},
		{
			fieldname: "sales_order_status",
			label: __("Sales Order Status"),
			fieldtype: "Select",
			options: [""],
			default: "",
			reqd: 0
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
			reqd: 0
		},
		{
			fieldname: "product_manager",
			label: __("Product Manager"),
			fieldtype: "Link",
			options: "User",
			reqd: 0
		},
		{
			fieldname: "item",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
			reqd: 0
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			reqd: 0
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
			reqd: 0
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -3)
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today()
		}
	],

	onload: function (report) {
		report.page.set_title(__("Sales Pipeline Report"));
		report.trigger_refresh_on_load = true;

		report.page.add_inner_button(__("Export Report"), function () {
			frappe.query_report.export_report("CSV");
		});

		getSalesOrderStatus(report);
		getQuotationStatus(report);
	},

	after_datatable_render: function (datatable_wrapper) {
		$(datatable_wrapper).find('table').addClass('table-striped table-hover');
		statuses = ["Cancelled", "Draft", "To Deliver and Bill", "To Deliver", "To Bill", "Completed"];
		updatePipelineSummary(statuses);
		addReportStyling();

	},

	formatter: function (value, row, column, data, default_formatter) {

		if (column.fieldname === "so_status") {

			let status_color = "badge-secondary";

			switch (value) {
				case "Draft":
					status_color = "badge-info";
					break;
				case "To Deliver and Bill":
					status_color = "badge-warning";
					break;
				case "To Deliver":
					status_color = "badge-primary";
					break;
				case "To Bill":
					status_color = "badge-danger";
					break;
				case "Completed":
					status_color = "badge-success";
					break;
				case "Cancelled":
					status_color = "badge-secondary";
					break;
			}

			return `<span class="badge ${status_color}"
						style="
						padding: 4px 20px;
						border-radius: 5px;
						font-size:10px;
						align-items: center;
						justify-content: center;
						display: flex;">${value}</span>`;
		}
		if (column.fieldname === "pipeline_status" || column.fieldname === "quotation_status") {
			let color = "#999";
			let background = "#f0f0f0";

			switch (value) {
				case "Open":
					color = "#0c5aa0";
					background = "#cfe9f3";
					break;
				case "Draft":
					color = "#0c5aa0";
					background = "#cfe9f3";
					break;
				case "To Deliver and Bill":
					color = "#856404";
					background = "#fff3cd";
					break;
				case "To Deliver":
					color = "#0c5aa0";
					background = "#d1ecf1";
					break;
				case "To Bill":
					color = "#721c24";
					background = "#f8d7da";
					break;
				case "Completed":
					color = "#155724";
					background = "#d4edda";
					break;
				case "Cancelled":
					color = "#383d41";
					background = "#e2e3e5";
					break;
			}

			return `<span
						style="background-color: ${background};
						color: ${color};
						padding: 2px 5px;
						border-radius: 5px;
						font-size:10px;
						align-items: center;
						justify-content: center;
						display: flex;">${value}
					</span>`;
		}
		return default_formatter(value, row, column, data);
	}
};

function getSalesOrderStatus(report) {
	frappe.model.with_doctype("Sales Order", function () {

		let field = frappe.meta.get_docfield("Sales Order", "status", "Sales Order");
		if (field && field.options) {

			let options = field.options.split('\n').filter(opt => opt.trim() !== "");
			options.unshift("");
			let status_filter = report.get_filter('sales_order_status');
			status_filter.df.options = options;
			status_filter.refresh();

		} else {
			console.warn("Couldn't find status field or it has no options");
		}
	});
}

function getQuotationStatus(report) {
	frappe.model.with_doctype("Quotation", function () {

		let field = frappe.meta.get_docfield("Quotation", "status", "Quotation");
		if (field && field.options) {

			let options = field.options.split('\n').filter(opt => opt.trim() !== "");
			options.unshift("");
			let status_filter = report.get_filter('quotation_status');
			status_filter.df.options = options;
			// statuses = options;
			status_filter.refresh();
			return options;
		} else {
			console.warn("Couldn't find status field or it has no options");
		}
	});
}

function build_filters(filters_array) {
	let filters = {};

	if (filters_array && filters_array.length) {
		filters_array.forEach(function (f) {
			if (f.value) {
				filters[f.key] = f.value;
			}
		});
	}

	return filters;
}

async function updatePipelineSummary(statuses_list) {
	$('#pipeline-summary-custom').remove();

	let data = [];
	if (frappe.query_report && frappe.query_report.datatable) {
		data = frappe.query_report.datatable.datamanager.data || [];
	}

	if (!data || data.length === 0 || !statuses_list || statuses_list.length === 0) return;

	const summary = {};
	// Pipeline statuses to summarize
	// Statuses come from the Quotation Status and Sales Order Status filters
	// Example statuses: ["Draft", "Open", "To Deliver", "To Bill", "Completed", "Cancelled"]
	// statuses_list = statuses_list.filter(status => status && status.trim() !== "");

	statuses_list.forEach(status => {
		summary[status] = data.filter(row =>
			row.pipeline_status === status || row.status === status
		).length;
	});

	console.log("✅ cleaned statuses_list:", statuses_list);
	console.log("✅ pipeline summary data:", summary);
	console.log("✅ full data:", data);
	let summary_html = `

		<div id="pipeline-summary-custom" class="frappe-control frappe-card-section"
		 		style="
					margin-bottom: 20px;
					padding: 20px;
					width: 100%;
					border-radius: 8px;
				">
			<div class="form-section">
				<h6 class="section-head" style="margin-bottom: 15px; display: flex; align-items: center; justify-content: center;">
					<i class="fa fa-line-chart" style="margin-right: 8px;"></i>
					<span>Quotation Status Summary</span>
				</h6>
				<div class="form-grid-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
	`;

	statuses_list.forEach(status => {
		const count = summary[status] || 0;
		summary_html += `
			<div style="
				background: rgba(255, 255, 255, 0.15);
				padding: 18px;
				border-radius: 8px;
				text-align: center;
				border: 1px solid rgba(255, 255, 255, 0.3);
				transition: all 0.3s;
			">
				<div style="font-size: 12px; opacity: 0.95; margin-bottom: 10px; letter-spacing: 0.5px; font-weight: 600;">${status}</div>
				<div style="font-size: 32px; font-weight: 900;">${count}</div>
			</div>
		`;
	});

	summary_html += `
			</div>
		</div>
	`;

	const reportResult = $('div.result');
	console.log("✅ Inserting pipeline summary into report...", reportResult.length);
	if (reportResult.length) {
		console.log("✅ Prepending pipeline summary");
		reportResult.prepend(summary_html);
	} else {
		console.log("✅ Prepending pipeline summary 2");
		$('div.frappe-control').last().after(summary_html);
	}
}

function addReportStyling() {
	console.log("Adding custom styles to Pipeline Report...");
	const style = `
		.datatable table thead {
			background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
			color: white;
		}

		.datatable table th {
			color: white;
			font-weight: 700;
			text-transform: uppercase;
			letter-spacing: 0.5px;
		}

		.datatable table tbody tr:hover {
			background: #f5f5f5 !important;
		}
	`;

	if ($('#pipeline-report-styles').length === 0) {
		$('head').append(`<style id="pipeline-report-styles">${style}</style>`);
	}
}

$(document).on('frappe-query-report-ready', function () {
	setTimeout(function () {
		console.log("Updating pipeline summary on report ready...");
		updatePipelineSummary(statuses);
	}, 500);
});

frappe.query_report.refresh_on_filter_change = true;

