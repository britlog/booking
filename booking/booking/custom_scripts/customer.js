// Copyright (c) 2016, Britlog and contributors
// For license information, please see license.txt


frappe.ui.form.on('Customer', "subscription_total_classes", function(frm) {
    frappe.call({
            method: "booking.booking.doctype.booking_slot.booking_slot.get_remaining_classes",
            args: {
                "customer_id": frm.docname,
                "total_classes": frm.doc.subscription_total_classes,
                "start_date": frm.doc.subscription_start_date
            },
            callback: function(r) {
                //console.log(r.message);
                frm.set_value("subscription_remaining_classes", r.message);
            }
    });
});