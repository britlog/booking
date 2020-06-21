# -*- coding: utf-8 -*-
# Copyright (c) 2015, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
import datetime

no_cache = 1

def get_context(context):
	# do your magic here
	pass

@frappe.whitelist(allow_guest=True)
def get_stock(slot):
	stock = frappe.get_doc("Booking Slot", slot)

	return str(stock.available_places)

@frappe.whitelist(allow_guest=True)
def get_introduction():
	return frappe.db.get_single_value('Booking Settings', 'booking_form_introduction')

@frappe.whitelist(allow_guest=True)
def get_activities():

	return frappe.db.sql("""
		select	distinct BS.type 
		from `tabBooking Slot` BS
		where time_slot > NOW() and show_in_website = 1
		order by BS.type""")

@frappe.whitelist(allow_guest=True)
def get_slots(activity):

	slots = frappe.db.sql("""
		select	name, time_slot_display, type, location, available_places, total_places,
			practical_information, is_replay 
		from `tabBooking Slot`
		where (time_slot > NOW() or is_replay = 1) and show_in_website = 1
			  and type = case when %(activity)s != '' then %(activity)s else type end
		order by time_slot asc""",{"activity": activity}, as_dict=True)

	for slot in slots:
		slot['subscription_places'] = slot.get('total_places') \
			- frappe.db.sql("""select COUNT(*) from `tabBooking Subscriber` where parent = %(slot)s""",
			{"slot": slot.get('name')})[0][0]

	return slots

@frappe.whitelist(allow_guest=True)
def set_notification(slot, email, name):
	doc = frappe.get_doc("Booking Slot", slot)

	# check if already registered
	booked = frappe.db.sql("""select COUNT(*)
	                from `tabBooking`
	                where `tabBooking`.slot = %(slot)s and `tabBooking`.email_id = %(email)s""",
						   {"slot": slot, "email": email})[0][0]

	booked += frappe.db.sql("""select COUNT(*)
	                from `tabBooking Subscriber`
	                inner join `tabCustomer` on `tabBooking Subscriber`.subscriber = tabCustomer.name
	                inner join `tabDynamic Link` on tabCustomer.name=`tabDynamic Link`.link_name
	                inner join `tabContact` on `tabDynamic Link`.parent=tabContact.name
	                where `tabBooking Subscriber`.parent = %(slot)s and `tabContact`.email_id = %(email)s""",
							{"slot": slot, "email": email})[0][0]

	# raise error
	if booked > 0:
		frappe.throw("Vous êtes déjà inscrit à cette séance")
	else:

		# check if already on waiting list
		waiting_list = frappe.db.sql("""select COUNT(*)
			                from `tabBooking Notification`
			                where parent = %(slot)s and email_id = %(email)s""",
					  {"slot": slot, "email": email})[0][0]

		if waiting_list > 0:
			frappe.throw("Vous êtes déjà inscrit sur la liste d'attente de cette séance")
		else:
			doc.append("notifications", {
				"email_id": email,
				"full_name": name,
				"request_date": datetime.datetime.now()
			})
			doc.save()

@frappe.whitelist(allow_guest=True)
def add_booking(slot, email, name, city, phone, sms, comment):
	validation = {}

	doc = frappe.get_doc({
		"doctype": "Booking",
		"slot": slot,
		"email_id": email,
		"full_name": name,
		"city": city,
		"phone": phone,
		"confirm_sms": sms == 'true',
		"comment": comment
	})
	doc.insert()

	# payment URL
	validation["payment_url"] = frappe.get_value("Payment Request", doc.payment_request, 'payment_url')
	validation["success_message"] = "Réservation confirmée"

	return validation