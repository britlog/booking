// Copyright (c) 2016, Britlog and contributors
// For license information, please see license.txt

frappe.ui.form.on('Booking Slot', {
	refresh: function(frm) {

	}
});

frappe.ui.form.on('Booking Slot', "total_places", function(frm) {

    frappe.call({
            method: "booking.booking.doctype.booking_slot.booking_slot.refresh_available_places",
            args: {
                "slot": frm.doc.name,
                "total_places": frm.doc.total_places
            },
            callback: function(r) {
                //frappe.msgprint(r.message);
                frm.doc.available_places = r.message;
                refresh_field("available_places");
            }
    });

});

frappe.ui.form.on('Booking Subscriber', {
    subscribers_remove: function(frm) {
        frm.doc.available_places += 1;
        refresh_field("available_places");

    },
    subscribers_add: function(frm) {
        frm.doc.available_places -= 1;
        refresh_field("available_places");
    }
});

//frappe.ui.form.on("Booking Subscriber", "present", function(frm,cdt,cdn) {
//    var customer = frappe.get_doc(cdt, cdn);
//    frappe.msgprint(customer.subscriber);
//
//    frappe.call({
//            method: "booking.api.update_remaining_classes",
//            args: {
//                "customer_id": customer.subscriber
//            },
//            callback: function(r) {
//                //frappe.msgprint(r.message);
//            }
//    });
//
//});
