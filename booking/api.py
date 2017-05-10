import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_solde(email_id):

    return frappe.db.sql("""
    select
        IFNULL(tabCustomer.subscription_remaining_classes,0) AS classes,
        DATE_FORMAT(tabCustomer.subscription_end_date,%(str)s) AS validity,
        IFNULL(tabCustomer.subscription_total_classes,0) AS total_classes
    from `tabCustomer`
    inner join `tabDynamic Link` on tabCustomer.name=`tabDynamic Link`.link_name
    inner join `tabContact` on `tabDynamic Link`.parent=tabContact.name
    where tabContact.email_id = %(email)s""",
    {"str": '%d-%m-%Y', "email": email_id},as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_classes(email_id):

    return frappe.db.sql("""
    select
        `tabBooking Slot`.name AS cours,
        `tabBooking Slot`.type AS style,
        `tabBooking Subscriber`.present
    from `tabCustomer`
    inner join `tabDynamic Link` on tabCustomer.name=`tabDynamic Link`.link_name
    inner join `tabContact` on `tabDynamic Link`.parent=tabContact.name
    inner join `tabBooking Subscriber` on tabCustomer.name=`tabBooking Subscriber`.subscriber
    inner join `tabBooking Slot` on `tabBooking Subscriber`.parent=`tabBooking Slot`.name
    where tabContact.email_id = %(email)s and CAST(`tabBooking Slot`.time_slot AS DATE)>=tabCustomer.subscription_start_date
    order by `tabBooking Slot`.time_slot desc""",
    {"email": email_id},as_dict=True)

