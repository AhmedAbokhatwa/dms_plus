# Copyright (c) 2025, dms developers and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from datetime import datetime


def execute(filters: dict | None = None):
    """Return columns and data for the report.
    """
    columns = get_columns()
    data = get_data_hierarchical(filters)
    main_chart = get_chart_data(data)


    return columns, data, None, main_chart

def get_columns() -> list[dict]:
    """Return columns for the report."""
    return [
        {"label": _("Quotation Planning"), "fieldname": "qp_name", "fieldtype": "Link", "options": "Quotation Planning", "width": 180},
        {"label": _("Period"), "fieldname": "period", "fieldtype": "Date", "width": 120},
        {"label": _("Month"), "fieldname": "month", "fieldtype": "Int", "width": 70},
        {"label": _("Year"), "fieldname": "year", "fieldtype": "Int", "width": 70},
        {"label": _("Product Manager"), "fieldname": "product_manager", "fieldtype": "Link", "options": "User", "width": 180},

        {"label": _("Planned Amount"), "fieldname": "planned_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Planned Quotations"), "fieldname": "planned_quotations", "fieldtype": "Int", "width": 140},


        {"label": _("Actual Amount"), "fieldname": "actual_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Actual Quotations"), "fieldname": "actual_quotations", "fieldtype": "Int", "width": 140},
        {"label": _("qmp Planned Amount"), "fieldname": "qmp_planned_amount", "fieldtype": "Currency", "width": 140},

        {"label": _("Variance $"), "fieldname": "variance_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Achievement %"), "fieldname": "achievement_pct", "fieldtype": "Percent", "width": 120},
        {"label": _("Status"), "fieldname": "status_indicator", "fieldtype": "Data", "width": 120},


        {"label": _("QMP Name"), "fieldname": "qmp_name", "fieldtype": "Link", "options": "Quotation Monthly Plan", "width": 180},
        {"label": _("Quotation"), "fieldname": "quotation_name", "fieldtype": "Link", "options": "Quotation", "width": 220},

    ]


def get_data(filters=None):
    """جلب البيانات المجمعة على مستوى شهري"""

    data = []
    plans = frappe.db.sql("""
        SELECT
            qp.name As qp_name,
            qp.year,
            qp.month,
            qp.product_manager,
            qp.territory,
            SUM(qp.planned_amount) AS planned_amount,
            COUNT(*) AS planned_quotations
        FROM `tabQuotation Planning` qp
        GROUP BY qp.year, qp.month, qp.product_manager, qp.territory
        ORDER BY qp.year DESC, qp.month DESC
    """, as_dict=1)


    for plan in plans:
        year = plan.year
        month = plan.month
        pm = plan.product_manager
        planned_amt = flt(plan.planned_amount)
        planned_count = plan.planned_quotations

        actuals = frappe.db.sql("""
            SELECT
                COUNT(DISTINCT qmp.name) AS qmp_count,
                COUNT(DISTINCT qmp.quotation) AS actual_quotations,
                SUM(qmp.actual_amount) AS actual_amount,
                GROUP_CONCAT(DISTINCT qmp.status) AS statuses
            FROM `tabQuotation Monthly Plan` qmp
            WHERE qmp.year = %s
            AND qmp.month = %s
            AND qmp.product_manager = %s
            AND qmp.docstatus != 2
        """, (year, month, pm), as_dict=1)

        actual = actuals[0] if actuals else {}
        actual_amt = flt(actual.get('actual_amount') or 0)
        actual_count = flt(actual.get('actual_quotations') or 0)
        qmp_count = actual.get('qmp_count') or 0
        statuses = actual.get('statuses') or ''


        variance = actual_amt - planned_amt
        achievement_pct = (actual_amt / planned_amt * 100) if planned_amt > 0 else 0
        avg_amount = (actual_amt / actual_count) if actual_count > 0 else 0

        if achievement_pct >= 100:
            status = "✅ Exceeded"
            status_color = "green"
        elif achievement_pct >= 80:
            status = "⚠️ On Track"
            status_color = "orange"
        else:
            status = "❌ Below Target"
            status_color = "red"

        period_date = f"{year}-{str(month).zfill(2)}-01"

        row = {
            "qp_name": plan.qp_name,

            "period": period_date,
            "month": month,
            "year": year,
            "product_manager": pm,
            "planned_amount": planned_amt,
            "planned_quotations": planned_count,
            "actual_amount": actual_amt,
            "actual_quotations": int(actual_count),
            "variance_amount": variance,
            "achievement_pct": round(achievement_pct, 2),
            "status_indicator": status,
            "qmp_count": qmp_count,
            "avg_amount": avg_amount,
        }

        data.append(row)

    return data


def get_summary_data(filters=None):
    """
    دالة مساعدة لحساب ملخص الأداء الكلي
    يمكن استخدامها في Dashboard
    """

    summary = frappe.db.sql("""
        SELECT
            COUNT(DISTINCT qp.name) as total_plans,
            SUM(qp.planned_amount) as total_planned,
            SUM(qmp.actual_amount) as total_actual,
            COUNT(DISTINCT qmp.quotation) as total_quotations
        FROM `tabQuotation Planning` qp
        LEFT JOIN `tabQuotation Monthly Plan` qmp
            ON qp.month = qmp.month
            AND qp.year = qmp.year
            AND qp.product_manager = qmp.product_manager
        WHERE qp.docstatus = 1
    """, as_dict=1)

    if summary:
        s = summary[0]
        total_planned = flt(s.total_planned or 0)
        total_actual = flt(s.total_actual or 0)

        return {
            "total_plans": s.total_plans,
            "total_planned": total_planned,
            "total_actual": total_actual,
            "total_quotations": s.total_quotations,
            "overall_achievement": (total_actual / total_planned * 100) if total_planned > 0 else 0,
            "variance": total_actual - total_planned
        }

    return {}



def get_chart_data(data):
    """
    chart will work Only For Parent Quotation Planning Where (indent=0)
    """

    if not data:
        return None
    print("Data for chart",data)
    parent_rows = [row for row in data if row.get('indent') == 0]
    if not parent_rows:
        return None

    labels = []
    monthly_data = {}

    for row in parent_rows:
        month = row.get('month')
        if month not in monthly_data:
            monthly_data[month] = {
                'planned': 0,
                'actual': 0,
                'achievement': 0,
                'count': 0
            }

        monthly_data[month]['planned'] += row.get('planned_amount', 0)
        monthly_data[month]['actual'] += row.get('actual_amount', 0)
        monthly_data[month]['count'] += 1

    for month in monthly_data:
        planned = monthly_data[month]['planned']
        actual = monthly_data[month]['actual']

        if planned > 0:
            achievement = (actual / planned) * 100
        else:
            achievement = 0

        monthly_data[month]['achievement'] = round(achievement, 2)


    labels = sorted(monthly_data.keys())
    planned_values = [monthly_data[m]['planned'] for m in labels]
    actual_values = [monthly_data[m]['actual'] for m in labels]
    achievement_values = [monthly_data[m]['achievement'] for m in labels]

    datasets =  [
    	{
    		"name": "Planned Amount",
    		"type": "bar",
    		"values": planned_values,
    		"backgroundColor": "#3b82f6",
    		"borderColor": "#1e40af"
    	},
    	{
    		"name": "Actual Amount",
    		"type": "bar",
    		"values": actual_values,
    		"backgroundColor": "#10b981",
    		"borderColor": "#047857"
    	},
    	{
    		"name": "Achievement %",
    		"type": "line",
    		"values": achievement_values,
    		"borderColor": "#f59e0b",
    		"borderWidth": 2,
    		"fill": False,
    		"yAxisID": "y1"
    	}
    ]


    chart_data = {
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "type": "bar",
        "options": {
            "responsive": True,
            "maintainAspectRatio": True,
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                },
                "title": {
                    "display": True,
                    "text": "Quotation Pipeline - Monthly Achievement"
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True
                },
                "y1": {
                    "type": "linear",
                    "display": True,
                    "position": "right",
                    "beginAtZero": True,
                    "max": 150,
                    "title": {
                        "display": True,
                        "text": "Achievement %"
                    }
                }
            }
        }
        }

    print("Chart data",chart_data)
    return chart_data

def get_status_breakdown_chart(data):
    """
    رسم بياني لتوزيع الحالات
    """

    if not data:
        return None

    status_count = {}
    for row in data:
        status = row.get('qmp_status', 'Unknown')
        status_count[status] = status_count.get(status, 0) + 1

    chart_data = {
        "data": {
            "labels": list(status_count.keys()),
            "datasets": [
                {
                    "name": "Count",
                    "data": list(status_count.values()),
                    "backgroundColor": [
                        "#10b981",  # Active - Green
                        "#3b82f6",  # Converted - Blue
                        "#ef4444",  # Lost - Red
                        "#f59e0b"   # On Hold - Yellow
                    ]
                }
            ]
        },
        "type": "doughnut",
        "options": {
            "responsive": True,
            "plugins": {
                "legend": {
                    "position": "bottom"
                },
                "title": {
                    "display": True,
                    "text": "Quotation Status Distribution"
                }
            }
        }
    }

    return chart_data

def get_data_hierarchical(filters=None):
    """جلب البيانات بصيغة hierarchical (parent-child)"""

    data = []
    plans = frappe.db.sql("""
        SELECT
            qp.name AS qp_name,
            qp.year,
            qp.month,
            qp.product_manager,
            qp.territory,
            SUM(qp.planned_amount) AS planned_amount,
            COUNT(*) AS planned_quotations
        FROM `tabQuotation Planning` qp
        GROUP BY qp.year, qp.month, qp.product_manager, qp.territory
        ORDER BY qp.year DESC, qp.month DESC
    """, as_dict=1)

    for plan in plans:
        year = plan.year
        month = plan.month
        pm = plan.product_manager
        planned_amt = flt(plan.planned_amount)
        planned_count = plan.planned_quotations

        actuals = frappe.db.sql("""
            SELECT
                COUNT(DISTINCT qmp.quotation) AS actual_quotations,
                SUM(qmp.actual_amount) AS actual_amount
            FROM `tabQuotation Monthly Plan` qmp
            WHERE qmp.year = %s
            AND qmp.month = %s
            AND qmp.product_manager = %s
            AND qmp.docstatus != 2
        """, (year, month, pm), as_dict=1)
        actual = actuals[0] if actuals else {}
        actual_amt = flt(actual.get('actual_amount') or 0)
        actual_count = flt(actual.get('actual_quotations') or 0)


        variance = actual_amt - planned_amt
        achievement_pct = (actual_amt / planned_amt * 100) if planned_amt > 0 else 0


        if achievement_pct >= 100:
            status = "Exceeded"
        elif achievement_pct >= 80:
            status = "On Track"
        else:
            status = "Below Target"

        period_date = f"{year}-{str(month).zfill(2)}-01"

        parent_row = {
            "qp_name": plan.qp_name,
            "period": period_date,
            "month": month,
            "year": year,
            "product_manager": pm,

            "planned_amount": planned_amt,
            "planned_quotations": planned_count,

            "actual_amount": actual_amt,
            "actual_quotations": int(actual_count),

            "variance_amount": variance,
            "achievement_pct": round(achievement_pct, 2),
            "status_indicator": status,

            "indent": 0
        }

        data.append(parent_row)


        child_records = frappe.db.sql("""
            SELECT
                qmp.name AS qmp_name,
                qmp.quotation AS quotation_name,
                qmp.actual_amount,
                qmp.planned_amount,
                qmp.status

            FROM `tabQuotation Monthly Plan` qmp
            WHERE qmp.year = %s
            AND qmp.month = %s
            AND qmp.product_manager = %s
            AND qmp.docstatus != 2
            ORDER BY qmp.name
        """, (year, month, pm), as_dict=1)

        print("\n\nchild_records fetched:", child_records)

        for child in child_records:
            child_row = {
                "qp_name": None,
                "period": None,
                "month": None,
                "year": None,
                "product_manager": None,

                "planned_amount": None,
                "planned_quotations": None,

                "actual_amount": flt(child.get('actual_amount') or 0),
                "qmp_planned_amount": flt(child.get('planned_amount') or 0),
                "actual_quotations": None,

                "variance_amount": None,
                "achievement_pct": None,
                "status_indicator": child.get('status'),

                "qmp_name": child.qmp_name,
                "quotation_name": child.quotation_name,


                "indent": 1,
                "parent": plan.qp_name
            }

            data.append(child_row)

    return data
