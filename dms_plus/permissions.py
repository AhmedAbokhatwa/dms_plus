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


JUNIOR_ROLES = {"Junior Sales"}
SENIOR_ROLES = {"Senior Sales"}
TOP_ROLES = {"Sales Master Manager", "Sales Manager", "Product Manager", "CEO"}
BLOCKED_ITEM_GROUP = "Professional Service"


def validate_professional_service(doc, method):
    user_roles = set(frappe.get_roles(frappe.session.user))

    if not user_roles & JUNIOR_ROLES:
        return

    for row in doc.items:
        if row.item_group == BLOCKED_ITEM_GROUP:
            frappe.throw(
                f"Row {row.idx}: دورك ({', '.join(user_roles & JUNIOR_ROLES)}) "
                f"لا يسمح بإضافة منتجات من مجموعة <b>{BLOCKED_ITEM_GROUP}</b>.",
                title="Permission Denied"
            )


# def check_approval_limit(doc, method):
#     if doc.workflow_state != "Draft":
#         return

#     total = doc.base_grand_total or 0
#     roles = set(frappe.get_roles(frappe.session.user))
#     print(f"User: {frappe.session.user}, Roles: {roles}, Total: {total}")
#     print(f"Is Top Role: {bool(roles & TOP_ROLES)}, Is Senior: {bool(roles & SENIOR_ROLES)}, Is Junior: {bool(roles & JUNIOR_ROLES)}")

#     if roles & TOP_ROLES:
#         return  # no limit

#     if roles & JUNIOR_ROLES:
#         limit = 75000
#     elif roles & SENIOR_ROLES:
#         limit = 150000
#     else:
#         return  # role غير معروف
#     print(f"Approval limit for user: {limit}")
#     print(f"Total: {total}, Limit: {limit}")
#     if total > limit:
#         frappe.db.set_value("Quotation", doc.name, "workflow_state", "Pending Approval")
#         frappe.db.set_value("Quotation", doc.name, "docstatus", 0)
#         frappe.db.commit()
#         frappe.msgprint(
#             f"قيمة العرض <b>{total:,.0f} SR</b> تتجاوز حد صلاحيتك ({limit:,.0f} SR).<br><br>"
#             "تم إحالته تلقائياً للمدير للموافقة.",
#             title="تجاوز حد الصلاحية"
#         )

# @frappe.whitelist()
# def check_approval_limit_api(total, doc_name):
#     total = float(total or 0)  # ✅ FIX
#     roles = set(frappe.get_roles(frappe.session.user))
#     print(f"API Check - User: {frappe.session.user}, Total: {total}, Doc Name: {doc_name}")

#     if roles & TOP_ROLES:
#         return {"allowed": True}

#     if roles & JUNIOR_ROLES:
#         limit = 75000
#     elif roles & SENIOR_ROLES:
#         limit = 150000
#     else:
#         return {"allowed": True}

#     if total > limit:
#         frappe.db.set_value("Quotation", doc_name, "workflow_state", "Pending Approval")
#         frappe.db.set_value("Quotation", doc_name, "docstatus", 0)
#         return {
#             "allowed": False,
#             "limit": limit,
#             "total": total
#         }

#     return {"allowed": True}
