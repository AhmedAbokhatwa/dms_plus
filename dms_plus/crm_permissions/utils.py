import frappe
from frappe import _

def get_team_hierarchy(owner_user):

    try:

        owner_employee = frappe.get_doc("Employee", {"user_id": owner_user})
        owner_emp_name = owner_employee.name
        print(f"Owner Employee: {owner_emp_name}")

        team_users = [owner_user]


        subordinates = get_all_subordinates(owner_emp_name)
        if subordinates:
            team_users.extend(subordinates)

        managers = get_all_managers(owner_emp_name)
        if managers:
            team_users.extend(managers)

        team_users = list(set([u for u in team_users if u]))
        team_users.sort()

        return team_users

    except Exception as e:
        error_msg = f"Error building team hierarchy: {str(e)}"
        frappe.logger().error(error_msg)
        return [owner_user]


def get_all_subordinates(emp_name, visited=None):

    if visited is None:
        visited = set()

    if emp_name in visited:
        return []

    visited.add(emp_name)
    subordinates = []

    try:
        junior_employees = frappe.get_all(
            "Employee",
            filters={"reports_to": emp_name},
            fields=["name", "user_id"]
        )

        for emp in junior_employees:
            if emp.user_id:
                subordinates.append(emp.user_id)
                subordinates.extend(get_all_subordinates(emp.name, visited))
    except Exception as e:
        frappe.logger().error(f"Error getting subordinates for {emp_name}: {str(e)}")

    return subordinates


def get_all_managers(emp_name, visited=None):

    if visited is None:
        visited = set()

    if emp_name in visited:
        return []

    visited.add(emp_name)
    managers = []

    try:
        employee = frappe.get_doc("Employee", emp_name)
        if employee.reports_to:
            manager_emp = frappe.get_doc("Employee", employee.reports_to)
            if manager_emp.user_id:
                managers.append(manager_emp.user_id)

                managers.extend(get_all_managers(employee.reports_to, visited))
    except Exception as e:
        frappe.logger().error(f"Error getting managers for {emp_name}: {str(e)}")

    return managers

def get_network_user_query(user, doctype, include_account_manager):
    """
    Returns SQL query conditions to filter documents where the account manager is in the user's
    or he is the owner. This allows users to see his own documents
    """
    tab = f"`tab{doctype}`"

    try:

        conditions = [f"{tab}.owner={frappe.db.escape(user)}"]
        if not frappe.db.exists("Employee", {"user_id": user}):
            return conditions[0]


        if include_account_manager and frappe.db.has_column(doctype, "account_manager"):
            employee = frappe.get_doc("Employee", {"user_id": user})
            if employee:
                conditions.append(f"{tab}.account_manager={frappe.db.escape(employee.name)}")

        return " OR ".join(conditions)

    except Exception as e:
        frappe.logger().error(f"Error in get_network_user_query for {user}: {str(e)}")
        return f"{tab}.owner={frappe.db.escape(user)}"




def get_senior_sales_query_with_lower_level(user):

    try:
        if not frappe.db.exists("Employee", {"user_id": user}):
            return f"`tabQuotation`.owner={frappe.db.escape(user)}"

        senior_employee = frappe.get_doc("Employee", {"user_id": user})
        sales_person = None

        try:
            sales_person = frappe.get_doc("Sales Person", {"employee": senior_employee.name})
        except:
            frappe.throw(f" No Sales Person found for {senior_employee.name}")

        # احصل على Junior Employees
        junior_employees = frappe.get_all(
            "Employee",
            filters={"reports_to": senior_employee.name},
            fields=["name", "user_id"]
        )

        sales_persons_list = []

        if sales_person:
            sales_persons_list.append(sales_person.employee)


        for emp in junior_employees:
            try:
                sp = frappe.get_doc("Sales Person", {"employee": emp.name})
                sales_persons_list.append(sp.employee)
            except:
                continue

        if not sales_persons_list:
            query = f"`tabQuotation`.owner={frappe.db.escape(user)}"
            return query

        # بناء الـ Query
        sales_persons_sql = ", ".join([frappe.db.escape(sp) for sp in sales_persons_list])

        query = f"""
        (
            `tabQuotation`.owner={frappe.db.escape(user)}
            or `tabQuotation`.account_manager in ({sales_persons_sql})
        )
        """
        return query

    except Exception as e:
        frappe.logger().error(f"Error in get_senior_sales_query for {user}: {str(e)}")
        return f"`tabQuotation`.owner={frappe.db.escape(user)}"
