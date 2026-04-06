import frappe

def after_install():
    create_roles()
    create_ptypes()

def after_uninstall():
    delete_roles()
    delete_ptypes()


def get_roles():
    companies = ["DMS", "ALVOIP", "AVTECH"]
    base_roles = [
        "Sales Master Manager",
        "Sales Manager",
        "Product Manager",
        "Sales Coordinator",
        "Senior Sales",
        "Junior Sales",
        # i have Stock Manager and Stock User
        # "Warehouse Manager",
        # "Warehouse User",
        # Marketing Manager

    ]

    roles = [f"{role} - {company}" for company in companies for role in base_roles]

    # extra roles
    roles += [
        "Logistic User",
        "Technician",
        "Technical Engineer",
    ]

    return roles

def create_roles(roles=None):
    roles = roles or get_roles()
    for role in list(set(roles)):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1,
                "is_custom": 1
            }).insert(ignore_permissions=True)

    frappe.db.commit()

def delete_roles(roles=None):
    roles = roles or get_roles()
    for role in list(set(roles)):
        if frappe.db.exists("Role", role):
            frappe.delete_doc("Role", role, ignore_permissions=True)

    frappe.db.commit()

def create_ptypes():
    """ Create Permission Types For All Documents"""
    doctypes = ["Customer", "Quotation", "Sales Order"]
    for doctype in doctypes:
        for ptype in ["can_view_if_account_manager"]:
            if not frappe.db.exists("Permission Type", {"perm_type": ptype, "doc_type": doctype}):
                frappe.get_doc({
                    "doctype": "Permission Type",
                    "perm_type": ptype,
                    "doc_type": doctype,
                }).insert(ignore_permissions=True)
    frappe.db.commit()

def delete_ptypes():
    """ Delete Permission Types For All Documents"""
    for doctype in frappe.get_all("DocType", filters={"istable": 0}, pluck="name"):
        for ptype in ["can_view_if_account_manager"]:
            if frappe.db.exists("Permission Type", {"perm_type": ptype, "doc_type": doctype}):
                doc = frappe.get_doc("Permission Type", {"perm_type": ptype, "doc_type": doctype})
                doc.delete(ignore_permissions=True)
    frappe.db.commit()

def remove_permission_type(ptype: str):
    """
    Remove a specific permission type from:
    1. Custom DocPerm (first - dependency)
    2. Permission Type
    """

    if not ptype:
        frappe.throw("Permission type is required")

    # هنجمع الـ doctypes اللي فيها الـ ptype
    doctypes = frappe.get_all(
        "Permission Type",
        filters={"perm_type": ptype},
        pluck="doc_type"
    )

    for doctype in doctypes:

        # 1. Delete from Custom DocPerm (IMPORTANT FIRST)
        custom_perms = frappe.get_all(
            "Custom DocPerm",
            filters={
                "parent": doctype,
                "perm_type": ptype
            },
            pluck="name"
        )

        for perm in custom_perms:
            frappe.delete_doc(
                "Custom DocPerm",
                perm,
                ignore_permissions=True
            )

        # 2. Delete from Permission Type
        perm_types = frappe.get_all(
            "Permission Type",
            filters={
                "perm_type": ptype,
                "doc_type": doctype
            },
            pluck="name"
        )

        for pt in perm_types:
            frappe.delete_doc(
                "Permission Type",
                pt,
                ignore_permissions=True
            )

    frappe.db.commit()
    frappe.clear_cache()

def set_full_permissions():

    roles = [
        "System Manager",
        "Sales Master Manager - ALVOIP",
        "Sales Master Manager - AVTECH",
        "Sales Master Manager - DMS",

        "Sales Manager - ALVOIP",
        "Sales Manager - AVTECH",
        "Sales Manager - DMS",
    ]
    all_doctypes = frappe.get_all(
        "DocType",
        filters={"istable": 0, "issingle": 0},
        pluck="name"
    )

    print(f"Found {len(all_doctypes)} DocTypes")

    for role in roles:
        print(f"Processing role: {role}")

        for doctype in all_doctypes:
            frappe.db.sql("""
                DELETE FROM `tabCustom DocPerm`
                WHERE parent = %s AND role = %s AND permlevel = 0
            """, (doctype, role))

            frappe.db.sql("""
                INSERT INTO `tabCustom DocPerm`
                    (name, parent, role, permlevel,
                     `select`, `read`, `write`, `create`, `delete`,
                     print, email, report, `import`, export, share,
                     amend, submit, cancel)
                VALUES
                    (%s, %s, %s, 0,
                     1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1,
                     1, 1, 1)
            """, (frappe.generate_hash(length=10), doctype, role))

    frappe.db.commit()
    print("\nDone! Run: bench clear-cache")


def set_permissions(role: str, full_access: bool = True):
    """
    Set custom DocPerm for a given role across all non-table, non-single DocTypes.

    Args:
        role: The role name to set permissions for
        full_access: If True, grant all permissions. If False, grant read-only.
    """
    all_doctypes = frappe.get_all(
        "DocType",
        filters={"istable": 0, "issingle": 0},
        pluck="name"
    )
    print(f"Found {len(all_doctypes)} DocTypes")
    print(f"Processing role: {role}")

    for doctype in all_doctypes:
        frappe.db.sql("""
            DELETE FROM `tabCustom DocPerm`
            WHERE parent = %s AND role = %s AND permlevel = 0
        """, (doctype, role))

        if full_access:
            frappe.db.sql("""
                INSERT INTO `tabCustom DocPerm`
                    (name, parent, role, permlevel,
                     `select`, `read`, `write`, `create`, `delete`,
                     print, email, report, `import`, export, share,
                     amend, submit, cancel)
                VALUES
                    (%s, %s, %s, 0,
                     1, 1, 1, 1, 1,
                     1, 1, 1, 1, 1, 1,
                     1, 1, 1)
            """, (frappe.generate_hash(length=10), doctype, role))

    frappe.db.commit()
    action = "set (full access)" if full_access else "set (read-only)"
    print(f"Done! Permissions {action} for role: {role}")
    print("Run: bench clear-cache")


def delete_permissions(role: str):
    """
    Delete all Custom DocPerm records for a given role.

    Args:
        role: The role name to remove all custom permissions for
    """
    result = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabCustom DocPerm`
        WHERE role = %s
    """, (role,))

    count = result[0][0] if result else 0
    print(f"Found {count} Custom DocPerm records for role: {role}")

    frappe.db.sql("""
        DELETE FROM `tabCustom DocPerm`
        WHERE role = %s
    """, (role,))

    frappe.db.commit()
    print(f"Done! Deleted {count} permissions for role: {role}")
    print("Run: bench clear-cache")
