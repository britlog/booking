# -*- coding: utf-8 -*-
# Copyright (c) 2016, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import throw, _
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from frappe.utils import now_datetime

class Booking(Document):

	def after_insert(self):
		doc = frappe.get_doc("Booking Slot", self.slot)

		# set property to the document
		doc.available_places -= 1

		# insert new booking class into child table
		subscriptions = get_subscriptions(self.email_id, doc.type)

		doc.append("bookings", {
			"booking": self.name,
			"subscriber": subscriptions[0]["customer"] if subscriptions else "",
			"subscription": subscriptions[0]["subscription"] if len(subscriptions) == 1 else ""
		})

		# save document to the database
		doc.save()

		# send email notification
		email = self.email_id

		if email:
			# add email to the main newsletter
			parsed_email = frappe.utils.validate_email_add(email, False)
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

		# send SMS notification
		if self.phone and self.confirm_sms:
			receiver_list = [self.phone]

			sms_template = frappe.db.get_single_value('Booking Settings', 'booking_sms')
			args = frappe.get_doc('Booking Slot', self.slot).as_dict()
			message = frappe.render_template(sms_template, args)

			try:
				send_sms(receiver_list,message,'',False)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), 'SMS failed')  # Otherwise, booking is not registered in database if errors

		# always send notification email to company master
		forward_to_email = frappe.db.get_value("Contact Us Settings", None, "forward_to_email")
		if forward_to_email:
			messages = (
				_("Nouvelle réservation n°"),
				self.name,
				_("pour le"),
				self.slot,
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
			try:
				frappe.sendmail(recipients=forward_to_email, sender=email, content=content.format(*messages), subject="Réservation de "+self.full_name)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(),'email to company failed')  # Otherwise, booking is not registered in database if errors


	# def on_trash(self):
	# 	doc = frappe.get_doc("Booking Slot", self.slot)
	#
	# 	# add available place if this booking was not already cancelled
	# 	if not self.cancellation_date:
	# 		doc.available_places += 1
	#
	# 	# save a document to the database
	# 	doc.save()

	# def on_update(self):
	# 	update_available_places(self.slot)

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


# def update_available_places(slot):
# 	doc = frappe.get_doc("Booking Slot", slot)
#
# 	doc.available_places = doc.total_places \
# 		- frappe.db.sql("""select COUNT(*) from `tabBooking Class` where parent = %(slot)s and cancellation_date is null""",
# 		{"slot": slot})[0][0] \
# 		- frappe.db.sql("""select COUNT(*) from `tabBooking Subscriber` where parent = %(slot)s and cancellation_date is null""",
# 		{"slot": slot})[0][0]
#
# 	doc.save()


def is_trial_class(email, class_type):

	if not frappe.get_value("Booking Type", class_type, 'allow_trial_class'):
		return False
	else:
		booking_nb = frappe.db.sql("""select COUNT(*) from `tabBooking` B 
			inner join `tabBooking Slot` BS on B.slot = BS.name
			inner join  `tabBooking Type` BT on BS.type = BT.name
			where B.email_id = %(email)s and BT.allow_trial_class = 1""",
			{"email": email})[0][0]

		return True if booking_nb <= 0 else False


@frappe.whitelist(allow_guest=True)
def get_subscriptions(email_id, class_type):

	subscriptions = frappe.db.sql("""
		select	C.name as customer, 
			    BSU.name as subscription,
			    BSU.remaining_catch_up
		from `tabBooking Subscription` BSU
		inner join `tabCustomer` C on BSU.customer = C.name
		inner join `tabDynamic Link` DL on C.name = DL.link_name
		inner join `tabContact` CT on DL.parent = CT.name
		where CT.email_id = %(email)s and BSU.remaining_classes > 0 and BSU.disabled = 0
		order by BSU.remaining_catch_up DESC""",
		{"email": email_id}, as_dict=True)

	if subscriptions:
		if frappe.db.get_single_value('Booking Settings', 'enable_catch_up') and not subscriptions[0]["remaining_catch_up"] :
			subscriptions[0]["subscription"] = ""

		if frappe.get_value("Booking Type", class_type, 'outside_subscription'):
			subscriptions[0]["subscription"] = ""

	return subscriptions