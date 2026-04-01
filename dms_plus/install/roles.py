import frappe

def after_install():
    create_roles()
    create_ptypes()

def after_uninstall():
    delete_roles()
    delete_ptypes()

def create_roles():
    roles = [
        # DMS
        "Sales Master Manager - DMS",
        "Sales Manager - DMS",
        "Product Manager - DMS",
        "Sales Coordinator - DMS",
        "Senior Sales - DMS",
        "Junior Sales - DMS",

        # ALVOIP
        "Sales Master Manager - ALVOIP",
        "Sales Manager - ALVOIP",
        "Product Manager - ALVOIP",
        "Sales Coordinator - ALVOIP",
        "Senior Sales - ALVOIP",
        "Junior Sales - ALVOIP",

        # AVTECH
        "Sales Master Manager - AVTECH",
        "Sales Manager - AVTECH",
        "Product Manager - AVTECH",
        "Sales Coordinator - AVTECH",
        "Senior Sales - AVTECH",
        "Junior Sales - AVTECH",
    ]

    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1,
                "is_custom": 1
            }).insert(ignore_permissions=True)

    frappe.db.commit()

def delete_roles():
    roles = [
        # DMS
        "Sales Master Manager - DMS",
        "Sales Manager - DMS",
        "Product Manager - DMS",
        "Sales Coordinator - DMS",
        "Senior Sales - DMS",
        "Junior Sales - DMS",

        # ALVOIP
        "Sales Master Manager - ALVOIP",
        "Sales Manager - ALVOIP",
        "Product Manager - ALVOIP",
        "Sales Coordinator - ALVOIP",
        "Senior Sales - ALVOIP",
        "Junior Sales - ALVOIP",

        # AVTECH
        "Sales Master Manager - AVTECH",
        "Sales Manager - AVTECH",
        "Product Manager - AVTECH",
        "Sales Coordinator - AVTECH",
        "Senior Sales - AVTECH",
        "Junior Sales - AVTECH",
    ]

    for role in roles:
        if frappe.db.exists("Role", role):
            frappe.delete_doc("Role", role, ignore_permissions=True)

    frappe.db.commit()

def create_ptypes():
    """ Create Permission Types For All Documents"""
    for doctype in frappe.get_all("DocType", filters={"istable": 0}, pluck="name"):
        for ptype in ["can_view_company", "can_view_all"]:
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
        for ptype in ["can_view_company", "can_view_all"]:
            if frappe.db.exists("Permission Type", {"perm_type": ptype, "doc_type": doctype}):
                doc = frappe.get_doc("Permission Type", {"perm_type": ptype, "doc_type": doctype})
                doc.delete(ignore_permissions=True)
    frappe.db.commit()
