// Copyright (c) 2016, Britlog and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Attendance Sheet"] = {
	"filters": [
        {
            "fieldname":"slot",
            "label": __("Slot"),
            "fieldtype": "Link",
            "options": "Booking Slot",
            "reqd": 1,
            "get_query": function() {
                console.log(frappe.datetime.get_today());
				return{
					filters: {
						'time_slot': [">=", frappe.datetime.get_today()]
					}
				};
			}
        }
	]
}
