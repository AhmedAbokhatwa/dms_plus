import frappe
from frappe import _

def get_permission_query_conditions(user=None):

    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    if (
        user == "Administrator"
        or "Sales Coordinator" in roles
        or "Product Manager" in roles
        or "Sales Manager" in roles
    ):
        return None  # View All Customers

    if "Junior Sales" in roles and "Senior Sales" not in roles:
        try:
            employee = frappe.get_doc("Employee", {"user_id": user})
            junior_sales_person = frappe.get_doc(
                    "Sales Person",
                    {"employee": employee.name}
                )
            query = f"""
                exists (
                    select 1
                    from `tabSales Team` st
                    where st.parenttype='Customer'
                    and st.parent=`tabCustomer`.name
                    and st.sales_person={frappe.db.escape(junior_sales_person.name)}
                ) OR owner = {frappe.db.escape(user)}
            """
            return query
        except:
            frappe.throw(
                _("Sales Person record not found for employee {0}").format(user),
                frappe.PermissionError
            )
            return "1=0"

    if "Senior Sales" in roles:
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
                ) OR owner = {frappe.db.escape(user)}
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

    frappe.throw(
        _("You don't have permission to see Customers Please Connect to Admin"),
        frappe.PermissionError
    )
    return "1=0"

def has_permission(doc, ptype, user):
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    if "Junior Sales" in roles or "Senior Sales" in roles:
        if not doc.flags.is_new and ptype in ("write", "delete"):
        #put ->  if doc.owner != user: to make edit his Customer after Create
            return False
        return None


@frappe.whitelist()
def check_item_permission(item_code):
    user = frappe.session.user

    if not item_code:
        return {"allowed": True}

    roles = frappe.get_roles(user)

    if "Junior Sales" in roles:
        item_group = frappe.db.get_value("Item", item_code, "item_group")

        if item_group == "Professional Services":
            return {
                "allowed": False,
                "item_group": item_group,
                "reason": "Junior Sales users are not allowed to add items from this group"
            }

    return {"allowed": True}





