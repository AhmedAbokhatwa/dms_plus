import frappe
from frappe import _
from frappe.model.document import Document
def get_permission_query_conditions(user=None):

    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    if (
        user == "Administrator"
        or "Sales Coordinator" in roles and "Sales User - Network DEPT" in roles
        or "Product Manager" in roles and "Sales Manager - Network" in roles
        or "Sales Manager" in roles and "Sales Manager - Network" in roles
    ):
        return None  # View All Customers

    if "Junior Sales - Network DEPT" in roles:
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

    if "Senior Sales" in roles and "Sales User - Network DEPT" in roles:
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
            frappe.logger().error(
                f"Error in get_permission_query_conditions for Senior Sales {user}: {str(e)}"
            )
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





