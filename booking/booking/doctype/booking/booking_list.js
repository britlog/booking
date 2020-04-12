frappe.listview_settings['Booking'] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		if(doc.status == "Draft") {
			return [__("Draft"), "darkgrey", "status,=,Draft"];
		}
		else if(doc.status == "Payment Ordered") {
			return [__("Payment Ordered"), "green", "status,=,Payment Ordered"];
		}
		else if(doc.status == "Confirmed") {
			return [__("Confirmed"), "blue", "status,=,Confirmed"];
		}
		else if(doc.status == "Cancelled") {
			return [__("Cancelled"), "orange", "status,=,Cancelled"];
		}
	}	
}
