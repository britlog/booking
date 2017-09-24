// Copyright (c) 2016, Britlog and contributors
// For license information, please see license.txt

frappe.query_reports["Attendance Sheet"] = {
	"filters": [
        {
            "fieldname":"slot",
            "label": __("Time Slot"),
            "fieldtype": "Link",
            "options": "Booking Slot",
            "reqd": 1,
            "get_query": function() {
//                console.log(frappe.datetime.get_today());
				return {
					filters: {
						'time_slot': [">=", frappe.datetime.get_today()]
					}
				};
			}
        }
	]
}
