// Get class_coefficient when select activity
frappe.ui.form.on('Booking Subscription Activity', "activity", function(frm) {
    frm.add_fetch('activity','class_coefficient','class_coefficient');
});