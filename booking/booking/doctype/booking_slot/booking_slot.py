# -*- coding: utf-8 -*-
# Copyright (c) 2015, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BookingSlot(Document):

    def autoname(self):

        self.name = frappe.utils.format_datetime(self.time_slot,"EEEE dd/MM/yyyy HH:mm").capitalize()

    # def on_update(self):
    #
    #     # update customer subscription whether present in class or not
    #     # get all subscribers of this slot
    #     subscribers = frappe.get_all("Booking Subscriber", filters={'parent': self.name},
    #                                  fields=['subscriber', 'present'])
    #
    #     for fields in subscribers:
    #         # get subscriber's remaining classes including this class slot update
    #         doc = frappe.get_doc('Customer', fields.subscriber)
    #         doc.subscription_remaining_classes = get_remaining_classes(doc.name,doc.subscription_total_classes)
    #
    #         # save the document to the database
    #         doc.save()


@frappe.whitelist()
def refresh_available_places(slot,total_places):

    return str( int(total_places) - frappe.db.count("Booking",{"slot": ["=", slot]})
        - frappe.db.count("Booking Subscriber", {"parent": ["=", slot]}) )

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
