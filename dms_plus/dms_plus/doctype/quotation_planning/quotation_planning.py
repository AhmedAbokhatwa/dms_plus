# Copyright (c) 2025, dms_plus developers and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import formatdate


class QuotationPlanning(Document):
	pass



def generate_monthly_plan(doc, method):
    # month = السنة والشهر من تاريخ عرض السعر
    month = int(frappe.utils.formatdate(doc.transaction_date, "MM"))
    year = int(frappe.utils.formatdate(doc.transaction_date, "YYYY"))
    frappe.db.delete("Quotation Monthly Plan", {"quotation": doc.name})
    for item in doc.items:
        frappe.db.delete("Quotation Monthly Plan", {
            "quotation": doc.name,
            "quotation_item": item.item_code
        })

        frappe.get_doc({
            "doctype": "Quotation Monthly Plan",
            "quotation": doc.name,
            "customer": doc.customer,
            "quotation_item": item.item_code,
            "month": month,
            "year": year,
            "planned_amount": item.amount,
            "actual_amount": 0,
            "product_manager": doc.custom_product_manager,  # أو doc.sales_person لو عندك حقل
            "company": doc.company,
            "sales_persons": doc.owner,
            "territory": doc.territory
        }).insert(ignore_permissions=True)

def update_actual_amount_from_sales_order(doc, method):
    try:
        for item in doc.items:
            quotation_name = item.prevdoc_docname

            quotation_monthly_plan = frappe.db.get_value(
                "Quotation Monthly Plan",
                {"quotation": quotation_name, "quotation_item": item.item_code},
                "name"
            )

            if quotation_monthly_plan:
                plan = frappe.get_doc("Quotation Monthly Plan", quotation_monthly_plan)
                plan.actual_amount += item.amount
                plan.sales_persons = ", ".join(get_sales_persons(doc.name))
                plan.save(ignore_permissions=True)

                update_monthly_plan_status(quotation_monthly_plan)

                frappe.db.commit()

    except Exception as e:
        frappe.log_error(f"Erroe: {str(e)}", "Update Actual Amount Error")

def update_monthly_plan_status(quotation_monthly_plan_name):
    """
    تحديث حالة Quotation Monthly Plan بناءً على planned_amount و actual_amount
    """
    plan = frappe.get_doc("Quotation Monthly Plan", quotation_monthly_plan_name)

    planned = plan.planned_amount or 0
    actual = plan.actual_amount or 0

    if actual == 0:
         plan.status = "Planned"
    elif actual < planned:
        plan.status = "Partially Achieved"
    elif actual == planned:
        plan.status = "Achieved"
    elif actual > planned:
        plan.status = "Over Achieved"


    plan.save(ignore_permissions=True)
    frappe.db.commit()

def get_sales_persons(sales_order_name) -> list:
    """Fetch all Sales Persons for filter options."""
    sales_persons = frappe.db.get_all("Sales Team", fields=["*"], filters={
        "parenttype": "Sales Order",
        "parent": sales_order_name
    })
    return [sp.sales_person for sp in sales_persons]
