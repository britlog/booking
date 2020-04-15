// Copyright (c) 2018, Britlog and contributors
// For license information, please see license.txt

frappe.ui.form.on('Booking Subscription', {
	refresh: function(frm) {

	}
});

frappe.ui.form.on('Booking Subscription', "subscribed_classes", function(frm) {

    if(!frm.doc.start_date) {
	    frappe.msgprint("Veuillez saisir une date de début");
		return;
	}

    frappe.call({
        method: "booking.booking.doctype.booking_subscription.booking_subscription.get_remaining_classes",
        args: {
            "subscribed_classes": frm.doc.subscribed_classes,
            "subscription": frm.doc.name
        },
        callback: function(r) {
            //console.log(r.message);
            frm.set_value("remaining_classes", r.message);
        }
    });
});

frappe.ui.form.on('Booking Subscription', "allowed_catch_up", function(frm) {

    frappe.call({
        method: "booking.booking.doctype.booking_subscription.booking_subscription.get_remaining_catch_up",
        args: {
            "allowed_catch_up": frm.doc.allowed_catch_up,
            "subscription": frm.doc.name
        },
        callback: function(r) {
            //console.log(r.message);
            frm.set_value("remaining_catch_up", r.message);
        }
    });
});

//frappe.ui.form.on('Booking Subscription', "customer", function(frm) {
//    frm.add_fetch('customer','email_id','email_id');
//});