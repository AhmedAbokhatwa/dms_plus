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
