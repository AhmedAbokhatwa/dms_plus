import frappe
from frappe import _

def get_permission_query_conditions(user=None):
    """
        Quotation View Permission Check
    """

    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    print(f"User: {user} & Roles: {roles}")

    # ===== ADMIN & CEO =====
    top_roles = ["Administrator", "CEO"]
    if any(role in roles for role in top_roles):
        return ""

    # ==== TOP Managers =====
    manager_roles = {"Sales Manager", "Product Manager", "Sales Master Manager"}
    if manager_roles.intersection(roles):

        team_members = get_team_hierarchy(user)
        if not team_members:
            return "1=0"


        members = " ,".join(
            frappe.db.escape(member) for member in team_members
            )
        print("members: ",members)
        return f"`tabQuotation`.owner IN ({members})"

    # ===== JUNIOR SALES =====
    if "Junior Sales" in roles and "Senior Sales" not in roles:
        return get_junior_sales_query(user)

    # ===== SENIOR SALES =====
    if "Senior Sales" in roles:
        return get_senior_sales_query_only_his_quote(user)

    # ===== DEFAULT (Owner only) =====
    return f"`tabQuotation`.owner={frappe.db.escape(user)}"


def get_junior_sales_query(user):

    try:

        if not frappe.db.exists("Employee", {"user_id": user}):
            return f"`tabQuotation`.owner={frappe.db.escape(user)}"

        employee = frappe.get_doc("Employee", {"user_id": user})
        print(f"Employee: {employee.name}")

        sales_person = None
        try:
            sales_person = frappe.get_doc("Sales Person", {"employee": employee.name})
        except:
            print(f" No Sales Person found for {employee.name}")

        if not sales_person:
            return f"`tabQuotation`.owner={frappe.db.escape(user)}"

        query = f"""
        (
            `tabQuotation`.owner={frappe.db.escape(user)}
            or `tabQuotation`.account_manager={frappe.db.escape(sales_person.name)}
        )
        """
        return query

    except Exception as e:
        frappe.logger().error(f"Error in get_junior_sales_query for {user}: {str(e)}")
        return f"`tabQuotation`.owner={frappe.db.escape(user)}"

def get_senior_sales_query_only_his_quote(user):
    """
    Return a SQL permission condition for a Senior Sales user to see **only their own Quotations**.
    """
    try:
        # Fallback if user is not linked to an Employee
        if not frappe.db.exists("Employee", {"user_id": user}):
            return f"`tabQuotation`.owner={frappe.db.escape(user)}"

        senior_employee = frappe.get_doc("Employee", {"user_id": user})
        employee_sql = frappe.db.escape(senior_employee.name)
        # Return only quotations where the user is the owner
        query = f"`tabQuotation`.owner={frappe.db.escape(user)} OR `tabQuotation`.account_manager = {employee_sql}"

        return query

    except Exception as e:
        frappe.logger().error(f"Error in get_senior_sales_query_only_his_quote for {user}: {str(e)}")
        # fallback to owner only
        return f"`tabQuotation`.owner={frappe.db.escape(user)}"


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

def has_permission(doc, ptype=None, user=None):
    """
    Prevent opening quotation directly via URL if user is not allowed
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

    allowed_roles = {"Sales Manager", "Product Manager"}
    allowed_ptypes = ("read", "write","create", "submit", "cancel")

    has_allowed_role = bool(allowed_roles.intersection(roles))
    if ptype in allowed_ptypes and is_team_member and has_allowed_role:

        return True

    if not doc.owner:
        return check_quotation_owner(doc, user)
    # ===== SENIOR SALES =====
    if "Senior Sales" in roles:
        # check account_manager safely
        if hasattr(doc, "account_manager") and doc.account_manager:
            employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
            if employee and doc.account_manager == employee:
                return True

    # ===== JUNIOR SALES =====
    if "Junior Sales" in roles:
        if hasattr(doc, "account_manager") and doc.account_manager:
            employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
            if employee and doc.account_manager == employee:
                return True

    # this deny everything else
    return False

#  3
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

    # Allowed Roles to Cancel, Amend
    # allowed_roles = ["Sales Coordinator", "Product Manager", "Sales Manager"]

    # if not any(role in roles for role in allowed_roles):
    #     return False

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

