// Copyright (c) 2016, Britlog and contributors
// For license information, please see license.txt

var CustomerClassesUpdate = false;  //Update customer remaining classes if present is checked

frappe.ui.form.on('Booking Slot', {
	refresh: function(frm) {
        if (CustomerClassesUpdate) {
            //frappe.msgprint("REFRESH");
            frappe.call({
                method: "booking.booking.doctype.booking_slot.booking_slot.update_subscriptions",
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

frappe.ui.form.on('Booking Slot', "type", function(frm) {
    frm.add_fetch('type','default_places','total_places');
});

frappe.ui.form.on('Booking Slot', "total_places", function(frm) {
    var tbl = frm.doc.subscribers || [];
    var nb_subscribers = 0;

    //calculate nb_subscribers
    $.each(tbl || [], function(i, subscriber) {
		if (!subscriber.cancellation_date) {
		    nb_subscribers += 1;
		}
	});

    frappe.call({
            method: "booking.booking.doctype.booking_slot.booking_slot.refresh_available_places",
            args: {
                "slot": frm.doc.name,
                "total_places": frm.doc.total_places,
                "nb_subscribers": nb_subscribers //tbl.length
            },
            callback: function(r) {
                //frappe.msgprint(r.message);
                //frm.doc.available_places = r.message;
                //refresh_field("available_places");
                frm.set_value("available_places", r.message);
            }
    });

});

frappe.ui.form.on('Booking Subscriber', {
    subscribers_remove: function(frm) {
//		frm.doc.available_places += 1;
//		refresh_field("available_places");
        frm.trigger("total_places");
        CustomerClassesUpdate = true;
    },
    subscribers_add: function(frm) {
//        frm.doc.available_places -= 1;
//        refresh_field("available_places");
        frm.trigger("total_places");
        CustomerClassesUpdate = true;
    }
});

frappe.ui.form.on("Booking Subscriber", "present", function(frm,cdt,cdn) {
    CustomerClassesUpdate = true;   //Refresh event will be triggered on saving form
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

frappe.ui.form.on("Booking Subscriber", "cancellation_date", function(frm,cdt,cdn) {
    frm.trigger("total_places");
});

frappe.ui.form.on('Booking Slot', "time_slot", function(frm) {
    frm.trigger("total_places");    // force calculation in case of duplicate time_slot
});

// Filter subscriptions in child table
frappe.ui.form.on("Booking Slot", "onload", function(frm, cdt, cdn) {

		frm.set_query("subscription", "subscribers", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];

			return {
				filters: {
                	"customer": row.subscriber,
                	"disabled": 0
            	}
			};
		});
});
