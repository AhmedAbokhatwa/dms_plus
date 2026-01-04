# Copyright (c) 2025, dms developers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from pprint import pprint
def execute(filters: dict | None = None):
    """Main entry point for Pipeline Follow-up Report"""
    columns = get_columns()
    data = get_quotation_data(filters)
    return columns, data

def get_columns() -> list[dict]:
    """Define report columns"""
    return [
        {
            "label": _("Quote State"),
            "fieldname": "quote_state",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Quotation Status"),
            "fieldname": "quotation_status",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("ID"),
            "fieldname": "quotation_name",
            "fieldtype": "Link",
            "options": "Quotation",
            "width": 220
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 250
        },
        {
            "label": _("End User"),
            "fieldname": "enduser",
            "fieldtype": "Link",
            "options": "User",
            "width": 180
        },
        {
            "label": _("Price List"),
            "fieldname": "price_list",
            "fieldtype": "Link",
            "options": "Price List",
            "width": 180
        },
        {
            "label": _("Account Manager"),
            "fieldname": "account_manager",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 180
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 250
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 120
        },
        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Int",
            "width": 80
        },

        {
            "label": _("Rate"),
            "fieldname": "rate",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Net Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Additional Discount Amount"),
            "fieldname": "discount",
            "fieldtype": "Currency",
            "width": 220
        },
        {
            "label":_("Net Rate"),
            "fieldname": "net_rate",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label":_("Net Amount"),
            "fieldname": "net_amount",
            "fieldtype": "Currency",
            "width": 150
        },
          {
            "label": _("Quotation Net Total"),
            "fieldname": "quotation_net_total",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Warehouse"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Warehouse",
            "width": 120
        },
        {
            "label": _("Sales Order Qty"),
            "fieldname": "ordered_qty",
            "fieldtype": "Int",
            "width": 150
        },
    ]

def get_quotation_data(filters: dict | None = None) -> list:
    """Fetch Quotations and their related Sales Orders"""
    filters = filters or {}
    where_conditions = []
    params = {}

    if  filters.get("quote_state"):
        where_conditions.append("q.workflow_state = %(quote_state)s")
        params["quote_state"] = filters.get("quote_state")

    if filters.get("quotation_name"):
        where_conditions.append("q.name = %(quotation_name)s")
        params["quotation_name"] = filters.get("quotation_name")

    if filters.get("quotation_status"):
        where_conditions.append("q.status = %(quotation_status)s")
        params["quotation_status"] = filters.get("quotation_status")

    if filters.get("from_date"):
        where_conditions.append("q.transaction_date >= %(from_date)s")
        params["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        where_conditions.append("q.transaction_date <= %(to_date)s")
        params["to_date"] = filters.get("to_date")

    if filters.get("item"):
        where_conditions.append("qi.item_code = %(item)s")
        params["item"] = filters.get("item")

    if filters.get("item_group"):
        where_conditions.append("qi.item_group = %(item_group)s")
        params["item_group"] = filters.get("item_group")

    if filters.get("customer_name"):
        where_conditions.append("q.customer_name = %(customer_name)s")
        params["customer_name"] = filters.get("customer_name")

    if filters.get("warehouse"):
        where_conditions.append("qi.warehouse = %(warehouse)s")
        params["warehouse"] = filters.get("warehouse")

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

    print("where_clause", where_clause)
    query = f"""
        SELECT
            q.workflow_state as quote_state,
            q.status as quotation_status,
            q.transaction_date,
            q.name as quotation_name,
            q.customer_name,
            q.enduser,
            q.selling_price_list as price_list,
            q.account_manager,
            qi.item_code,
            qi.item_group,
            qi.qty,
            qi.amount,
            qi.rate,
            qi.distributed_discount_amount as discount,
            qi.net_rate,
            qi.net_amount,
            q.net_total as quotation_net_total,
            qi.warehouse
        FROM `tabQuotation` q
        LEFT JOIN `tabQuotation Item` qi ON qi.parent = q.name
        WHERE {where_clause}
        ORDER BY q.transaction_date DESC
    """

    try:
        results = frappe.db.sql(query, params, as_dict=True)

        quotation_names = list(
                {row.quotation_name for row in results if row.quotation_name}
            )
        if not quotation_names:
            return results

        if quotation_names:
            ordered_data = frappe.db.sql("""
                    SELECT
                        soi.prevdoc_docname AS quotation_name,
                        soi.item_code,
                        SUM(soi.qty) AS ordered_qty
                    FROM
                        `tabSales Order Item` soi
                    INNER JOIN
                        `tabSales Order` so
                        ON so.name = soi.parent
                    WHERE
                        so.docstatus = 1
                        AND soi.prevdoc_docname IN %(quotation_names)s
                    GROUP BY
                        soi.prevdoc_docname,
                        soi.item_code
                """, {
                    "quotation_names": tuple(quotation_names)
                }, as_dict=True)
            ordered_map = {
                (row.quotation_name, row.item_code): row.ordered_qty
                for row in ordered_data
            }

            for row in results:
                row.ordered_qty = ordered_map.get((row.quotation_name, row.item_code), 0)

                if not hasattr(get_quotation_data, 'last_quotation'):
                    get_quotation_data.last_quotation = None
                if row.quotation_name != get_quotation_data.last_quotation:
                    get_quotation_data.last_quotation = row.quotation_name
                else:
                    row.quotation_net_total = None

        return results
    except Exception as e:
        frappe.msgprint(f"Error fetching data: {str(e)}")
        return []


# Test Case
# SAL-QTN-2025-00026 have twot items Item-0001 qty 10 and Item-0002 qty 5
# create three sales order
#  first sales order Item-0001 qty 2 Done
#  second sales order Item-0001 qty 3 not Done
#  third sales order Item-0002 qty 3 not Done
