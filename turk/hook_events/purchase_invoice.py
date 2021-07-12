import frappe
from frappe import _

@frappe.whitelist()
def add_location(self, method):
    pi_doc = frappe.get_doc("Purchase Invoice", self.name)
    if pi_doc:
        for d in pi_doc.items:
            itm_doc = frappe.db.sql("""select location_name from `tabLocation Item` where parent='{0}'""".format(d.item_code))
            if itm_doc:
                d.location_name = itm_doc[0][0]