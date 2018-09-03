import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def set_attendance(customer=""):
    print("set attendance called")
    print(customer)
    # frappe.db.sql("""
        # 	update `tabBooking Subscriber` set present = 1
        # 	where parent = %(parent)s and customer_id = %(customer)s """,
        #   {"parent": slot, "customer": fields.email_id})