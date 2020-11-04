from __future__ import unicode_literals
import frappe

def execute():

	frappe.db.sql(""" UPDATE `tabBooking Subscriber` set class_coefficient = 1 """)
	frappe.db.sql(""" UPDATE `tabBooking Class` set class_coefficient = 1 """)

