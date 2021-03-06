# -*- coding: utf-8 -*-
# Copyright (c) 2015, Britlog and contributors
# For license information, please see license.txt

from __future__ import print_function
from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from booking.booking.doctype.booking_notification.booking_notification import trigger_notification
from booking.booking.doctype.booking_subscription.booking_subscription import update_subscriptions
from booking.booking.doctype.booking.booking import update_booking_status

class BookingSlot(Document):

    # def autoname(self):
    #     location = " " + self.location if self.location else ""
    #     self.name = frappe.utils.format_datetime(self.time_slot,"EEEE dd/MM/yyyy HH:mm").capitalize() + location

    def validate(self):
        if frappe.session['user'] != 'Guest':
            self.time_slot_display = frappe.utils.format_datetime(self.time_slot, "EEEE dd/MM/yyyy HH:mm").capitalize()

        trigger_notification(self)

    def on_update(self):
        update_subscriptions(self.name)
        update_booking_status(self.name)
