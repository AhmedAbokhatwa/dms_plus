import frappe

FIELDS = {
    "Custom DocPerm": [
        {
            "fieldname": "can_view_company",
            "label": "Can view documents in same company",
            "fieldtype": "Check",
            "insert_after": "if_owner",
            "description": "Allow users to view documents if they belong to the same company.",
        },
    ],
    "DocPerm": [
        {
            "fieldname": "can_view_company",
            "label": "Can view documents in same company",
            "fieldtype": "Check",
            "insert_after": "if_owner",
            "description": "Allow users to view documents if they belong to the same company.",
        },
    ],
}


def before_uninstall():
    delete_custom_fields()


def after_install():
    create_custom_fields()


def get_custom_fields():
    custom_fields = []
    for dt, fields in FIELDS.items():
        for f in fields:
            custom_fields.append({
                "doctype": "Custom Field",
                "dt": dt,
                **f
            })
    return custom_fields


def create_custom_fields():
    for dt, fields in FIELDS.items():
        for f in fields:
            if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": f["fieldname"]}):
                doc = frappe.get_doc({
                    "doctype": "Custom Field",  # ✅ fixed
                    "dt": dt,                   # ✅ fixed
                    "module": "dms_plus",
                    **f
                })
                doc.insert(ignore_permissions=True)
    frappe.db.commit()


def delete_custom_fields():
    for dt, fields in FIELDS.items():
        for f in fields:
            cf = frappe.db.exists("Custom Field", {
                "dt": dt,
                "fieldname": f["fieldname"],
            })
            if cf:
                frappe.delete_doc("Custom Field", cf, ignore_permissions=True)
    frappe.db.commit()
