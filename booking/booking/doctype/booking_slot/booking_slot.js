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
    var nb_subscribers = 0;
    var nb_bookings = 0;

    //calculate nb_subscribers
    $.each(frm.doc.subscribers || [], function(i, subscriber) {
		if (!subscriber.cancellation_date) {
		    nb_subscribers += 1;
		}
	});

    //calculate nb_bookings
    $.each(frm.doc.bookings || [], function(i, booking) {
		if (!booking.cancellation_date) {
		    nb_bookings += 1;
		}
	});

	frm.set_value("available_places", frm.doc.total_places - nb_subscribers - nb_bookings);

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

frappe.ui.form.on('Booking Class', {
    bookings_remove: function(frm) {
        frm.trigger("total_places");
        CustomerClassesUpdate = true;
    },
    bookings_add: function(frm) {
        frm.trigger("total_places");
        CustomerClassesUpdate = true;
    }
});

frappe.ui.form.on("Booking Subscriber", "present", function(frm,cdt,cdn) {

	var row = locals[cdt][cdn];
	if (!row.subscription) {
		frappe.msgprint("Veuillez renseigner un abonnement");
		row.present = false;
		refresh_field("subscribers");
	}
	else
    	CustomerClassesUpdate = true;   //Refresh event will be triggered on saving form

});

frappe.ui.form.on("Booking Class", "present", function(frm,cdt,cdn) {

	var row = locals[cdt][cdn];
	if (!row.subscription) {
		frappe.msgprint("Veuillez renseigner un abonnement");
		row.present = false;
		refresh_field("bookings");
	}
	else
    	CustomerClassesUpdate = true;   //Refresh event will be triggered on saving form

});

frappe.ui.form.on("Booking Subscriber", "cancellation_date", function(frm,cdt,cdn) {
    frm.trigger("total_places");
});

frappe.ui.form.on("Booking Class", "cancellation_date", function(frm,cdt,cdn) {
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

		frm.set_query("subscription", "bookings", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];

			return {
				filters: {
                	"customer": row.subscriber,
                	"disabled": 0
            	}
			};
		});
});
