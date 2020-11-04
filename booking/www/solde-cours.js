
frappe.ready(function() {

	$("#solde").on("submit", function() {
		return false;
	});

	$("#update").click(function() {

		//init
		$('[id="subscriptions"]').toggle(false);
		$('#matable').toggle(false);
		$("#contact-alert").toggle(false);

		var args = {
			email_id : $("#customer_id").val()
		}

		if(!args.email_id) {
			frappe.msgprint("Votre adresse email est obligatoire");
			return;
		}

		frappe.call({
			method: 'booking.booking.doctype.booking_subscription.booking_subscription.get_subscriptions',
			args: args,
			callback: function(r) {
//				console.log(r.message);
				if (!jQuery.isEmptyObject(r.message)) {
					$("#contact-alert").toggle(false);
					$('[id="subscriptions"]').toggle(true);
					$('[id="subscriptions"]').empty();
					$('[id="subscriptions"]').append($('<option>').val('').text("{{ _("Pick a subscription") }}"));
					(r.message || []).forEach(function(row){
						$('[id="subscriptions"]').append($('<option>').val(row.name).text(row.name+" du "+row.start_date
							+" | "+row.subscribed_classes+" cours | "+(row.reference || ''))
						.attr('remaining_classes',row.remaining_classes)
						.attr('remaining_catch_up',row.remaining_catch_up)
						.attr('end_date',row.end_date));
					});
				}
				else {
					msgprint("Aucun abonnement trouvé avec cette adresse e-mail");
				}

				if(r.exc) {
					frappe.msgprint(r.exc);
				}
			}
     	});

        return false;
	});

	$('[id="subscriptions"]').change(function () {

		//console.log(r.message);
		if ( $("select option:selected").val() ) {
			var remaining_classes = $("select option:selected").attr('remaining_classes');
			var remaining_catch_up = $("select option:selected").attr('remaining_catch_up');
			var validity_date = $("select option:selected").attr('end_date');

			if(!validity_date)
				validity_date = "";
			else validity_date = " jusqu'au "+validity_date;

			//frappe.msgprint("Il vous reste "+num.toString()+" cours");
			var subscription_status = "Il vous reste "+remaining_classes.toString()+" cours "+validity_date;
			if (remaining_catch_up != 0) {
				subscription_status += ", dont "+remaining_catch_up.toString()+" en rattrapage";
			}
			msgprint_alert(subscription_status);

			//print detail classes table
			frappe.call({
				method: 'booking.booking.doctype.booking_subscription.booking_subscription.get_classes',
				args: {
            		'subscription_id': $("select option:selected").val()
        		},
				callback: function(r) {
					if(r.message) {
//						console.log(r.message);

						var tableData = '<tr>'
						tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;">Historique des cours</th>'
						tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;">Activité</th>'
						tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;text-align: center;">Réservation</th>'
						tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;text-align: center;">Présence</th>'
						tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;text-align: center;">Annulation</th>'
						tableData+='<th bgcolor="#FFD996" style="padding: 15px;border: 1px solid black;text-align: center;">Lien YouTube</th>'
						tableData+='</tr>';
						(r.message || []).forEach(function(row){
								tableData += '<tr>';
								tableData += '<td>' + (row.time_slot_display || row.slot) + '</td>';
								tableData += '<td style="text-align: center;">' + row.style + '</td>';
								tableData += '<td style="text-align: center;">' + row.booking_no + '</td>';
								if (row.present) {
									tableData += '<td style="text-align: center;"><i class="fa fa-check-square-o" aria-hidden="true"></i>';
									if (row.class_coefficient != 1)
										tableData += ' / ' + row.class_coefficient
									tableData += '</td>';
								} else
									tableData += '<td style="text-align: center;"><i class="fa fa-square-o" aria-hidden="true"></i></td>';

								if (row.cancellation_date) {
									tableData += '<td style="text-align: center;">' + row.cancellation_date;
									if (row.present)
										tableData += '<br>(Hors délai)'
									tableData += '</td>';
								} else if (row.is_cancelable) {
									var CurrentDate = new Date();
									var TimeSlotDate = new Date(row.time_slot.replace(/\s/, 'T'));

									// add class cancellation period
									// Finally allow cancellation till the class to free up places
									//if (row.cancellation_period > 0)
									//	CurrentDate.setHours( CurrentDate.getHours() + row.cancellation_period );

									if (TimeSlotDate > CurrentDate)
										tableData += '<td style="text-align: center;padding: 5px;"><input class="btn btn-primary" type="button" id="'+ row.slot +'" \
												 value="Signaler une absence" onclick="cancel_class(this.id,\''+row.booking_no+'\');"></td>';
									else
										tableData += '<td></td>';
								} else
									tableData += '<td></td>';

								if (row.streaming_link)
									tableData += '<td style="text-align: center;padding: 5px;"><a class="btn btn-primary" href="'+row.streaming_link+'" target="_blank">VOIR LA VIDEO</a></td>';
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
		}
		else {
			$("#contact-alert").toggle(false);
			$('#matable').toggle(false);
		}
	});
});