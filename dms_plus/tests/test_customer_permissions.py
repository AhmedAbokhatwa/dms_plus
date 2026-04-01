
# Test Junior -> Sales Junior Sales - Network DEPT
# Test Senior -> Sales Senior Sales - Network DEPT

# Test Manager  -> Sales Manager - Network

# logic 1
# if a user does not have any of the Network roles,
# the permission logic will prevent them from accessing Customers that belong to Network users

import frappe
from dms_plus.crm_permissions.customer_permissions import get_permission_query_conditions
import unittest

class TestCustomerPermissions(unittest.TestCase):

    def test_customer_visibility(self):
        user_test = frappe.set_user("test@gmail.com")
        sql = get_permission_query_conditions(user=user_test)
        customers = frappe.get_list(
            "Customer",
            fields=["name","owner"],
            ignore_permissions=False
        )

        print(customers)

        self.assertTrue(isinstance(customers, list))

    def test_customer_access(self):
        frappe.set_user("test@gmail.com")

        customers = frappe.get_list(
            "Customer",
            filters={"name": "Customer Test A"},
            fields=["name"]
        )
        for c in customers:
            print("customer:",c)

        self.assertTrue(
            all(c["owner"] == "test@gmail.com" for c in customers)
        )
