// Copyright (c) 2025, dms developers and contributors
// For license information, please see license.txt

frappe.query_reports["Pipeline Quotation Report"] = {
	filters: [
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Int",
			reqd: 1,
			default: new Date().getFullYear(),
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				"",
				"1", "2", "3", "4", "5", "6",
				"7", "8", "9", "10", "11", "12",
			],
			default: (new Date().getMonth() + 1).toString(),
			reqd: 1,
		},
		{
			fieldname: "product_manager",
			label: __("Product Manager"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "territory",
			label: __("Territory"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "show_summary",
			label: __("Show Summary Only"),
			fieldtype: "Check",
			default: 0,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		if (column.fieldname === "status_indicator") {
			let color = "#999";
			let background = "#f0f0f0";
			console.log("Formatting:", value);
			switch (value) {
				case "Achieved":
					color = "#0c5aa0";
					background = "#cfe9f3";
					break;
				case "Partially Achieved" || "On Track":
					color = "#856404";
					background = "#fff3cd";
					break;
				case "Lost":
					color = "#721c24";
					background = "#f8d7da";
					break;
				case "Over Achieved" || "Exceeded":
					color = "#155724";
					background = "#d4edda";
					break;

				case "Not Achieved":
					color = "#383d41";
					background = "#e2e3e5";
					break;
				case "Planned":
					color = "#f03333ff";
					background = "#ffe6e0";
					break;
				case "Below Target":
					color = "#ff5733";
					background = "#ffe6e0";
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
		};
		return default_formatter(value, row, column, data);
	}
};
