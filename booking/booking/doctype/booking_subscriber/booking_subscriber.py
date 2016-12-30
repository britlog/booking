# -*- coding: utf-8 -*-
# Copyright (c) 2015, Britlog and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BookingSubscriber(Document):

	def on_update(self):
		print("BOOKING SUBSCRIBER TOTOTOTOTOTOTOTOTOTOTOTOTOTOTOTOTOTOTOTOTOTO")