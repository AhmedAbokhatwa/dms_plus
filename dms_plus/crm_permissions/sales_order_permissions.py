import frappe
from frappe import _


def get_permission_query_conditions(user=None):
    """
        Sales Order View Permission Check
    """

    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    print(f"User: {user} & Roles: {roles}")

    # ===== ADMIN & TOP ROLES =====
    top_roles = ["CEO", "Sales Manager", "Product Manager", "Sales Coordinator"]
    if user == "Administrator" or any(role in roles for role in top_roles):
        return None

    # ===== JUNIOR SALES =====
    if "Junior Sales" in roles and "Senior Sales" not in roles:
        return get_junior_sales_query(user)

    # ===== SENIOR SALES =====
    if "Senior Sales" in roles:
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
