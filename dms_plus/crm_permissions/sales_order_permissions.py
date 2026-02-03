import frappe
from frappe import _
from dms_plus.crm_permissions.utils import get_team_hierarchy, get_network_user_query

def get_permission_query_conditions(user=None):
    """
        Sales Order View Permission Check
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
                `tabSales Order`.owner NOT IN (
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
    # ===== TOP Managers =====
    manager_roles = {"Sales Manager - Network", "Product MGR - Network", "Sales Master Manager - Network"}
    if manager_roles.intersection(roles):

        team_members = get_team_hierarchy(user)
        if not team_members:
            return "1=0"


        members = " ,".join(
            frappe.db.escape(member) for member in team_members
            )
        print("members: ",members)
        return f"`tabSales Order`.owner IN ({members})"

    is_junior = "Junior Sales - Network DEPT" in roles
    is_senior = "Senior Sales - Network DEPT" in roles
    is_coordinator = "Sales Coordinator - Network DEPT" in roles
    # ===== JUNIOR SALES =====
    if is_junior or is_senior or is_coordinator:
        return get_network_user_query(user, doctype="Sales Order", include_account_manager=True)
