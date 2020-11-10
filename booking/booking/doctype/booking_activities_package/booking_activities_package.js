// Copyright (c) 2020, Britlog and contributors
// For license information, please see license.txt

frappe.ui.form.on('Booking Activities Package', {
	refresh: function(frm) {

	}
});

// Get class_coefficient when select activity
frappe.ui.form.on('Booking Subscription Activity', "activity", function(frm) {
    frm.add_fetch('activity','class_coefficient','class_coefficient');
});