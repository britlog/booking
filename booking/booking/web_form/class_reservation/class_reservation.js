
frappe.ready(function() {
	// bind events here

    // load slots
    $('[name="slot"]').empty()
    $('[name="slot"]').append($('<option>').val('').text(''));
    frappe.call({
        method: 'booking.booking.web_form.class_reservation.class_reservation.get_slot',
        args: {
            //'type': 'Vinyasa'
        },
        callback: function(r) {
                //console.log(r.message);
                var options = [];
                var pluriel = "";
                (r.message || []).forEach(function(row){
                    if (row.available_places>1) { pluriel = "s"; } else { pluriel = ""; }
                    $('[name="slot"]').append($('<option>').val(row.name).text(row.name+" | "+row.type.toUpperCase()+" | "+row.available_places+" place"+pluriel+" disponible"+pluriel));
                    //$('select option:contains("'+row.name+'")').text(row.name+" "+row.type+" - "+row.available_places+" PLACES DISPONIBLES");
                });

            }
    });

    function valid_phone(id,mobile) {
        if (mobile)
            return (id.search("(0|\\+33|0033)[6-7][0-9]{8}")==-1) ? 0 : 1;
        else
            return (id.search("(0|\\+33|0033)[1-9][0-9]{8}")==-1) ? 0 : 1;
    }

    clickListener = jQuery._data($('.btn-form-submit')[0], 'events').click[0]; // caching the first .click bind
    $('.btn-form-submit').off('click'); // removing all binds

    $('.btn-form-submit').on("click", function() {
		var email = $('[name="email_id"]').val();
		var phone = $('[name="phone"]').val();
		var sms = $('[name="confirm_sms"]').is(':checked');

		if(email && !valid_email(email)) {
            frappe.msgprint(__("Entrez s'il vous plaît une adresse e-mail valide."));
            $('[name="email_id"]').focus();
            return false;
		}

		if(phone && !valid_phone(phone,sms)) {
            frappe.msgprint(__("Entrez s'il vous plaît un numéro de téléphone valide.\
                Un numéro de portable est nécessaire si vous avez demandé une confirmation par SMS."));
            $('[name="phone"]').focus();
            return false;
		}

        $('.btn-form-submit').off('click');                 // removing all binds
        $('.btn-form-submit').click(clickListener.handler); // rebind click event for saving
        $('.btn-form-submit').triggerHandler('click');      // save

		return false;
	});

})


