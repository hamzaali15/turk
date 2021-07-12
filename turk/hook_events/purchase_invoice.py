import frappe
from frappe import _

@frappe.whitelist()
def add_location(self, method):
    for d in self.items:
        itm_doc = frappe.db.sql("""select location_name from `tabLocation Item` where parent='{0}'""".format(d.item_code))
        if itm_doc:
            d.location_name = itm_doc[0][0]