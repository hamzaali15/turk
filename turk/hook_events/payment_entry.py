import frappe
from frappe import _



def validate_sales_order(pe, method):
	for reference in pe.references:
		if reference.reference_doctype in ["Sales Invoice", "Sales Order"]:
			if reference.reference_doctype == "Sales Invoice":
				so = frappe.db.get_value("Sales Invoice", reference.reference_name, "cust_sales_order_number")
			elif reference.reference_doctype == "Sales Order":
				so = reference.reference_name
			if reference.sales_order != so:
				reference.sales_order = so

@frappe.whitelist()
def get_party_primary_role(party_type, party):
	doc = frappe.get_list('Party Link', filters={ party_type: party }, fields= "primary_role")
	if doc:
		return doc[0].primary_role