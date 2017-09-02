# -*- coding: utf-8 -*-
# Copyright (c) 2015, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import datetime

def get_context(context):
	# do your magic here
	pass

@frappe.whitelist(allow_guest=True)
def get_stock(slot):
	stock = frappe.get_doc("Booking Slot", slot)

	return str(stock.available_places)

@frappe.whitelist(allow_guest=True)
def get_slot():
	return frappe.get_all("Booking Slot",
		fields=["name", "type","available_places"],
		filters=[["Booking Slot", "time_slot", ">", datetime.datetime.now()],
				 ["Booking Slot", "available_places", ">=", 0],
				 ["Booking Slot", "show_in_website", "=", 1]],
		order_by="time_slot asc")

@frappe.whitelist(allow_guest=True)
def set_notification(slot, email, name):
	doc = frappe.get_doc("Booking Slot", slot)
	doc.append("notifications", {
		"email_id": email,
		"full_name": name,
		"request_date": datetime.datetime.now()
	})
	doc.save()
