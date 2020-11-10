from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doctype("Booking Subscriber")
	frappe.db.sql(""" UPDATE `tabBooking Subscriber` set class_coefficient = 1 """)

	frappe.reload_doctype("Booking Class")
	frappe.db.sql(""" UPDATE `tabBooking Class` set class_coefficient = 1 """)

