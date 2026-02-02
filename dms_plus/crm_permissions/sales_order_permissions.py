import frappe
from frappe import _
from dms_plus.crm_permissions.utils import get_team_hierarchy

def get_permission_query_conditions(user=None):
    """
        Sales Order View Permission Check
    """

    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    print(f"User: {user} & Roles: {roles}")

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
    # ===== JUNIOR SALES =====
    if is_junior and not is_senior:
        return get_junior_sales_query(user)

    # ===== SENIOR SALES =====
    if is_senior and not is_junior:
        return get_senior_sales_query_only_his_orders(user)

    # ===== DEFAULT (Owner only) =====
    return f"`tabSales Order`.owner = {frappe.db.escape(user)}"


def get_junior_sales_query(user):
    try:
        if not frappe.db.exists("Employee", {"user_id": user}):
            return f"`tabSales Order`.owner = {frappe.db.escape(user)}"

        employee = frappe.get_doc("Employee", {"user_id": user})
        print(f"Employee: {employee.name}")

        sales_person = None
        try:
            sales_person = frappe.get_doc("Sales Person", {"employee": employee.name})
        except:
            print(f"No Sales Person found for {employee.name}")

        if not sales_person:
            return f"`tabSales Order`.owner = {frappe.db.escape(user)}"

        meta = frappe.get_meta("Sales Order")
        has_account_manager = meta.has_field("account_manager")
        if has_account_manager:
            query = f"""
            (
                `tabSales Order`.owner = {frappe.db.escape(user)}
                OR `tabSales Order`.account_manager = {frappe.db.escape(sales_person.name)}
            )
            """
            return query
        else:
            return f"`tabSales Order`.owner = {frappe.db.escape(user)}"

    except Exception as e:
        frappe.logger().error(f"Error in get_junior_sales_query for {user}: {str(e)}")
        return f"`tabSales Order`.owner = {frappe.db.escape(user)}"


def get_senior_sales_query_only_his_orders(user):
    """
    Senior Sales can see ONLY their own Sales Orders
    """
    try:
        if not frappe.db.exists("Employee", {"user_id": user}):
            return f"`tabSales Order`.owner = {frappe.db.escape(user)}"

        senior_employee = frappe.get_doc("Employee", {"user_id": user})
        employee_sql = frappe.db.escape(senior_employee.name)

        meta = frappe.get_meta("Sales Order")
        has_account_manager = meta.has_field("account_manager")

        if has_account_manager:
            query = f"""
            `tabSales Order`.owner = {frappe.db.escape(user)}
            OR `tabSales Order`.account_manager = {employee_sql}
            """
            return query
        else:
            return f"`tabSales Order`.owner = {frappe.db.escape(user)}"

    except Exception as e:
        frappe.logger().error(
            f"Error in get_senior_sales_query_only_his_orders for {user}: {str(e)}"
        )
        return f"`tabSales Order`.owner = {frappe.db.escape(user)}"
