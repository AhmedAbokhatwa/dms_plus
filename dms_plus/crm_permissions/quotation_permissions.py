import frappe
from frappe import _
from dms_plus.crm_permissions.utils import get_team_hierarchy

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
        if none of the above, return quotations owned by self only
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
    manager_roles = {"Sales Manager - Network", "Product MGR - Network", "Sales Master Manager - Network"}
    if manager_roles.intersection(roles):

        team_members = get_team_hierarchy(user)
        if not team_members:
            return "1=0"


        members = " ,".join(
            frappe.db.escape(member) for member in team_members
            )
        print("members: ",members)
        return f"`tabQuotation`.owner IN ({members})"

    is_junior = "Junior Sales - Network DEPT" in roles
    is_senior = "Senior Sales - Network DEPT" in roles

    # ===== JUNIOR SALES =====
    if is_junior:
        return get_junior_sales_query(user)

    # ===== SENIOR SALES =====
    if is_senior and not is_junior:
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

    allowed_roles = {"Sales Manager - Network", "Product MGR - Network", "Sales Master Manager - Network"}
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


