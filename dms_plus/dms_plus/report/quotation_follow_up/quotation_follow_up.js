// Copyright (c) 2025, dms developers and contributors
// For license information, please see license.txt

    frappe.query_reports["Quotation Follow-up"] = {
        "filters": [
            {
                "fieldname": "quote_state",
                "label": "Quote State",
                "fieldtype": "Data",
                "width": 120
            },
            {
                "fieldname": "quotation_name",
                "label": "Quotation Name",
                "fieldtype": "Link",
                "options": "Quotation",
                "width": 220
            },
            {
                "fieldname": "quotation_status",
                "label": "Quotation Status",
                "fieldtype": "Select",
                "options": "",
                "default": "",
                "width": 120
            },
            {
                "fieldname": "from_date",
                "label": "From Date",
                "fieldtype": "Date",
                "width": 100
            },
            {
                "fieldname": "to_date",
                "label": "To Date",
                "fieldtype": "Date",
                "width": 100
            },
            {
                "fieldname": "item",
                "label": "Item",
                "fieldtype": "Link",
                "options": "Item",
                "width": 120
            },
            {
                "fieldname": "item_group",
                "label": "Item Group",
                "fieldtype": "Link",
                "options": "Item Group",
                "width": 120
            },
            {
                "fieldname": "customer_name",
                "label": "Customer",
                "fieldtype": "Link",
                "options": "Customer",
                "width": 240
            },
            {
                "fieldname": "warehouse",
                "label": "Warehouse",
                "fieldtype": "Link",
                "options": "Warehouse",
                "width": 150
            },
            {
                "fieldname": "account_manager",
                "label": "Account Manager",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 180
            },
        ],
     onload: function (report) {
        frappe.model.with_doctype("Quotation", function () {
            const meta = frappe.get_meta("Quotation");
            const status_field = meta.fields.find(
                f => f.fieldname === "status"
            );

            if (status_field) {
                const options = ["", ...status_field.options.split("\n")];

                report.set_filter_value("quotation_status", "");
                report.get_filter("quotation_status").df.options = options.join("\n");
                report.get_filter("quotation_status").refresh();
            }
        });
    },
};
