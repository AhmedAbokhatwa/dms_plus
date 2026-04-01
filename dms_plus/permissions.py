import frappe

def get_scope_condition(user, doctype):
    if frappe.has_permission(doctype, "view", user=user):
        return ""

    if frappe.has_permission(doctype, "view_company", user=user):
        company = frappe.db.get_value("Employee", {"user_id": user}, "company")
        return f"`tab{doctype}`.company = {frappe.db.escape(company)}"

    return f"`tab{doctype}`.owner = {frappe.db.escape(user)}"
