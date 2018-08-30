from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Bookings"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Booking",
					"description": _("Web Bookings."),
				},
				{
					"type": "doctype",
					"name": "Booking Slot",
					"description": _("Booking Slots."),
				},
				{
					"type": "doctype",
					"name": "Booking Subscription",
					"description": _("Subscriptions."),
				},
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Attendance Sheet"
				},
			]
		},
		{
			"label": _("Setup"),
			"icon": "fa fa-cog",
			"items": [
				{
					"type": "doctype",
					"name": "Booking Settings",
					"description": _("Default settings for booking transactions.")
				},
				{
					"type": "doctype",
					"name": "Booking Type",
					"description": _("Booking Type."),
				},
			]
		},
	]
