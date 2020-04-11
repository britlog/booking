frappe.listview_settings['Booking'] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		if(doc.status == "Payment Ordered") {
			return [__("Payment Ordered"), "darkgrey", "status,=,Payment Ordered"];
		}
		else if(doc.status == "Confirmed") {
			return [__("Confirmed"), "green", "status,=,Confirmed"];
		}
		else if(doc.status == "Cancelled") {
			return [__("Cancelled"), "orange", "status,=,Cancelled"];
		}
	}	
}
