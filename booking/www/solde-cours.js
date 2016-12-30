
frappe.ready(function() {

	$("#solde").on("submit", function() {
		return false;
	});

	$("#update").click(function() {
		var args = {
			email_id : $("#customer_id").val()
		}

		if(!args.email_id) {
			frappe.msgprint("Votre adresse email est obligatoire")
			return;
		}

		frappe.call({
			method: 'booking.api.get_solde',
			args: args,
			callback: function(r) {
				if(r.message) {
                    console.log(r.message);
                    var remaining_classes = r.message[0].classes;
                    var validity_date = r.message[0].validity;
                    //frappe.msgprint("Il vous reste "+num.toString()+" cours");
                    msgprint("Il vous reste "+remaining_classes.toString()+" cours à suivre jusqu'au "+validity_date);
                }
                else msgprint("Adresse email non reconnue, veuillez contacter Santani Yoga");

                if(r.exc) {
                    frappe.msgprint(r.exc);
                }

			}
     	});

     	frappe.call({
			method: 'booking.api.get_classes',
			args: args,
			callback: function(r) {
				if(r.message) {
                    console.log(r.message);

					var tableData = '<tr>'
					tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;">Historique des cours</th>'
					tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;">Style</th>'
					tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;text-align: center;">Présence</th>'
					tableData+='</tr>';
                    (r.message || []).forEach(function(row){
							tableData += '<tr>';
							tableData += '<td>' + row.cours + '</td>';
							tableData += '<td>' + row.style + '</td>';
							if (row.present)
								tableData += '<td style="text-align: center;"><i class="fa fa-check-square-o" aria-hidden="true"></i></td>';
							else
								tableData += '<td style="text-align: center;"><i class="fa fa-square-o" aria-hidden="true"></i></td>';
							tableData += '</tr>';
					});
					$('#matable').html(tableData).toggle(true);
                }
                else $('#matable').toggle(false);

                if(r.exc) {
                    frappe.msgprint(r.exc);
                }

			}
     	});

        return false;
	});
});