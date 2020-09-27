
frappe.ready(function() {
	// bind events here

	// load introduction text
	frappe.call({
        method: 'booking.www.reservation.get_introduction',
        args: {},
        callback: function(r) {
            if (r.message){
                $('.introduction p').html(r.message);
            };
        }
    });

	// load activities
	$('[name="type"]').empty();
	$('[name="type"]').append($('<option>').val('').text('- Toutes -'));
	frappe.call({
			method: 'booking.www.reservation.get_activities',
			args: {},
			callback: function(r) {
//				console.log(r.message);

				(r.message || []).forEach(function(row){
					$('[name="type"]').append($('<option>').val(row).text(row));
				});

			}
		});

	// load slots
    get_slots("");

	function get_slots(activity) {

		$('[name="slot"]').empty();
    	$('[name="slot"]').append($('<option>').val('').text(''));

		frappe.call({
			method: 'booking.www.reservation.get_slots',
			args: {
				'activity': activity
			},
			callback: function(r) {
//				console.log(r.message);
				var available_message = "";
				(r.message || []).forEach(function(row){
					if (row.available_places <= 0) {
						available_message = "Liste d'attente";
					}
					else if (row.available_places == 1) {
						available_message = "1 place disponible";
					}
					else {
						available_message = row.available_places+" places disponibles";
					}

					$('[name="slot"]').append($('<option>').val(row.name).text((row.time_slot_display || row.name)
						+((activity) ? '' : " | "+row.type.toUpperCase())
						+((row.location) ? ' '+row.location : '')
						+((row.is_replay) ? ' REPLAY' : '')
						+" | "+available_message)
						.attr('available_places',row.available_places).attr('subscription_places',row.subscription_places)
						.attr('practical_information',row.practical_information));

	//                if (row.available_places == 0) { $('select option:contains("'+row.name+'")').attr("disabled", "disabled"); }
				});

			}
		});
    }

    function valid_email_fr(email) {
	    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  		return re.test(email);
    }

    function valid_phone(id,mobile) {
    if (mobile)
        return (id.search("^0[6-7][0-9]{8}$")==-1) ? 0 : 1;
    else
        return (id.search("^0[1-9][0-9]{8}$")==-1) ? 0 : 1;
    }

	function display_payment() {
		// Check subscription validity if any
		frappe.call({
            method: 'booking.booking.doctype.booking.booking.get_slot_subscription',
            args: {
                'email_id': $('[name="email_id"]').val(),
                'slot_id': $('[name="slot"]').val()
            },
            callback: function(r) {
//                console.log(r.message);

				if (jQuery.isEmptyObject(r.message) || !r.message.is_valid) {

					if (r.message.price) {
						$('#amount').html("Montant à payer : "+r.message.price);
					} else {
						$('#amount').html("");
					}

					if (r.message.to_bill) {
						$("#credit-card").prop("checked", true);
						$('#credit-card-group').show();
					} else {
						$('#credit-card-group').hide();
					}

					if (r.message.allow_payment_on_site) {
						if (r.message.payment_instruction) {
							$('label[for=payment-on-site]').html(r.message.payment_instruction);
						} else {
							$('label[for=payment-on-site]').html("Paiement sur place");
						}
						if (!r.message.to_bill) {
							$("#payment-on-site").prop("checked", true);
						}
						$('#payment-on-site-group').show();
					} else {
						$('#payment-on-site-group').hide();
					}

					$('#payment-group').show();

				} else $('#payment-group').hide();
            }
        });
    }

    $('[name="slot"]').change(function () {

		  // display practical information if specified
		  if ($('[name="slot"] :selected').attr('practical_information')) {
		  	$("#practical-information").html($('[name="slot"] :selected').attr('practical_information'));
		  	$("#practical-information").toggle(true);
          }
          else {
            $("#practical-information").html('');
            $("#practical-information").toggle(false);
          }

		  // manage notification button display
          $("#notification-button").prop("disabled",false);

          if ($('[name="slot"] :selected').attr('available_places') <= 0) {
            $("#notification-button").toggle(true);		//show button
          }
          else {
            $("#notification-button").toggle(false);	//hide button
          }

		  if ($('[name="slot"] :selected').attr('subscription_places') <= 0) {
		  	frappe.msgprint("Le groupe est complet, cours à la séance uniquement.");
		  }

		  // email already entered and slot is changed => display payment based on the selected activity
		  if ($('[name="email_confirm"]').val()) {
		  	display_payment();
		  }
     })

	$('[name="type"]').change(function () {

//		  frappe.msgprint($('[name="type"]').val());
//		  $('[name="slot"]').val($('[name="slot"] option:first').val());
		  $("#notification-button").toggle(false);	//hide button

		  // reload slots
		  get_slots($('[name="type"]').val());

		  $("#practical-information").html('');
          $("#practical-information").toggle(false);

     })

    $('#notification-button').on("click", function() {
        var email = $('[name="email_id"]').val();
        var email_confirm = $('[name="email_confirm"]').val();
        var fullname = $('[name="full_name"]').val();
        var slot = $('[name="slot"]').val();

        if (!email || !valid_email_fr(email)) {
            frappe.msgprint(__("Entrez s'il vous plaît une adresse e-mail valide, sans accents ni espaces."));
            $('[name="email_id"]').focus();
            return false;
		}

		if(email != email_confirm) {
			frappe.msgprint(__("Veuillez contrôler votre adresse e-mail : les champs E-mail et Confirmation E-mail sont différents."));
            $('[name="email_confirm"]').focus();
            return false;
		}

		if (!fullname) {
            frappe.msgprint(__("Entrez s'il vous plaît votre nom."));
            $('[name="full_name"]').focus();
            return false;
		}

		frappe.call({
            method: 'booking.www.reservation.set_notification',
            args: {
                'slot': slot,
                'email': email,
                'name': fullname
            },
            callback: function(r) {
                //console.log(r.message);
                frappe.msgprint(__("Votre demande d'inscription sur la liste d'attente est bien enregistrée.\
                	Vous allez recevoir un e-mail si une place se libère."));
                $("#notification-button").prop("disabled",true);
            }
        });
    });

	$('[name="email_confirm"]').change(function () {
		  display_payment();
     })

    $('.btn-form-submit').on("click", function() {
		var slot = $('[name="slot"]').val();
		var fullname = $('[name="full_name"]').val();
		var email = $('[name="email_id"]').val();
		var email_confirm = $('[name="email_confirm"]').val();
		var city = $('[name="city"]').val();
		var phone = $('[name="phone"]').val();
		var sms = $('[name="confirm_sms"]').is(':checked');
		var comment = $('[name="comment"]').val();
		var payment = $('[name="payment"]:checked').val();

		if(!slot) {
			frappe.msgprint(__("Veuillez choisir un cours."));
            $('[name="slot"]').focus();
            return false;
		}

		if(!fullname) {
			frappe.msgprint(__("Veuillez saisir votre nom."));
            $('[name="full_name"]').focus();
            return false;
		}

		if(!valid_email_fr(email)) {
            frappe.msgprint(__("Entrez s'il vous plaît une adresse e-mail valide, sans accents ni espaces."));
            $('[name="email_id"]').focus();
            return false;
		}

		if(email != email_confirm) {
			frappe.msgprint(__("Veuillez contrôler votre adresse e-mail : les champs E-mail et Confirmation E-mail sont différents."));
            $('[name="email_confirm"]').focus();
            return false;
		}

		if(phone || sms) {
            phone = phone.replace(/\D/g,"");    // delete all non-numeric characters
            $('[name="phone"]').val(phone);
            if (!valid_phone(phone,sms)) {
                frappe.msgprint(__("Entrez s'il vous plaît un numéro de téléphone valide.\
                    Un numéro de portable est nécessaire si vous avez demandé une confirmation par SMS."));
                $('[name="phone"]').focus();
                return false;
            }
		}

		// Check subscription validity if any
		frappe.call({
            method: 'booking.booking.doctype.booking.booking.get_slot_subscription',
            args: {
                'email_id': email,
                'slot_id': $('[name="slot"]').val()
            },
            callback: function(r) {
                console.log(r.message);
                var bCancel = false

				if (!jQuery.isEmptyObject(r.message) && typeof r.message.is_valid !== 'undefined' && !r.message.is_valid) {
					// subscription is not valid, display a warning
					if (!confirm(r.message.warning_msg)) {
						bCancel = true;
					}
				}

                if (!bCancel) {
                	//Add the booking
					frappe.call({
						method: 'booking.www.reservation.add_booking',
						args: {
							'slot': slot,
							'email': email,
							'name': fullname,
							'city': city,
							'phone': phone,
							'sms': sms,
							'comment': comment,
							'payment_mode': payment
						},
						callback: function(r) {
							if (!jQuery.isEmptyObject(r.message)){

								if (r.message.payment_url) {
									// redirect to payment
									window.location.href = r.message.payment_url;
								}
								else {
									frappe.msgprint(r.message.success_message);

									//Init form
									$('[name="type"]').val('');
									get_slots("");
									$('[name="comment"]').val('');
								}
							};
						}
    				});
                }
            }
        });

    	return false;
	});

})


