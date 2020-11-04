# -*- coding: utf-8 -*-
# Copyright (c) 2018, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
import datetime
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

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
				update `tabBooking Subscriber` BSU 
				inner join `tabBooking Subscription` BSN on BSU.subscription = BSN.name 
				inner join `tabBooking Slot` BSL on BSU.parent = BSL.name
				set BSU.present = 1
				where (BSU.cancellation_date is null 
				or BSU.cancellation_date > DATE_ADD(BSL.time_slot, INTERVAL -BSU.cancellation_period HOUR)) 
				and BSU.present = 0 and BSN.disabled = 0 and BSL.time_slot < NOW()""")

			frappe.db.sql("""
				update `tabBooking Class` BCL 
				inner join `tabBooking Subscription` BSN on BCL.subscription = BSN.name 
				inner join `tabBooking Slot` BSL on BCL.parent = BSL.name
				set BCL.present = 1
				where (BCL.cancellation_date is null 
				or BCL.cancellation_date > DATE_ADD(BSL.time_slot, INTERVAL -BCL.cancellation_period HOUR)) 
				and BCL.present = 0 and BSN.disabled = 0 and BSL.time_slot < NOW()""")

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
			doc.save(ignore_permissions=True)


@frappe.whitelist()
def get_remaining_classes(subscribed_classes, subscription):

	if not subscribed_classes:
		subscribed_classes = 0

	# remaining classes
	classes = int(subscribed_classes) \
		- frappe.db.sql("""select ifnull(SUM(BSU.class_coefficient),0) 
			from `tabBooking Subscriber` BSU
			where BSU.subscription = %(subscription)s and BSU.present = 1""",
			{"subscription": subscription})[0][0] \
		- frappe.db.sql("""select ifnull(SUM(BCL.class_coefficient),0) 
			from `tabBooking Class` BCL
			where BCL.subscription = %(subscription)s and BCL.present = 1""",
			{"subscription": subscription})[0][0]

	return classes #max(0,classes)

@frappe.whitelist()
def get_remaining_catch_up(allowed_catch_up, subscription):

	if not allowed_catch_up:
		allowed_catch_up = 0

	# remaining catch up
	catch_up = int(allowed_catch_up) \
		- frappe.db.sql("""select ifnull(SUM(BCL.class_coefficient),0) 
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
		BSU.remaining_catch_up AS remaining_catch_up,
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
		TBS.class_coefficient,
		BS.time_slot,
		TBS.present,
		"" AS booking_no,
		DATE_FORMAT(TBS.cancellation_date,%(str)s) AS cancellation_date,
		BT.is_cancelable,
		BT.cancellation_period,
		BS.streaming_link
	from `tabBooking Slot` BS
	inner join `tabBooking Type` BT ON BS.Type = BT.name   
	inner join `tabBooking Subscriber` TBS on BS.name = TBS.parent
	where TBS.subscription = %(subscription)s	
	union ALL
	select
		BS.name AS slot,
		BS.time_slot_display,
		BS.type AS style,
		TBC.class_coefficient,
		BS.time_slot,
		TBC.present,
		IFNULL(TBC.booking,'') AS booking_no,
		DATE_FORMAT(TBC.cancellation_date,%(str)s) AS cancellation_date,
		BT.is_cancelable,
		BT.cancellation_period,
		BS.streaming_link
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
			update `tabBooking Class` BCL
			inner join `tabBooking Slot` BSL ON BCL.parent = BSL.name
			inner join `tabBooking Type` BT ON BSL.Type = BT.name
			SET BCL.cancellation_date = NOW(), BCL.cancellation_period = BT.cancellation_period 
			where BCL.parent = %(parent)s and BCL.subscription = %(subscription)s """,
			{"parent": slot, "subscription": subscription_id})
	else:
		frappe.db.sql("""
			update `tabBooking Subscriber` BSU
			inner join `tabBooking Slot` BSL ON BSU.parent = BSL.name
			inner join `tabBooking Type` BT ON BSL.Type = BT.name
			SET BSU.cancellation_date = NOW(), BSU.cancellation_period = BT.cancellation_period 
			where BSU.parent = %(parent)s and BSU.subscription = %(subscription)s """,
			{"parent":slot, "subscription": subscription_id})

	frappe.db.commit()

	# free 1 place
	doc = frappe.get_doc("Booking Slot", slot)

	# set property to the document
	doc.available_places += 1

	# save document to the database
	doc.save(ignore_permissions=True)

	return True

def set_delivery_date(doc, method):
	if doc.order_type == "Shopping Cart":
		doc.delivery_date = datetime.datetime.now().date()
		for item in doc.items:
			item.delivery_date = doc.delivery_date

def create_subscription(doc, method):
	if doc.order_type == "Shopping Cart":
		for item in doc.items:
			doc_item = frappe.get_doc("Item", item.item_code)
			if doc_item.create_subscription:
				date_now = datetime.datetime.now().date()
				doc_subscription = frappe.get_doc({
					"doctype": "Booking Subscription",
					"customer": doc.customer,
					"email_id": doc.contact_email,
					"reference": item.item_code,
					"activities": doc_item.subscription_activities,
					"comment": "Créé automatiquement",
					"subscribed_classes": doc_item.subscription_classes,
					"remaining_classes": doc_item.subscription_classes,
					"start_date": date_now,
					"end_date": date_now + datetime.timedelta(weeks = doc_item.subscription_validity_weeks)
				})
				doc_subscription.insert(ignore_permissions=True)

def make_delivery_note_shopping_cart():

	# make delivery note for shopping cart orders
	orders = frappe.get_all("Sales Order",
		filters=[["order_type", "=", "Shopping Cart"], ["delivery_date", "<", now_datetime()],
				 ["status", "in", ["To Deliver", "To Deliver and Bill"]]],
		fields=['name'])

	for order in orders:
		dn = make_delivery_note(order.name)
		dn = dn.insert()
		dn.submit()

@frappe.whitelist()
def get_class_coefficient(subscription, activity):

	coefficient = frappe.db.sql("""
		select ifnull(BSA.class_coefficient, (select class_coefficient from `tabBooking Type` where name = %(activity)s)) 
		from `tabBooking Subscription` BSU
		left join `tabBooking Subscription Activity` BSA ON BSU.name = BSA.parent and BSA.activity = %(activity)s		
		where BSU.name = %(subscription)s""",
		  {"subscription": subscription, "activity": activity})

	return coefficient[0][0] if coefficient else 1