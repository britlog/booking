import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_subscriptions(email_id):

    return frappe.db.sql("""
    select
        BSU.name,
        BSU.reference,
        BSU.subscribed_classes AS subscribed_classes,
        BSU.remaining_classes AS remaining_classes,
        DATE_FORMAT(BSU.start_date,%(str)s) AS start_date,
        DATE_FORMAT(BSU.end_date,%(str)s) AS end_date
    from `tabBooking Subscription` BSU
    inner join `tabCustomer` C on BSU.customer = C.name
    inner join `tabDynamic Link` DL on C.name = DL.link_name
    inner join `tabContact` CT on DL.parent = CT.name
    where CT.email_id = %(email)s and BSU.disabled = 0""",
    {"str": '%d-%m-%Y', "email": email_id},as_dict=True)

@frappe.whitelist(allow_guest=True)
def get_classes(subscription_id):

    return frappe.db.sql("""
    select
        BS.name AS slot,
        BS.type AS style,
        SUB.present
    from `tabBooking Slot` BS   
    inner join `tabBooking Subscriber` SUB on BS.name=SUB.parent
    where SUB.subscription = %(subscription)s
    order by BS.time_slot desc""",
    {"subscription": subscription_id},as_dict=True)


@frappe.whitelist(allow_guest=True)
def set_attendance(customer=""):
    print("set attendance called")
    print(customer)
    # frappe.db.sql("""
        # 	update `tabBooking Subscriber` set present = 1
        # 	where parent = %(parent)s and customer_id = %(customer)s """,
        #   {"parent": slot, "customer": fields.email_id})