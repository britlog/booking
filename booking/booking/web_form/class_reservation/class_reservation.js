
frappe.ready(function() {
	// bind events here

    // load slots
    $('[name="slot"]').empty()
    $('[name="slot"]').append($('<option>').val('').text(''));
    $('[name="slot"]').after($('<input class="btn btn-default" type="button" id="notification-button" value="Prévenez-moi lorsqu\'une place se libère">'));
    $("#notification-button").prop("disabled",true);
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
                if (row.available_places == 0) {
                    available_message = "Complet";
                }
                else if (row.available_places == 1) {
                    available_message = "1 place disponible";
                }
                else {
                    available_message = row.available_places+" places disponibles";
                }
                $('[name="slot"]').append($('<option>').val(row.name).text(row.name+" | "+row.type.toUpperCase()+" | "+available_message));

//                if (row.available_places == 0) { $('select option:contains("'+row.name+'")').attr("disabled", "disabled"); }
            });

        }
    });

    function valid_phone(id,mobile) {
    if (mobile)
        return (id.search("^0[6-7][0-9]{8}$")==-1) ? 0 : 1;
    else
        return (id.search("^0[1-9][0-9]{8}$")==-1) ? 0 : 1;
    }

    $('[name="slot"]').change(function () {
          var str = "";
          $('#notification-button').prop('value', 'Prévenez-moi lorsqu\'une place se libère');

          $("select option:selected").each(function () {
                str += $(this).text() + " ";
              });

          if (str.search("Complet") != -1) {
            $("#notification-button").prop("disabled",false);
          }
          else {
            $("#notification-button").prop("disabled",true);
          }
     })

    $('#notification-button').on("click", function() {
        var email = $('[name="email_id"]').val();
        var slot = $('[name="slot"]').val();

        if (!email || !valid_email(email)) {
            frappe.msgprint(__("Entrez s'il vous plaît une adresse e-mail valide."));
            $('[name="email_id"]').focus();
            return false;
		}

		frappe.call({
            method: 'booking.booking.web_form.class_reservation.class_reservation.set_notification',
            args: {
                'slot': slot,
                'email': email
            },
            callback: function(r) {
                //console.log(r.message);
                $('#notification-button').prop('value', 'Demande de notification enregistrée');
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

		if(email && !valid_email(email)) {
            frappe.msgprint(__("Entrez s'il vous plaît une adresse e-mail valide."));
            $('[name="email_id"]').focus();
            return false;
		}

		if(phone || sms) {
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


