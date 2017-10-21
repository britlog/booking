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

		# save document to the database
		doc.save()

		# send email notification
		email = self.email_id

		if email:
			url = frappe.utils.get_url("/files/logo_santani_small.png")

			messages = (
				_("Bonjour"),
				_("J'ai le plaisir de vous informer que votre réservation n°"),
				self.name,
				_("est confirmée pour le"),
				self.slot,
				_("N'oubliez pas de prévenir en cas d'absence. Merci."),
				_("Namasté"),
				url
			)

			content = """
				<div style="font-family: verdana; font-size: 16px;">
				<p>{0},<p>
				<p>{1} {2} {3}</p>
				<p><strong>{4}</strong></p>
				<p>{5}</p>
				<p>{6},<br>Tonya</p>
				<img alt="Santani Yoga" src="{7}">
				</div>
				"""

			try:
				frappe.sendmail(email, subject=_("Votre cours de yoga"), content=content.format(*messages))
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), 'email failed')    # Otherwise, booking is not registered in database if errors

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
			message = "Santani Yoga : votre cours du "+self.slot+" est confirmé. Namasté, Tonya. Merci de ne pas répondre (message automatique)."

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


	def on_trash(self):
		doc = frappe.get_doc("Booking Slot", self.slot)

		# add available place if this booking was not already cancelled
		if not self.cancellation_date:
			doc.available_places += 1

		# save a document to the database
		doc.save()

	def on_update(self):
		update_available_places(self.slot)

	def before_insert(self):

		# check if already registered
		booked = frappe.db.sql("""select COUNT(*)
				 from `tabBooking`
				 where `tabBooking`.slot = %(slot)s and `tabBooking`.email_id = %(email)s""",
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
			frappe.throw("""Plus de place disponible pour cette séance, vous pouvez néanmoins demander
						à être prévenu par e-mail si une place se libère.""")


def update_available_places(slot):
	doc = frappe.get_doc("Booking Slot", slot)

	doc.available_places = doc.total_places \
		- frappe.db.sql("""select COUNT(*) from `tabBooking` where slot = %(slot)s and cancellation_date is null""",
		{"slot": slot})[0][0] \
		- frappe.db.sql("""select COUNT(*) from `tabBooking Subscriber` where parent = %(slot)s and cancellation_date is null""",
		{"slot": slot})[0][0]

	doc.save()