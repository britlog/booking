# -*- coding: utf-8 -*-
# Copyright (c) 2015, Britlog and contributors
# For license information, please see license.txt

from __future__ import print_function
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from booking.booking.doctype.booking_notification.booking_notification import trigger_notification

class BookingSlot(Document):

    def autoname(self):
        self.name = frappe.utils.format_datetime(self.time_slot,"EEEE dd/MM/yyyy HH:mm").capitalize()

    def validate(self):
        trigger_notification(self)

    def on_update(self):
        pass

@frappe.whitelist()
def update_subscriptions(slot):

    # get all subscribers of this slot
    subscribers = frappe.get_all("Booking Subscriber", filters=[["parent", "=", slot], ["subscription","!=", ""]],
                                 fields=['subscription'])
    for row in subscribers:
        # get subscription remaining classes including this class slot update
        doc = frappe.get_doc('Booking Subscription', row.subscription)
        doc.remaining_classes = get_remaining_classes(doc.subscribed_classes, doc.name)

        # save the Subscription Doctype to the database
        doc.save()

    # get all bookings of this slot
    bookings = frappe.get_all("Booking Class", filters=[["parent", "=", slot], ["subscription", "!=", ""]],
                                 fields=['subscription'])
    for row in bookings:
        # get subscription remaining classes including this class slot update
        doc = frappe.get_doc('Booking Subscription', row.subscription)
        doc.remaining_classes = get_remaining_classes(doc.subscribed_classes, doc.name)

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
