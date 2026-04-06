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


JUNIOR_ROLES = {
    "Junior Sales - ALVOIP",
    "Junior Sales - DMS",
    "Junior Sales - AVTECH",
}

BLOCKED_ITEM_GROUP = "Professional Service"

def validate_professional_service(doc, method):
    # Check if current user has any junior role
    user_roles = set(frappe.get_roles(frappe.session.user))
    if not user_roles & JUNIOR_ROLES:
        return  # Not a junior, skip

    # Check items in the sales order
    for row in doc.items:
        if row.item_group == BLOCKED_ITEM_GROUP:
            frappe.throw(
                f"Row {row.idx}: Your Role is {', '.join(user_roles & JUNIOR_ROLES)} are not allowed to add items from "
                f"the <b>{BLOCKED_ITEM_GROUP}</b> group.",
                title="Permission Denied"
            )
