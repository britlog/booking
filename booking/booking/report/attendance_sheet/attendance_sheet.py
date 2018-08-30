# -*- coding: utf-8 -*-
# Copyright (c) 2013, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _

def execute(filters=None):

	if not filters: filters = {}

	columns = get_columns(filters)
	data = get_subscribers(filters.get("slot"))
	data += get_bookings(filters.get("slot"))

	return columns, data

def get_columns(filters):
	columns = [
		_("Name") + "::200",
		_("Booking No") + "::100",
		_("Trial Class") + ":Check:100",
		_("Remaining Classes") + "::100",
		_("End Date")+ ":Date:100",
		_("Cancellation Date") + ":Date:100",
		_("Present") + ":Check:100"
	]
	return columns

def get_subscribers(slot):
	subscribers =  frappe.db.sql("""select C.customer_name, 'Abonné', '', SUB.remaining_classes,
			SUB.end_date, BS.cancellation_date, BS.present
		from `tabBooking Subscriber` BS
		inner join tabCustomer C on BS.subscriber = C.name
		inner join `tabBooking Subscription` SUB on BS.subscription = SUB.name
		where BS.parent = %s order by BS.subscriber""", slot, as_dict=0)
	return subscribers

def get_bookings(slot):
	customers =  frappe.db.sql("""select full_name, name, trial_class, '', '', cancellation_date, present from `tabBooking`
		where slot=%s order by full_name""", slot, as_dict=0)
	return customers