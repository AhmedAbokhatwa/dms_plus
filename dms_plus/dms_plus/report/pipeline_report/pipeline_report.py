# # Copyright (c) 2025, dms_plus developers and contributors
# # For license information, please see license.txt
import frappe
from frappe import _

def execute(filters: dict | None = None):
    """Main entry point for Pipeline Report"""
    columns = get_columns()
    data = get_quotation_data(filters)
    report_summary = generate_pipeline_summary(data)

    return columns, data, None, None, report_summary

def get_columns() -> list[dict]:
    """Define report columns"""
    return [
        {
            "label": _("Quotation"),
            "fieldname": "quotation_name",
            "fieldtype": "Link",
            "options": "Quotation",
            "width": 200
        },
        {
            "label": _("Customer"),
            "fieldname": "party_name",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 150
        },
        {
            "label": _("Product Manager"),
            "fieldname": "product_manager",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Order Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 200
        },
        {
            "label": _("Delivery Date"),
            "fieldname": "delivery_date",
            "fieldtype": "Date",
            "width": 200
        },
        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 180
        },
        {
            "label": _("Quotation Status"),
            "fieldname": "quotation_status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Related Sales Order"),
            "fieldname": "related_sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 150
        },
        {
            "label": _("SO Status"),
            "fieldname": "so_status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("% Delivered"),
            "fieldname": "per_delivered",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("% Billed"),
            "fieldname": "per_billed",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Pipeline Status"),
            "fieldname": "pipeline_status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Territory"),
            "fieldname": "warehouse",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 120
        },
        {
            "label": _("Sales Person"),
            "fieldname": "sales_person",
            "fieldtype": "Data",
            "width": 150
        }
    ]

def build_filters(filters: dict) -> tuple[str, dict]:
    """Build SQL WHERE conditions based on filters"""
    where_conditions = []
    params = {}

    print("\nfilters.get quotation_status",filters.get("quotation_status"))
    if filters.get("quotation_status"):
        quotation_status = filters.get("quotation_status")
        where_conditions.append("q.status = %(quotation_status)s")
        params["quotation_status"] = filters.get("quotation_status")
    if filters.get("sales_order_status"):
        where_conditions.append("so.status = %(so_status)s")
        params["so_status"] = filters.get("sales_order_status")
    if filters.get("item_group"):
        where_conditions.append("qi.item_group = %(item_group)s")
        params["item_group"] = filters.get("item_group")
    if filters.get("item"):
        where_conditions.append("qi.item_code = %(item)s")
        params["item"] = filters.get("item")
    if filters.get("product_manager"):
        where_conditions.append("q.owner = %(product_manager)s")
        params["product_manager"] = filters.get("product_manager")
    if filters.get("customer"):
        where_conditions.append("q.party_name = %(customer)s")
        params["customer"] = filters.get("customer")
    if filters.get("territory"):
        where_conditions.append("q.territory = %(territory)s")
        params["territory"] = filters.get("territory")
    if filters.get("from_date"):
        where_conditions.append("q.transaction_date >= %(from_date)s")
        params["from_date"] = filters.get("from_date")
    if filters.get("to_date"):
        where_conditions.append("q.transaction_date <= %(to_date)s")
        params["to_date"] = filters.get("to_date")

    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    return where_clause, params

def get_quotation_data(filters: dict) -> list:
    """Fetch Quotations and their related Sales Orders"""
    filters = filters or {}
    print("\nfilters in get_quotation_data",filters )
    # Build WHERE conditions for Quotations
    where_clause, params = build_filters(filters)
    print("\nwhere_clause",where_clause )
    print("\nparams",params )
    query = f"""
        SELECT DISTINCT
            q.name as quotation_name,
            q.party_name,
            qi.item_code,
            qi.item_group,
            q.owner as product_manager,
            q.transaction_date,
            q.valid_till as delivery_date,
            qi.qty,
            qi.amount,
            qi.warehouse,
            q.status as quotation_status,
            q.territory,
            qt.sales_person
        FROM `tabQuotation` q
        LEFT JOIN `tabQuotation Item` qi ON qi.parent = q.name
        LEFT JOIN `tabSales Team` qt ON qt.parent = q.name
        WHERE {where_clause}
        ORDER BY q.transaction_date DESC
    """

    try:
        results = frappe.db.sql(query, params, as_dict=True)

        # أضف Related Sales Order والـ Pipeline Status لكل Quotation
        for row in results:
            # print("\n\nrow before SO fetch",row )
            sales_order_data = get_sales_order_for_quotation(row.get('quotation_name'), row.get('party_name'))
            # print("sales_order_data",sales_order_data )
            row['related_sales_order'] = sales_order_data.get('sales_order_name', 'No SO Found')
            row['so_status'] = sales_order_data.get('status', 'No SO Found')
            row['sales_person'] = ', '.join(get_sales_persons(row['related_sales_order'])) if row['related_sales_order'] != 'No SO Found' else ''
            row['per_delivered'] = sales_order_data.get('per_delivered', 0)
            row['per_billed'] = sales_order_data.get('per_billed', 0)

            if sales_order_data.get('sales_order_name'):
                row['pipeline_status'] = calculate_pipeline_status(sales_order_data)
            else:
                row['pipeline_status'] = 'Not Converted'
        # print("\n\ntotal quotation",results )
        # print("where_clause",where_clause )
        return results
    except Exception as e:
        frappe.msgprint(f"Error fetching data: {str(e)}")
        return []


def get_sales_order_for_quotation(quotation_name: str, customer:str) -> dict:
    """
    Get the latest Sales Order related to a Quotation
    based on the prevdoc_docname field in Sales Order Item.
    """
    try:
        sales_orders = frappe.db.sql(
            """
            SELECT DISTINCT
                soi.parent AS sales_order_name,
                so.status,
                so.per_delivered,
                so.per_billed,
                so.transaction_date
            FROM `tabSales Order Item` soi
            LEFT JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE soi.prevdoc_docname = %s
            And so.customer = %s
            AND so.status != 'Cancelled'
            ORDER BY so.transaction_date DESC
            LIMIT 1
            """,
            (quotation_name, customer),
            as_dict=True
        )

        return sales_orders[0] if sales_orders else {}

    except Exception as e:
        frappe.log_error(f"Error getting sales order: {str(e)}")
        return {}



def calculate_pipeline_status(row: dict) -> str:
    """
    calculate the pipeline status based on delivery and billing percentages.
    status can be:
    - Cancelled
    - Draft
    - Completed
    - To Bill
    - To Deliver
    - To Deliver and Bill
    """
    status = row.get('status', 'Draft')
    per_delivered = row.get('per_delivered', 0) or 0
    per_billed = row.get('per_billed', 0) or 0

    # تحويل النسب إلى أرقام عادية
    if isinstance(per_delivered, str):
        per_delivered = float(per_delivered.replace('%', '') or 0)
    if isinstance(per_billed, str):
        per_billed = float(per_billed.replace('%', '') or 0)

    # منطق تحديد الحالة
    if status == "Cancelled":
        return "Cancelled"
    elif status == "Draft":
        return "Draft"
    elif per_delivered == 100 and per_billed == 100:
        return "Completed"
    elif per_delivered == 100 and per_billed < 100:
        return "To Bill"
    elif per_delivered > 0 and per_delivered < 100 and per_billed == 0:
        return "To Deliver"
    elif per_delivered > 0 and per_delivered < 100 and per_billed > 0:
        return "To Deliver and Bill"
    elif per_delivered == 0 and per_billed == 0:
        return "To Deliver and Bill"
    else:
        return "To Deliver and Bill"

def get_sales_persons(sales_order_name) -> list:
    """Fetch all Sales Persons for filter options."""
    sales_persons = frappe.db.get_all("Sales Team", fields=["*"], filters={
        "parenttype": "Sales Order",
        "parent": sales_order_name
    })
    return [sp.sales_person for sp in sales_persons]

def generate_pipeline_summary(data: list) -> list:
    """Generate report_summary (shown above report table)"""
    summary = {}
    for row in data:
        status = row.get('pipeline_status', 'Unknown')
        summary[status] = summary.get(status, 0) + 1

    report_summary = []
    for status, count in summary.items():
        report_summary.append({
            "value": count,
            "label": status,
            "datatype": "Int"
        })

    return report_summary
