
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

    // load slots
    $('[name="slot"]').empty()
    $('[name="slot"]').append($('<option>').val('').text(''));
    $('[name="slot"]').after($('<input class="btn btn-primary" type="button" id="notification-button" value="S\'inscrire sur la liste d\'attente">'));
    //$("#notification-button").prop("disabled",true);
    $("#notification-button").toggle(false);	//hide button

    frappe.call({
        method: 'booking.booking.web_form.class_reservation.class_reservation.get_slot',
        args: {
            //'type': 'Vinyasa'
        },
        callback: function(r) {
            //console.log(r.message);
            var options = [];
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
                $('[name="slot"]').append($('<option>').val(row.name).text(row.name+" | "+row.type.toUpperCase()+" | "+available_message)
                .attr('available_places',row.available_places).attr('subscription_places',row.subscription_places));

//                if (row.available_places == 0) { $('select option:contains("'+row.name+'")').attr("disabled", "disabled"); }
            });

        }
    });

    function valid_email_fr(id) {
	    return (id.toLowerCase().search("^[a-z0-9._-]+@[a-z0-9._-]{2,}\.[a-z]{2,4}$")==-1) ? 0 : 1;
    }

    function valid_phone(id,mobile) {
    if (mobile)
        return (id.search("^0[6-7][0-9]{8}$")==-1) ? 0 : 1;
    else
        return (id.search("^0[1-9][0-9]{8}$")==-1) ? 0 : 1;
    }

    $('[name="slot"]').change(function () {

          $("#notification-button").prop("disabled",false);

          if ($("select option:selected").attr('available_places') <= 0) {
            $("#notification-button").toggle(true);		//show button
          }
          else {
            $("#notification-button").toggle(false);	//hide button
          }

		  if ($("select option:selected").attr('subscription_places') <= 0) {
		  	frappe.msgprint("Le groupe est complet, cours à la séance uniquement.");
		  }


     })

    $('#notification-button').on("click", function() {
        var email = $('[name="email_id"]').val();
        var fullname = $('[name="full_name"]').val();
        var slot = $('[name="slot"]').val();

        if (!email || !valid_email_fr(email)) {
            frappe.msgprint(__("Entrez s'il vous plaît une adresse e-mail valide, sans accents ni espaces."));
            $('[name="email_id"]').focus();
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
		var phone = $('[name="phone"]').val();
		var sms = $('[name="confirm_sms"]').is(':checked');

		if(email && !valid_email_fr(email)) {
            frappe.msgprint(__("Entrez s'il vous plaît une adresse e-mail valide, sans accents ni espaces."));
            $('[name="email_id"]').focus();
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

        $('.btn-form-submit').off('click');                 // removing all binds
        $('.btn-form-submit').click(clickListener.handler); // rebind click event for saving
        $('.btn-form-submit').triggerHandler('click');      // save

		return false;
	});

})


