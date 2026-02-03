import frappe
from frappe import _
from dms_plus.crm_permissions.utils import get_team_hierarchy, get_network_user_query

def get_permission_query_conditions(user=None):
    """
        Quotation View Permission Check
        if user is Admin or CEO: return all
        if user is Sales Manager/Product MGR/Sales Master Manager:
            return quotations owned by team members
        if user is Senior Sales - Network DEPT:
            return quotations owned by self only
        if user is Junior Sales - Network DEPT:
            return quotations owned by self or where account_manager is self
        if Coordinator:
            return quotations owned by self only or where account_manager is self
        if none of the above, return quotations owned by self only
    """

    NETWORK_ROLES = {
        "Sales Master Manager - Network",
        "Sales Manager - Network",
        "Product MGR - Network",
        "Sales Coordinator - Network DEPT",
        "Senior Sales - Network DEPT",
        "Junior Sales - Network DEPT",
    }

    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    print(f"User: {user} & Roles: {roles}")

    # ===== DEFAULT (Owner only) =====
    if user != "Administrator" and "CEO" not in roles:
        is_network_user = any(role in NETWORK_ROLES for role in roles)

        if not is_network_user:
            return """
                `tabQuotation`.owner NOT IN (
                    select hr.parent
                    from `tabHas Role` hr
                    where hr.role in ({roles})
                    and hr.parenttype = "User"
                )
            """.format(
                roles=", ".join(frappe.db.escape(r) for r in NETWORK_ROLES)
            )

    # ===== ADMIN & CEO =====
    top_roles = ["Administrator", "CEO"]
    if any(role in roles for role in top_roles):
        return ""

    # ==== TOP Managers =====
    manager_roles = {
        "sales Coordinator - Network DEPT",
        "Sales Manager - Network",
        "Product MGR - Network",
        "Sales Master Manager - Network"
        }
    if manager_roles.intersection(roles):

        team_members = get_team_hierarchy(user)
        print("team_members: ",team_members)
        if not team_members:
            return "1=0"


        members = " ,".join(
            frappe.db.escape(member) for member in team_members
            )
        print("members: ",members)
        return f"`tabQuotation`.owner IN ({members})"

    is_junior = "Junior Sales - Network DEPT" in roles
    is_senior = "Senior Sales - Network DEPT" in roles
    is_coordinator = "Sales Coordinator - Network DEPT" in roles

    if is_junior or is_senior or is_coordinator:
        return get_network_user_query(user, doctype="Quotation", include_account_manager=True)

def has_permission(doc, ptype=None, user=None):
    """
    Prevent opening quotation directly via URL if user is not allowed
    -> Check if the user is part of the Quotation owner's team.
    Returns:
        bool: True if the user has permission, False otherwise.
        if user is Admin or CEO: True
        if user is Sales Manager/Product MGR/Sales Master Manager and part of team: True
        if user is Senior Sales - Network DEPT and owner: True
        if user is Junior Sales - Network DEPT and owner or account_manager: True
        else: False
    """
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    print("roles",roles)

    # ===== ADMIN & TOP LEVEL CEO Only=====
    if user == "Administrator" or any(
        role in roles
        for role in ["CEO"]
    ):
        return True

    # ===== OWNER =====
    if doc.owner == user:
        return True

    print(f"========================= validation ==============================")
    is_team_member = check_quotation_owner(doc, user)
    print(f"validate",is_team_member)

    allowed_roles = {
        "Sales Manager - Network",
        "Product MGR - Network",
        "Sales Coordinator - Network DEPT",
        "Sales Master Manager - Network"
        }
    allowed_ptypes = ("read", "write","create", "submit", "cancel")

    has_allowed_role = bool(allowed_roles.intersection(roles))
    if ptype in allowed_ptypes and is_team_member and has_allowed_role:

        return True

    if not doc.owner:
        return check_quotation_owner(doc, user)
    # ===== SENIOR SALES =====
    if "Senior Sales - Network DEPT" in roles:
        # check account_manager safely
        if hasattr(doc, "account_manager") and doc.account_manager:
            employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
            if employee and doc.account_manager == employee:
                return True

    # ===== JUNIOR SALES =====
    if "Junior Sales - Network DEPT" in roles:
        if hasattr(doc, "account_manager") and doc.account_manager:
            employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
            if employee and doc.account_manager == employee:
                return True

    # this deny everything else
    return False

#  3 -> Check if the user is part of the Quotation owner's team.
def check_quotation_owner(doc, user=None):
    """
    -> Check if the user is part of the Quotation owner's team.

    Steps:
        1. Get doc.owner (the owner of the Quotation).
        2. Build the owner's team hierarchy using get_team_hierarchy.
        3. Check if the user is in the team.

    Returns:
        bool: True if the user has permission, False otherwise.
    """
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return True

    roles = frappe.get_roles(user)

    try:
        # 1. Get Document Owner
        quotation_owner = doc.owner
        print(f" Quotation: {doc.name}  Owner: {quotation_owner}")

        # 2. Build Team
        team_members = get_team_hierarchy(quotation_owner)
        print(f"Team Members: {team_members}")

        # 3. Check if User is Part of Team
        if user in team_members:
            return True
        else:
            return False

    except Exception as e:
        error_msg = f"Error in check quotation owner: {str(e)}"
        frappe.logger().error(error_msg)
        return False


