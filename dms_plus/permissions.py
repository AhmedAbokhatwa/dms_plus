import frappe

# def get_scope_condition(user, doctype):
#     print(f"Checking permissions for user: {user} on doctype: {doctype} read: {frappe.has_permission(doctype, 'read', user=user)}, view: {frappe.has_permission(doctype, 'view', user=user)}, can_view_if_account_manager: {frappe.has_permission(doctype, 'can_view_if_account_manager', user=user)}")
#     if user == "Administrator":
#         return "1=1"
#     if frappe.has_permission(doctype, "can_view_if_account_manager", user=user):
#         if doctype == "Customer":
#             return f"`tab{doctype}`.account_manager = {frappe.db.escape(user)} OR `tabCustomer`.owner = {frappe.db.escape(user)}"

#         if doctype == "Quotation":
#             company = frappe.db.get_value("Employee", {"user_id": user}, "company")
#             return f"`tabQuotation`.owner = {frappe.db.escape(user)}"

#         if doctype == "Sales Order":
#             return f"`tabSales Order`.owner = {frappe.db.escape(user)}"
#     return "1=1"


RESTRICTED_ROLES = {
    "Junior Sales - ALVOIP",
    "Junior Sales - DMS",
    "Junior Sales - AVTECH",
    "Senior Sales - ALVOIP",
    "Senior Sales - DMS",
    "Senior Sales - AVTECH",
}

def is_restricted_user(user):
    user_roles = set(frappe.get_roles(user))
    return bool(user_roles & RESTRICTED_ROLES)

def get_scope_condition(user, doctype):
    if user == "Administrator":
        return "1=1"

    if not is_restricted_user(user):
        return "1=1"

    # Restricted sales user — scope to their own records only
    if doctype == "Customer":
        return (
            f"`tabCustomer`.account_manager = {frappe.db.escape(user)} "
            f"OR `tabCustomer`.owner = {frappe.db.escape(user)}"
        )
    if doctype == "Quotation":
        return f"`tabQuotation`.owner = {frappe.db.escape(user)}"
    if doctype == "Sales Order":
        return f"`tabSales Order`.owner = {frappe.db.escape(user)}"

    return "1=1"
