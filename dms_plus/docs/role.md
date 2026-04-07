1- create_roles / delete_roles:
 methos path: dms_plus/dms_plus/install/roles.py
 this create/ remove  Role for All DMS roles

2- create_ptypes / delete_ptypes :
    methos path: dms_plus/dms_plus/install/roles.py
    Create / reomve Custom permission Type for Every Doctype in List  Like Create can_view_if_account_manager

3- remove_permission_type:
        methos path: dms_plus/dms_plus/install/roles.py
        Remove a specific permission type from:
        1. Custom DocPerm (first - dependency)
        2. Permission Type


4-
    Quotation Work flow Sate:

        Draft
        Pending Approval
        Approved Sales Manager
        Approved Sales Master Manager
        Approved CEO
        Rejected Sales Manager
        Rejected Sales Master Manager
        Rejected CEO
        Cancelled

5-
   Quotation :(Draft)

    CEO:
        Draft → Pending Approval
        DocStatus: 0
        Allowed:

