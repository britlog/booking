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
		# update presence first
		if frappe.db.get_single_value('Booking Settings', 'enable_auto_attendance'):
			frappe.db.sql("""
				UPDATE `tabBooking Subscriber` BSU INNER JOIN `tabBooking Slot` BSL ON BSU.parent = BSL.name
				SET BSU.present = 1
				WHERE BSU.subscription IS NOT NULL AND BSU.cancellation_date IS NULL AND BSU.present = 0
					AND BSL.time_slot < NOW()""")

			frappe.db.sql("""
				UPDATE `tabBooking Class` BCL INNER JOIN `tabBooking Slot` BSL ON BCL.parent = BSL.name
				SET BCL.present = 1
				WHERE BCL.subscription IS NOT NULL AND BCL.cancellation_date IS NULL AND BCL.present = 0
					AND BSL.time_slot < NOW()""")

			frappe.db.commit()

		# get all active subscriptions
		subscriptions = frappe.get_all("Booking Subscription",
			filters=[["disabled", "=", 0]],
			fields=['name'])

	for subscription in subscriptions:
		doc = frappe.get_doc('Booking Subscription', subscription.name)
		remaining_classes = get_remaining_classes(doc.subscribed_classes, doc.name)
		remaining_catch_up = get_remaining_catch_up(doc.allowed_catch_up, doc.name)

		if doc.remaining_classes != remaining_classes or doc.remaining_catch_up != remaining_catch_up :
			doc.remaining_classes = remaining_classes
			doc.remaining_catch_up = remaining_catch_up

			# save the Subscription Doctype to the database
			doc.save()


@frappe.whitelist()
def get_remaining_classes(subscribed_classes, subscription):

	if not subscribed_classes:
		subscribed_classes = 0

	# remaining classes
	classes = int(subscribed_classes) \
		- frappe.db.sql("""select ifnull(SUM(BTP.class_coefficient),0) 
			from `tabBooking Subscriber` BSU
			inner join `tabBooking Slot` BSL ON BSU.parent = BSL.name
			inner join `tabBooking Type` BTP ON BSL.Type = BTP.name
			where BSU.subscription = %(subscription)s and BSU.present = 1""",
			{"subscription": subscription})[0][0] \
		- frappe.db.sql("""select ifnull(SUM(BTP.class_coefficient),0) 
			from `tabBooking Class` BCL
			inner join `tabBooking Slot` BSL ON BCL.parent = BSL.name
			inner join `tabBooking Type` BTP ON BSL.Type = BTP.name
			where BCL.subscription = %(subscription)s and BCL.present = 1""",
			{"subscription": subscription})[0][0]

	return classes #max(0,classes)

@frappe.whitelist()
def get_remaining_catch_up(allowed_catch_up, subscription):

	if not allowed_catch_up:
		allowed_catch_up = 0

	# remaining catch up
	catch_up = int(allowed_catch_up) \
		- frappe.db.sql("""select ifnull(SUM(BTP.class_coefficient),0) 
			from `tabBooking Class` BCL
			inner join `tabBooking Slot` BSL ON BCL.parent = BSL.name
			inner join `tabBooking Type` BTP ON BSL.Type = BTP.name
			where BCL.subscription = %(subscription)s and BCL.present = 1 and BTP.check_catch_up = 1""",
			{"subscription": subscription})[0][0]

	return catch_up

@frappe.whitelist(allow_guest=True)
def get_subscriptions(email_id):

	return frappe.db.sql("""
	select
		BSU.name,
		IFNULL(BSU.reference,'') AS reference,
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
		BS.time_slot_display,
		BS.type AS style,
		BT.class_coefficient,
		BS.time_slot,
		TBS.present,
		"" AS booking_no,
		DATE_FORMAT(TBS.cancellation_date,%(str)s) AS cancellation_date
	from `tabBooking Slot` BS
	inner join `tabBooking Type` BT ON BS.Type = BT.name   
	inner join `tabBooking Subscriber` TBS on BS.name = TBS.parent
	where TBS.subscription = %(subscription)s	
	union ALL
	select
		BS.name AS slot,
		BS.time_slot_display,
		BS.type AS style,
		BT.class_coefficient,
		BS.time_slot,
		TBC.present,
		IFNULL(TBC.booking,'') AS booking_no,
		DATE_FORMAT(TBC.cancellation_date,%(str)s) AS cancellation_date
	from `tabBooking Slot` BS
	inner join `tabBooking Type` BT ON BS.Type = BT.name    
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