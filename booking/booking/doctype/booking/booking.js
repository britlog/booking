// Copyright (c) 2016, Britlog and contributors
// For license information, please see license.txt

//frappe.ui.form.on("Booking", {
//	slot: function(frm, cdt, cdn) {
//		var res = frappe.model.get_doc(cdt, cdn);
//		if (res.slot) {
//			// if slot, get stock
//			frappe.call({
//				method: "booking.booking.doctype.booking.booking.get_stock",
//				args: {
//					slot: res.slot
//				},
//				callback: function(r) {
//					frappe.model.set_value(cdt, cdn, "stock", r.message);
//				}
//			});
//
//		} else {
//			// if no slot, clear stock
//			frappe.model.set_value(cdt, cdn, "stock", null);
//		}
// 	},
//});

//frappe.ui.form.on("Booking", "onload", function(frm) {
//    cur_frm.set_query("slot", function() {
//        return {
//            "filters": {
//                'type': 'Vinyasa'
//            }
//        };
//    });
//
//    cur_frm.fields_dict['slot'].get_query = function(doc, cdt, cdn) {
//        return {
//            filters:{'type': 'Détente'}
//        }
//    };
//});


//frappe.form.link_formatters['Booking Slot'] = function(value, doc) {
//    frappe.msgprint(value+' TOTO');
//	return value+' TOTO';
//
//};
//refresh_field("slot");