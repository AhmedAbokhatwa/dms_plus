import frappe
from frappe import _
from frappe.model.document import Document
from dms_plus.crm_permissions.utils import get_team_hierarchy

def get_permission_query_conditions(user=None):

    NETWORK_ROLES = {
        "Sales Master Manager - Network",
        "Sales Manager - Network",
        "Sales Coordinator - Network DEPT",
        "Senior Sales - Network DEPT",
        "Junior Sales - Network DEPT",
    }

    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    if user != "Administrator" and "CEO" not in roles:

        is_network_user = any(role in NETWORK_ROLES for role in roles)

        if not is_network_user:
            return """
                `tabCustomer`.owner NOT IN (
                    select hr.parent
                    from `tabHas Role` hr
                    where hr.role in ({roles})
                    and hr.parenttype = "User"
                )
            """.format(
                roles=", ".join(frappe.db.escape(r) for r in NETWORK_ROLES)
            )

    if (
        user == "Administrator"
        or "CEO" in roles
    ):
        return "1=1"

    # View All Customers - Network DEPT
    if ("Sales Coordinator - Network DEPT" in roles
        or "Sales Manager - Network" in roles
        or "Sales Master Manager - Network" in roles):

        team_members = get_team_hierarchy(user)
        if not team_members:
            return "1=0"
        members = " ,".join(
            frappe.db.escape(member) for member in team_members
            )
        return f"`tabCustomer`.owner IN ({members})"

    # Junior/Senior Sales - Network DEPT
    is_junior = "Junior Sales - Network DEPT" in roles
    is_senior = "Senior Sales - Network DEPT" in roles

    if is_junior:
        try:
            employee = frappe.get_doc("Employee", {"user_id": user})
            junior_sales_person = frappe.get_doc(
                    "Sales Person",
                    {"employee": employee.name}
                )
            query = f"""
                  (
                    exists (
                        select 1
                        from `tabSales Team` st
                        where st.parenttype = 'Customer'
                        and st.parent = `tabCustomer`.name
                        and st.sales_person = {frappe.db.escape(junior_sales_person.name)}
                    )
                    OR `tabCustomer`.owner = {frappe.db.escape(user)}
                )
            """
            return query

        except:
            frappe.throw(
                _("Sales Person record not found for employee {0}").format(user),
                frappe.PermissionError
            )
            return "1=0"

    if is_senior:
        try:

            senior_employee = frappe.get_doc("Employee", {"user_id": user})
            senior_sales_person = frappe.get_doc(
                "Sales Person",
                {"employee": senior_employee.name}
            )

            junior_employees = frappe.get_all(
                "Employee",
                filters={"reports_to": senior_employee.name},
                pluck="name"
            )

            # Convert Employees To Sales Persons
            sales_persons_list = [senior_sales_person.name]  # Add Senior itself

            for emp in junior_employees:
                try:
                    sp = frappe.get_doc("Sales Person", {"employee": emp})
                    sales_persons_list.append(sp.name)
                except:
                    frappe.msgprint(_("Sales Person record not found for employee {0}").format(emp))
                    pass

            if not sales_persons_list:
                return "1=0"  # False condition

            users_sql = ", ".join([frappe.db.escape(sp) for sp in sales_persons_list])

            query = f"""
                exists (
                    select 1 from `tabSales Team` st
                    where st.parenttype='Customer'
                      and st.parent=`tabCustomer`.name
                      and st.sales_person in ({users_sql})
                )
                OR `tabCustomer`.owner = {frappe.db.escape(user)}
            """
            return query

        except Exception as e:
            frappe.throw(
                _("Employee or Sales Person record not found for {0}").format(user),
                frappe.PermissionError
            )
            return "1=0"

    return "1=1"

def customer_sales_permission(doc, ptype, user):
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)

    if user == "Administrator" or any(
        role in roles
        for role in ["CEO", "Sales Manager - Network", "Sales Master Manager - Network"]
    ):
        return True

    # Junior/Senior Sales in Network DEPT
    if ("Junior Sales - Network DEPT" in roles) or \
   ("Senior Sales - Network DEPT" in roles):
        if doc.is_new():
            return True
        else:

            if doc.owner == user:
                if ptype == "read":
                    return True
                else:
                    #  can not edit
                    return False

            employee = frappe.get_doc("Employee", {"user_id": user})
            sales_person = frappe.get_doc("Sales Person", {"employee": employee.name})
            allowed = frappe.db.exists(
                "Sales Team",
                {"parenttype": "Customer", "parent": doc.name, "sales_person": sales_person.name}
            )
            if allowed:
                if ptype == "read":
                    return True
                else:
                    #  can not edit
                    return True

@frappe.whitelist()
def check_item_permission(item_code):
    user = frappe.session.user

    if not item_code:
        return {"allowed": True}

    roles = frappe.get_roles(user)

    if "Junior Sales - Network DEPT" in roles:
        item_group = frappe.db.get_value("Item", item_code, "item_group")

        if item_group == "Professional Services":
            return {
                "allowed": False,
                "item_group": item_group,
                "reason": "Junior Sales users are not allowed to add items from this group"
            }

    return {"allowed": True}





