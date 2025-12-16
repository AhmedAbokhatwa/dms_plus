import frappe
from frappe import _
from frappe.utils import flt, getdate
from copy import deepcopy

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)

    return columns, data, None, chart

def get_columns():
    return [
        {
            "label": _("Sales Invoice"),
            "fieldname": "invoice_name",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 200
        },
        {
            "label": _("Sales Person"),
            "fieldname": "sales_person",
            "fieldtype": "Link",
            "options": "Sales Person",
            "width": 150
        },
        {
            "label": _("Transaction Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Sales Order"),
            "fieldname": "sales_order_name",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 200
        },
        {
            "label": _("Customer"),
            "fieldname": "customer_name",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "label": _("Item"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 120
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
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Price"),
            "fieldname": "price",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Total"),
            "fieldname": "total",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Buying Amount"),
            "fieldname": "buying_amount",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Landing Costs"),
            "fieldname": "landing_costs",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Gross Profit"),
            "fieldname": "gross_profit",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "label": _("Gross Profit %"),
            "fieldname": "gross_profit_percent",
            "fieldtype": "Percent",
            "width": 130
        }
    ]

def build_filters(filters):
    conditions = ""
    values = []
    if filters.get('sales_person'):
        conditions += f" AND sp.name = %s"
        values.append(filters.get('sales_person'))

    if filters.get('customer_name'):
        conditions += f" AND si.customer = %s"
        values.append(filters.get('customer_name'))

    if filters.get('sales_order_name'):
        conditions += f" AND sii.sales_order = %s"
        values.append(filters.get('sales_order_name'))

    if filters.get('item_code'):
        conditions += f" AND sii.item_code = %s"
        values.append(filters.get('item_code'))

    if filters.get('from_date'):
        conditions += f" AND si.posting_date >= %s"
        values.append(filters.get('from_date'))

    if filters.get('to_date'):
        conditions += f" AND si.posting_date <= %s"
        values.append(filters.get('to_date'))

    return conditions , values

def get_data(filters):
    if not filters:
        filters = {}

    conditions, values = build_filters(filters)

    query = f"""
        SELECT
            si.name as invoice_name,
            IFNULL(sii.sales_order, '') as sales_order_name,
            si.posting_date as transaction_date,
            si.customer_name,
            si.customer,
            IFNULL(sp.name, '') as sales_person,
            sii.item_code,
            item.item_group,
            sii.qty,
            sii.rate as price,
            sii.amount as total,
            sii.warehouse,
            si.update_stock
        FROM
            `tabSales Invoice Item` sii
        INNER JOIN
            `tabSales Invoice` si ON sii.parent = si.name
        LEFT JOIN
            `tabItem` item ON sii.item_code = item.name
        LEFT JOIN
            `tabSales Team` st ON si.name = st.parent AND st.parenttype = 'Sales Invoice'
        LEFT JOIN
            `tabSales Person` sp ON st.sales_person = sp.name
        WHERE
            si.docstatus = 1
            {conditions}
        ORDER BY
            si.posting_date DESC, si.customer_name
    """

    invoices = frappe.db.sql(query, values, as_dict=True)

    data = []
    for invoice in invoices:
        row = deepcopy(invoice)

        # Calculate buying amount using Stock Ledger Entry
        buying_amount = get_buying_amount(
            invoice.get('item_code'),
            invoice.get('qty'),
            invoice.get('transaction_date'),
            invoice.get('warehouse'),
            invoice.get('update_stock')
        )

        # Get landing costs
        landing_costs = get_landing_costs(
            invoice.get('item_code'),
            invoice.get('qty'),
            invoice.get('transaction_date')
        )

        row['buying_amount'] = buying_amount
        row['landing_costs'] = landing_costs
        row['gross_profit'] = flt(invoice.get('total')) - flt(buying_amount) - flt(landing_costs)

        if invoice.get('total') and invoice.get('total') != 0:
            row['gross_profit_percent'] = (row['gross_profit'] / flt(invoice.get('total'))) * 100
        else:
            row['gross_profit_percent'] = 0

        data.append(row)

    return data


def get_stock_ledger_entries(item_code, warehouse, posting_date):
    """
    Fetch Stock Ledger Entries for given item and warehouse up to a posting date.
    Sorted descending (latest first).
    """
    if not item_code or not warehouse:
        return []

    sle = frappe.db.sql("""
        SELECT
            valuation_rate,
            actual_qty,
            posting_date,
            posting_datetime,
            warehouse
        FROM
            `tabStock Ledger Entry`
        WHERE
            item_code = %s
            AND warehouse = %s
            AND posting_date <= %s
        ORDER BY
            posting_datetime DESC, posting_date DESC, creation DESC
    """, (item_code, warehouse, posting_date), as_dict=True)

    return sle or []

def get_buying_amount(item_code, qty, posting_date, warehouse, update_stock):
    """
    Calculate Buying Amount using Stock Ledger Entries.
    """
    if not item_code or not qty:
        return 0
    sle = get_stock_ledger_entries(item_code, warehouse, posting_date)

    if update_stock and sle:

        latest_rate = flt(sle[0].get('valuation_rate', 0))
        return flt(qty) * latest_rate
    if not update_stock and sle:
        valuation_rate = sum([flt(entry.get('valuation_rate', 0)) for entry in sle]) / len(sle) if sle else 0
        return flt(qty) * valuation_rate

    return 0

def get_landing_costs(item_code, qty, posting_date):
    """
    Get landing costs from Purchase Receipt/Invoice Item
    Distributed on per unit basis
    """
    if not item_code or not qty:
        return 0

    # Get average landing cost per unit
    landing_cost = frappe.db.sql("""
        SELECT
            SUM(pri.landed_cost_voucher_amount) as total_landing_cost,
            SUM(pri.qty) as total_qty
        FROM
            `tabPurchase Receipt Item` pri
        LEFT JOIN
            `tabPurchase Receipt` pr ON pri.parent = pr.name
        WHERE
            pri.item_code = %s
            AND pr.posting_date <= %s
            AND pr.docstatus = 1
    """, (item_code, posting_date), as_dict=True)

    if landing_cost and landing_cost[0].get('total_qty'):
        cost_per_unit = flt(landing_cost[0].get('total_landing_cost', 0)) / flt(landing_cost[0].get('total_qty'))
        return flt(qty) * cost_per_unit

    return 0

def get_chart_data(data):
    """
    Generate chart data for Gross Profit visualization
    """
    if not data:
        return None

    labels = []
    gross_profit_data = []

    for row in data:
        labels.append(row.get('customer_name', 'Unknown'))
        gross_profit_data.append(row.get('gross_profit', 0))

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Gross Profit",
                    "values": gross_profit_data
                }
            ]
        },
        "type": "bar",
        "colors": ["#2ecc71"],
        "options": {
            "height": 100,
            "width": 400
        }
    }
