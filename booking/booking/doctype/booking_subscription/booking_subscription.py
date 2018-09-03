# -*- coding: utf-8 -*-
# Copyright (c) 2018, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BookingSubscription(Document):
	pass

@frappe.whitelist(allow_guest=True)
def get_subscriptions(email_id):

	return frappe.db.sql("""
	select
		BSU.name,
		BSU.reference,
		BSU.subscribed_classes AS subscribed_classes,
		BSU.remaining_classes AS remaining_classes,
		DATE_FORMAT(BSU.start_date,%(str)s) AS start_date,
		DATE_FORMAT(BSU.end_date,%(str)s) AS end_date
	from `tabBooking Subscription` BSU
	inner join `tabCustomer` C on BSU.customer = C.name
	inner join `tabDynamic Link` DL on C.name = DL.link_name
	inner join `tabContact` CT on DL.parent = CT.name
	where CT.email_id = %(email)s and BSU.disabled = 0
	order by start_date desc""",
	{"str": '%d-%m-%Y', "email": email_id},as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_classes(subscription_id):

	return frappe.db.sql("""
	select
		BS.name AS slot,
		BS.type AS style,
		SUB.present
	from `tabBooking Slot` BS   
	inner join `tabBooking Subscriber` SUB on BS.name=SUB.parent
	where SUB.subscription = %(subscription)s
	order by BS.time_slot desc""",
	{"subscription": subscription_id},as_dict=True)