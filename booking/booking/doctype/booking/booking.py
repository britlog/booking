# -*- coding: utf-8 -*-
# Copyright (c) 2016, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import throw, _
from erpnext.setup.doctype.sms_settings.sms_settings import send_sms
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

        # send SMS notification
        if self.phone and self.confirm_sms:
            receiver_list = [self.phone]
            message = "Santani Yoga : votre cours du "+self.slot+" est confirmé. Namasté, Tonya. Merci de ne pas répondre (robot)."

            try:
                send_sms(receiver_list,message,'',False)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), 'SMS failed')  # Otherwise, booking is not registered in database if errors

        # always send notification email to company master
        forward_to_email = frappe.db.get_value("Contact Us Settings", None, "forward_to_email")
        if forward_to_email:
            messages = (
                _("Bonjour"),
                _("J'ai le plaisir de vous informer de la réservation n°"),
                self.name,
                _("pour le"),
                self.slot,
                _("Nom"),
                self.full_name,
                _("Commentaire"),
                self.comment,
                url
            )

            content = """
                <div style="font-family: verdana; font-size: 16px;">
                <p>{0},<p>
                <p>{1} {2} {3}</p>
                <p><strong>{4}</strong></p>
                <p>{5} : {6}</p>
                <p>{7} : {8}</p>
                <img alt="Santani Yoga" src="{9}">
                </div>
                """
            try:
                frappe.sendmail(recipients=forward_to_email, sender=email, content=content.format(*messages), subject="Réservation de "+self.full_name)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(),'email to company failed')  # Otherwise, booking is not registered in database if errors


    def on_trash(self):
        doc = frappe.get_doc("Booking Slot", self.slot)

        # set property to the document
        doc.available_places += 1

        # save a document to the database
        doc.save()


    def validate(self):

        # check available places before saving
        doc = frappe.get_doc("Booking Slot", self.slot)

        # raise error
        if doc.available_places <= 0 and doc.time_slot > now_datetime() :
            frappe.throw("""Plus de place disponible pour cette séance, vous pouvez néanmoins demander
                        à être prévenu par e-mail si une place se libère.""")

        # check if already registered
        booked = frappe.db.sql("""select COUNT(*)
                 from `tabBooking`
                 where `tabBooking`.slot = %(slot)s and `tabBooking`.email_id = %(email)s
                 and `tabBooking`.name <> %(name)s""",
                 {"slot": self.slot, "email": self.email_id, "name": self.name})[0][0]

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
