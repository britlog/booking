
frappe.ready(function() {
	// bind events here

	// load introduction text
	frappe.call({
        method: 'booking.booking.web_form.class_reservation.class_reservation.get_introduction',
        args: {},
        callback: function(r) {
            if (r.message){
                $('.introduction p').html(r.message);
            };
        }
    });

	// add fields
	$('[name="email_id"]').after($('<label for="email_confirm" class="control-label text-muted small">Confirmation E-mail</label> \
    	<input class="form-control" type="email" name="email_confirm" oncopy="return false" onpaste="return false" oncut="return false">'));
    $('[name="email_confirm"]').after($('<br><input class="btn btn-primary" type="button" id="notification-button" value="S\'inscrire sur la liste d\'attente">'));
    $("#notification-button").toggle(false);	//hide button

	// load activities
	$('[name="type"]').empty();
	$('[name="type"]').append($('<option>').val('').text('- Toutes -'));
	frappe.call({
			method: 'booking.booking.web_form.class_reservation.class_reservation.get_activities',
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
			method: 'booking.booking.web_form.class_reservation.class_reservation.get_slots',
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

					$('[name="slot"]').append($('<option>').val(row.name).text((row.time_slot_display || row.name)+" | "+((activity) ? '' : row.type.toUpperCase()+" | ")+available_message)
					.attr('available_places',row.available_places).attr('subscription_places',row.subscription_places));

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

    $('[name="slot"]').change(function () {

          $("#notification-button").prop("disabled",false);

//		  console.log($('[name="slot"] :selected').attr('available_places'));
          if ($('[name="slot"] :selected').attr('available_places') <= 0) {
            $("#notification-button").toggle(true);		//show button
          }
          else {
            $("#notification-button").toggle(false);	//hide button
          }

		  if ($('[name="slot"] :selected').attr('subscription_places') <= 0) {
		  	frappe.msgprint("Le groupe est complet, cours à la séance uniquement.");
		  }

     })

	$('[name="type"]').change(function () {

//		  frappe.msgprint($('[name="type"]').val());
//		  $('[name="slot"]').val($('[name="slot"] option:first').val());
		  $("#notification-button").toggle(false);	//hide button
		  get_slots($('[name="type"]').val());

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
            method: 'booking.booking.web_form.class_reservation.class_reservation.set_notification',
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


    clickListener = jQuery._data($('.btn-form-submit')[0], 'events').click[0]; // caching the first .click bind
    $('.btn-form-submit').off('click'); // removing all binds
    $('.btn-form-submit').text('Envoyer');    // rename button

    $('.btn-form-submit').on("click", function() {
		var email = $('[name="email_id"]').val();
		var email_confirm = $('[name="email_confirm"]').val();
		var phone = $('[name="phone"]').val();
		var sms = $('[name="confirm_sms"]').is(':checked');

		if(email && !valid_email_fr(email)) {
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

		// Check if catch up class is allowed or display a warning message
		frappe.call({
            method: 'booking.booking.doctype.booking.booking.get_slot_subscription',
            args: {
                'email_id': email,
                'slot_id': $('[name="slot"]').val()
            },
            callback: function(r) {
//                console.log(r.message);
                var bCancel = false

				if (r.message && !r.message.is_valid) {
					// subscription is not valid, display a warning
					if (!confirm(r.message.warning_msg)) {
						bCancel = true;
					}
				}

                if (!bCancel) {
                	$('.btn-form-submit').off('click');                 // removing all binds
					$('.btn-form-submit').click(clickListener.handler); // rebind click event for saving
					$('.btn-form-submit').triggerHandler('click');      // save
                }
            }
        });

		return false;
	});

})


