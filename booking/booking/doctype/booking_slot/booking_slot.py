# -*- coding: utf-8 -*-
# Copyright (c) 2015, Britlog and contributors
# For license information, please see license.txt

from __future__ import print_function
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BookingSlot(Document):

    def autoname(self):
        self.name = frappe.utils.format_datetime(self.time_slot,"EEEE dd/MM/yyyy HH:mm").capitalize()

    # def on_update(self):
    #     # send notification email if customer ask for warning
    #     if int(self.available_places) > 0:
    #         send_notification_email(self.name)


@frappe.whitelist()
def refresh_available_places(slot,total_places,nb_subscribers):

    return str( int(total_places)
          # - frappe.db.count("Booking",{"slot": ["=", slot], "cancellation_date": ""})
          - frappe.db.sql("""select COUNT(*) from `tabBooking` where slot = %(slot)s and cancellation_date is null""",
                        {"slot": slot})[0][0]
          - int(nb_subscribers)
    )

@frappe.whitelist()
def update_customers(slot):

    # get all subscribers of this slot
    subscribers = frappe.get_all("Booking Subscriber", filters={'parent': slot},
                                 fields=['subscriber', 'present'])

    for fields in subscribers:
        # get subscriber's remaining classes including this class slot update
        doc = frappe.get_doc('Customer', fields.subscriber)
        doc.subscription_remaining_classes = get_remaining_classes(doc.name,doc.subscription_total_classes,doc.subscription_start_date)

        # save the Customer Doctype to the database
        doc.save()

@frappe.whitelist()
def get_remaining_classes(customer_id,total_classes,start_date):

    if not total_classes:
        total_classes=0

    classes = int(total_classes) - frappe.db.sql("""select COUNT(*)
        from `tabBooking Subscriber`
        inner join `tabBooking Slot` on `tabBooking Subscriber`.parent=`tabBooking Slot`.name
        where `tabBooking Subscriber`.subscriber = %(customer)s and present = 1
        and CAST(`tabBooking Slot`.time_slot AS DATE)>=%(subscription_date)s""",
        {"customer": customer_id , "subscription_date": start_date })[0][0]

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

    return max(0,classes)

def send_notification_email():
    """
        Send email to customer who ask to be warned for available places
    """

    notifications = frappe.db.sql("""select distinct BS.name AS slot, BN.email_id
            from `tabBooking Slot` BS
            inner join `tabBooking Notification` BN on BS.name = BN.parent
            where BS.time_slot > NOW() and BS.available_places > 0 and BN.sending_date is null""", as_dict=True)

    if notifications:
        url = frappe.utils.get_url("/reservation")

        for fields in notifications:
            messages = (
                "Bonjour",
                "Une place vient de se libérer pour le cours de yoga du",
                fields.slot,
                "Je vous invite à vous inscrire sur la",
                url,
                "Si le cours est déjà complet, c'est que la place vient d'être réservée et il faut vous réinscrire à l'alerte car cet e-mail n'est envoyé qu'une seule fois.",
                "Namasté"
            )

            content = """
                <div style="font-family: verdana; font-size: 16px;">
                <p>{0},<p>
                <p>{1} <strong>{2}</strong>.</p>
                <p>{3} <a href="{4}">page réservation</a>.</p>
                <p>{5}</p>
                <p>{6},<br>Tonya</p>
                </div>
                """
            try:
                frappe.sendmail(fields.email_id, subject="Cours de yoga du "+fields.slot, content=content.format(*messages))
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), 'notification email failed')

            frappe.db.sql("""
                update `tabBooking Notification` set sending_date = NOW()
                where parent = %(parent)s and email_id = %(email)s and sending_date is null """,
                {"parent": fields.slot,"email":fields.email_id})