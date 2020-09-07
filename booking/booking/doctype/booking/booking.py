# -*- coding: utf-8 -*-
# Copyright (c) 2016, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import throw, _
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from frappe.utils import now_datetime
from erpnext.accounts.doctype.payment_request.payment_request import make_payment_request
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note, make_sales_invoice

class Booking(Document):

	def after_insert(self):
		doc = frappe.get_doc("Booking Slot", self.slot)

		# insert new booking class into child table
		subscription = get_slot_subscription(self.email_id, self.slot)

		# payment
		type_doc = frappe.get_doc("Booking Type", doc.type)
		if type_doc.accept_payment and (not subscription or not subscription["is_valid"]) and not self.trial_class:
			# create sales order if no valid subscription
			so = make_sales_order(type_doc.billing_customer, type_doc.billing_item, doc.time_slot, doc.time_slot_display,
								  self.name, self.full_name)

			# create payment request
			pr = make_payment_request(dt="Sales Order", dn=so.name, recipient_id=self.email_id, submit_doc=True,
									  mute_email=True, return_doc=True)
			pr.set_payment_request_url()

			self.payment_request = pr.name
			self.status = "Payment Ordered"
			self.save(ignore_permissions=True)

		else:
			# confirm booking
			# in case of payment, it will be done after successful payment
			self.status = "Confirmed"
			self.save(ignore_permissions=True)

			# add booking to slot
			doc.append("bookings", {
				"full_name": self.full_name,
				"booking": self.name,
				"subscriber": subscription["customer"] if subscription else "",
				"subscription": subscription["subscription"] if subscription and subscription["is_valid"] else ""
			})

			# decrease available places
			doc.available_places -= 1

			# save document to the database
			doc.save(ignore_permissions=True)

			# send SMS confirmation
			self.send_sms_confirmation()

		# send email to company master, even if payment not done yet
		# otherwise, customer comment may never be read
		self.send_email_to_company()

		# add email to the main newsletter
		self.add_email_to_newsletter()

	def before_insert(self):

		# check if already registered
		booked = frappe.db.sql("""select COUNT(*)
				 from `tabBooking Class` TBC
				 inner join `tabBooking` TB on TBC.booking = TB.name 
				 where TBC.parent = %(slot)s and TB.email_id = %(email)s""",
				 {"slot": self.slot, "email": self.email_id})[0][0]

		booked += frappe.db.sql("""select COUNT(*)
				 from `tabBooking Subscriber`
				 inner join `tabCustomer` on `tabBooking Subscriber`.subscriber = tabCustomer.name
				 inner join `tabDynamic Link` on tabCustomer.name=`tabDynamic Link`.link_name
				 inner join `tabContact` on `tabDynamic Link`.parent=tabContact.name
				 where `tabBooking Subscriber`.parent = %(slot)s and `tabContact`.email_id = %(email)s""",
				 {"slot": self.slot, "email": self.email_id})[0][0]

		# raise error
		if booked > 0 :
			frappe.throw("Vous êtes déjà inscrit à cette séance")

		# check available places before saving
		doc = frappe.get_doc("Booking Slot", self.slot)

		# raise error
		if doc.available_places <= 0:
			frappe.throw("""Plus de place disponible pour cette séance, vous pouvez néanmoins
						vous inscrire sur la liste d'attente pour recevoir un mail si une place se libère.""")

		# manage trial class
		self.trial_class = is_trial_class(self.email_id, doc.type)

		# get subscription if any
		subscription = get_slot_subscription(self.email_id, self.slot)

		# error if guest booking is not allowed
		if not self.trial_class and frappe.get_value("Booking Type", doc.type, 'disable_guest_booking'):
			if not subscription or not subscription["is_valid"]:
				frappe.throw(frappe.db.get_single_value('Booking Settings', 'guest_booking_message'))


	def send_sms_confirmation(self):
		# send SMS notification
		if self.phone and self.confirm_sms:
			receiver_list = [self.phone]

			sms_template = frappe.db.get_single_value('Booking Settings', 'booking_sms')
			args = frappe.get_doc('Booking Slot', self.slot).as_dict()
			message = frappe.render_template(sms_template, args)

			try:
				send_sms(receiver_list, message, '', False)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(),
								 'SMS failed')  # Otherwise, booking is not registered in database if errors

	def send_email_to_company(self):
		# send notification email to company master
		forward_to_email = frappe.db.get_value("Contact Us Settings", None, "forward_to_email")
		comment_only_email_notify = frappe.db.get_single_value('Booking Settings', 'comment_only_email_notify')

		if forward_to_email and (self.comment or not comment_only_email_notify):
			messages = (
				_("Nouvelle réservation n°"),
				self.name,
				_("pour le"),
				frappe.db.get_value("Booking Slot", self.slot, "time_slot_display"),
				_("Nom"),
				self.full_name,
				_("Commentaire"),
				self.comment
			)

			content = """
				<div style="font-family: verdana; font-size: 16px;">
				<p>{0} {1} {2} <strong>{3}</strong>.</p>
				<p>{4} : {5}</p>
				<p>{6} : {7}</p>
				</div>
				"""

			subject = "Réservation de " + self.full_name
			if self.comment and not comment_only_email_notify:
				subject += "*"

			try:
				frappe.sendmail(recipients=forward_to_email, sender=self.email_id, content=content.format(*messages),
								subject=subject)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(),
								 'email to company failed')  # Otherwise, booking is not registered in database if errors

	def add_email_to_newsletter(self):
		if self.email_id:
			parsed_email = frappe.utils.validate_email_add(self.email_id, False)
			email_group = _("Website", lang='fr')

			if parsed_email:
				if not frappe.db.get_value("Email Group Member",
										   {"email_group": email_group, "email": parsed_email}):
					frappe.get_doc({
						"doctype": "Email Group Member",
						"email_group": email_group,
						"email": parsed_email
					}).insert(ignore_permissions=True)

				frappe.get_doc("Email Group", email_group).update_total_subscribers()
				frappe.db.commit()

def is_trial_class(email, activity):

	if not frappe.get_value("Booking Type", activity, 'allow_trial_class'):
		return False
	else:
		booking_nb = frappe.db.sql("""select COUNT(*) from `tabBooking` B 
			where B.email_id = %(email)s and B.status = 'Confirmed' and B.trial_class = 1""",
			{"email": email})[0][0]

		return True if booking_nb <= 0 else False

def make_sales_order(customer, item_code, delivery_date, time_slot, booking_name, full_name):

	company = frappe.db.get_single_value('Global Defaults', 'default_company')
	default_terms = frappe.get_value("Company", company, 'default_terms')

	doc = frappe.get_doc({
		"doctype": "Sales Order",
		"customer": customer,
		"company": company,
		"delivery_date": delivery_date,
		"items": [{
			'doctype': 'Sales Order Item',
			'item_code': item_code,
			'description': "Cours du "+time_slot,
			'qty': 1
		}],
		"tc_name": default_terms,
		"terms": frappe.db.get_value("Terms and Conditions", default_terms, "terms"),
		"booking": booking_name,
		"title": full_name
	})

	doc.insert(ignore_permissions=True)
	doc.submit()

	return doc

def update_payment_status(pr_doc, method):

	# confirm booking when payment request is paid
	if pr_doc.reference_doctype == "Sales Order" and pr_doc.status == "Paid":

		# get the booking
		booking_name = frappe.db.get_value("Sales Order", pr_doc.reference_name, "booking")

		if booking_name:
			booking_doc = frappe.get_doc("Booking", booking_name)
			booking_doc.status = "Confirmed"
			booking_doc.save(ignore_permissions=True)

			slot_doc = frappe.get_doc("Booking Slot", booking_doc.slot)
			slot_doc.append("bookings", {
				"full_name": booking_doc.full_name,
				"booking": booking_doc.name
			})

			# decrease available places
			slot_doc.available_places -= 1
			slot_doc.save(ignore_permissions=True)

			# send SMS confirmation
			booking_doc.send_sms_confirmation()

def convert_sales_order():

	# make sales invoice from sales order
	# get all sales orders linked to a booking
	orders = frappe.get_all("Sales Order",
				filters=[["ifnull(booking, '')", "!=", ""], ["delivery_date", "<", now_datetime()],
						 ["status", "=", "To Deliver and Bill"]],
				fields=['name','booking'])

	for order in orders:

		# first cancel orders without payment entry
		bk = frappe.get_doc("Booking", order.booking)

		if bk.status == "Payment Ordered":
			# cancel the payment request
			pr = frappe.get_doc("Payment Request", bk.payment_request)
			if pr:
				pr.cancel()

			# cancel the order
			so = frappe.get_doc("Sales Order", order.name)
			if so:
				so.cancel()

		else:
			# without delivery note, sales order status will stay in "Overdue"
			dn = make_delivery_note(order.name)
			dn = dn.insert()
			dn.submit()

			# finally make the invoice and get the advance payment
			si = make_sales_invoice(order.name)
			si.allocate_advances_automatically = True
			si = si.insert()
			si.submit()

def update_booking_status(slot=None):

	# get all bookings of this slot
	bookings = frappe.get_all("Booking Class",
		filters=[ ["parent", "=", slot] ],
		fields=['booking', 'cancellation_date'])

	for booking in bookings:
		if booking.booking:
			doc = frappe.get_doc('Booking', booking.booking)

			if booking.cancellation_date:
				status = "Cancelled"
			else:
				status = "Confirmed"

			if doc.status != status:
				doc.status = status
				doc.save(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def get_slot_subscription(email_id, slot_id):

	subscription = {}

	subscriptions = frappe.db.sql("""
		select	C.name as customer, 
				BSU.name as subscription,
				BSU.remaining_classes,
				BSU.remaining_catch_up
		from `tabBooking Subscription` BSU
		inner join `tabCustomer` C on BSU.customer = C.name
		inner join `tabDynamic Link` DL on C.name = DL.link_name
		inner join `tabContact` CT on DL.parent = CT.name
		where CT.email_id = %(email)s and BSU.remaining_classes > 0 and BSU.end_date > NOW() and BSU.disabled = 0
		order by BSU.remaining_catch_up DESC""",
		{"email": email_id}, as_dict=True)

	if subscriptions:
		subscription = subscriptions[0]
		subscription["is_valid"] = True
		subscription["warning_msg"] = ""

		# available classes = subscription remaining classes - pending bookings
		available_classes = float(subscription["remaining_classes"]) \
		  - frappe.db.sql("""select ifnull(SUM(BTP.class_coefficient),0) 
			from `tabBooking Subscriber` BSU
			inner join `tabBooking Slot` BSL ON BSU.parent = BSL.name
			inner join `tabBooking Type` BTP ON BSL.Type = BTP.name
			where BSU.subscription = %(subscription)s and BSU.present = 0 and BSU.cancellation_date is null""",
						  {"subscription": subscription["subscription"]})[0][0] \
		  - frappe.db.sql("""select ifnull(SUM(BTP.class_coefficient),0) 
			from `tabBooking Class` BCL
			inner join `tabBooking Slot` BSL ON BCL.parent = BSL.name
			inner join `tabBooking Type` BTP ON BSL.Type = BTP.name
			where BCL.subscription = %(subscription)s and BCL.present = 0 and BCL.cancellation_date is null""",
						  {"subscription": subscription["subscription"]})[0][0]

		activity = frappe.get_value("Booking Slot", slot_id, 'type')
		coefficient = frappe.get_value("Booking Type", activity, 'class_coefficient')

		if available_classes < coefficient:
			# not enough remaining classes for this slot
			return False

		if frappe.get_value("Booking Type", activity, 'outside_subscription'):
			subscription["is_valid"] = False
			subscription["warning_msg"] = "Cours hors abonnement, souhaitez-vous valider la réservation ?"

		if subscription["is_valid"] and frappe.get_value("Booking Type", activity, 'check_catch_up') \
				and subscription["remaining_catch_up"] <= 0:
			subscription["is_valid"] = False
			subscription["warning_msg"] = "Cours hors rattrapage, souhaitez-vous valider la réservation ?"

	return subscription