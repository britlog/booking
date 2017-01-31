// Copyright (c) 2016, Britlog and contributors
// For license information, please see license.txt

var CustomerClassesUpdate = false;  //Update customer remaining classes if present is checked

frappe.ui.form.on('Booking Slot', {
	refresh: function(frm) {
        if (CustomerClassesUpdate) {
            //frappe.msgprint("REFRESH");
            frappe.call({
                method: "booking.booking.doctype.booking_slot.booking_slot.update_customers",
                args: {
                    "slot": frm.doc.name
                },
                callback: function(r) {
                    //frappe.msgprint(r.message);
                }
            });
            CustomerClassesUpdate = false;
        }
	}
});


frappe.ui.form.on('Booking Slot', "total_places", function(frm) {
    var tbl = frm.doc.subscribers || [];

    frappe.call({
            method: "booking.booking.doctype.booking_slot.booking_slot.refresh_available_places",
            args: {
                "slot": frm.doc.name,
                "total_places": frm.doc.total_places,
                "nb_subscribers": tbl.length
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
        CustomerClassesUpdate = true;

    },
    subscribers_add: function(frm) {
        frm.doc.available_places -= 1;
        refresh_field("available_places");
        CustomerClassesUpdate = true;
    }
});

frappe.ui.form.on("Booking Subscriber", "present", function(frm,cdt,cdn) {
    CustomerClassesUpdate = true;
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

});
