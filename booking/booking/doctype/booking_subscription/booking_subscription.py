# -*- coding: utf-8 -*-
# Copyright (c) 2018, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BookingSubscription(Document):
	pass

@frappe.whitelist()
def update_subscriptions(slot=None):

	# get all customers in the slot
	# it limits the calculation if defined, mostly when a booking slot is saved
	if slot:
		customers = frappe.db.sql("""
			select TBS.subscriber
			from `tabBooking Slot` BS   
			inner join `tabBooking Subscriber` TBS on BS.name = TBS.parent
			where TBS.subscriber is not null and BS.name = %(slot)s	
			union
			select TBC.subscriber
			from `tabBooking Slot` BS   
			inner join `tabBooking Class` TBC on BS.name = TBC.parent
			where TBC.subscriber is not null and BS.name = %(slot)s""",
				{"slot": slot}, as_dict=False)

		# get all active subscriptions of customers in this slot
		subscriptions = frappe.get_all("Booking Subscription",
			filters=[ ["disabled", "=", 0], ["customer", "in", [customer[0] for customer in customers]] ],
			fields=['name'])

	else:
		# get all active subscriptions
		subscriptions = frappe.get_all("Booking Subscription",
			filters=[["disabled", "=", 0]],
			fields=['name'])

	for subscription in subscriptions:
		doc = frappe.get_doc('Booking Subscription', subscription.name)
		remaining_classes = get_remaining_classes(doc.subscribed_classes, doc.name)

		if doc.remaining_classes != remaining_classes:
			doc.remaining_classes = remaining_classes

			# save the Subscription Doctype to the database
			doc.save()


@frappe.whitelist()
def get_remaining_classes(subscribed_classes, subscription):

	if not subscribed_classes:
		subscribed_classes=0

	classes = int(subscribed_classes) \
		- frappe.db.sql("""select COUNT(*) from `tabBooking Subscriber`
			where subscription = %(subscription)s and present = 1""",
			{"subscription": subscription})[0][0] \
		- frappe.db.sql("""select COUNT(*) from `tabBooking Class`
			where subscription = %(subscription)s and present = 1""",
			{"subscription": subscription})[0][0]

	# classes = int(total_classes) - frappe.db.count("Booking Subscriber", {"subscriber": customer_id, "present": 1})

	# missed = frappe.db.sql("""select COUNT(*)
	#     from `tabBooking Subscriber`
	#     inner join `tabBooking Slot` on `tabBooking Subscriber`.parent=`tabBooking Slot`.name
	#     where `tabBooking Subscriber`.subscriber = %(customer)s and present = 0
	#     and CAST(`tabBooking Slot`.time_slot AS DATE)>=%(subscription_date)s""",
	#     {"customer": customer_id , "subscription_date": start_date})[0][0]
	#
	# # missed = frappe.db.count("Booking Subscriber",{"subscriber": customer_id, "present": 0})
	#
	# if total_classes == 10:
	#     max_missed = 2
	# elif total_classes == 20:
	#     max_missed = 4
	# elif total_classes == 40:
	#     max_missed = 8
	# else:
	#     max_missed = 99  # unlimited
	#
	# lost = missed - max_missed
	#
	# if lost>0:
	#     classes -= lost  # lost classes

	return classes #max(0,classes)

@frappe.whitelist(allow_guest=True)
def get_subscriptions(email_id):

	return frappe.db.sql("""
	select
		BSU.name,
		IFNULL(BSU.reference,''),
		BSU.subscribed_classes AS subscribed_classes,
		BSU.remaining_classes AS remaining_classes,
		DATE_FORMAT(BSU.start_date,%(str)s) AS start_date,
		DATE_FORMAT(BSU.end_date,%(str)s) AS end_date
	from `tabBooking Subscription` BSU
	inner join `tabCustomer` C on BSU.customer = C.name
	inner join `tabDynamic Link` DL on C.name = DL.link_name
	inner join `tabContact` CT on DL.parent = CT.name
	where CT.email_id = %(email)s and BSU.disabled = 0
	order by BSU.start_date desc""",
	{"str": '%d-%m-%Y', "email": email_id},as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_classes(subscription_id):

	return frappe.db.sql("""
	select
		BS.name AS slot,
		BS.type AS style,
		BS.time_slot,
		TBS.present,
		"" AS booking_no,
		DATE_FORMAT(TBS.cancellation_date,%(str)s) AS cancellation_date
	from `tabBooking Slot` BS   
	inner join `tabBooking Subscriber` TBS on BS.name = TBS.parent
	where TBS.subscription = %(subscription)s	
	union ALL
	select
		BS.name AS slot,
		BS.type AS style,
		BS.time_slot,
		TBC.present,
		TBC.booking AS booking_no,
		DATE_FORMAT(TBC.cancellation_date,%(str)s) AS cancellation_date
	from `tabBooking Slot` BS   
	inner join `tabBooking Class` TBC on BS.name = TBC.parent
	where TBC.subscription = %(subscription)s	
	order by time_slot desc""",
	{"str": '%d-%m-%Y %H:%i',"subscription": subscription_id},as_dict=True)

@frappe.whitelist(allow_guest=True)
def report_absence(slot, subscription_id, booking_no):

	if booking_no:
		frappe.db.sql("""
			update `tabBooking Class` SET cancellation_date = NOW()
			where parent = %(parent)s and subscription = %(subscription)s """,
			{"parent": slot, "subscription": subscription_id})
	else:
		frappe.db.sql("""
			update `tabBooking Subscriber` SET cancellation_date = NOW()
			where parent = %(parent)s and subscription = %(subscription)s """,
			{"parent":slot, "subscription": subscription_id})

	frappe.db.commit()

	# free 1 place
	doc = frappe.get_doc("Booking Slot", slot)

	# set property to the document
	doc.available_places += 1

	# save document to the database
	doc.save()

	return True