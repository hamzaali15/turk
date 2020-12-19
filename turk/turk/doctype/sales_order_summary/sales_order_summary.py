# -*- coding: utf-8 -*-
# Copyright (c) 2020, RC and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.desk.form.linked_with import get_linked_doctypes
from frappe.utils import flt
from collections import defaultdict


class SalesOrderSummary(Document):
	pass


@frappe.whitelist()
def get_related_documents(doctype, docname):
	document_details = defaultdict(list)
	si_list = []
	linked_doc_info = get_linked_doctypes(doctype)
	document_details[doctype].append(frappe.get_doc(doctype, docname).as_dict())

	# also consider the sales return
	for linked_doctype in ["Sales Order", "Material Request", "Stock Entry", "Delivery Note", "Sales Invoice", "Payment Entry"]:
		link = linked_doc_info.get(linked_doctype)
		filters = [[link.get('child_doctype', linked_doctype), link.get("fieldname")[0], '=', docname]]
		if link.get("doctype_fieldname"):
			filters.append([link.get('child_doctype'), link.get("doctype_fieldname"), "=", doctype])

		if linked_doctype == "Payment Entry":
			filters.append(["Payment Entry", "docstatus", "=", 1])

		names = frappe.get_all(linked_doctype, fields="name", filters=filters, distinct=1)

		for doc in names:
			doc_obj = frappe.get_doc(linked_doctype, doc.name)

			if linked_doctype == "Sales Invoice":
				si_list.append(doc_obj.name)

			if linked_doctype == "Sales Invoice" and doc_obj.is_return:
				document_details["Sales Return"].append(doc_obj.as_dict())
			else:
				document_details[linked_doctype].append(doc_obj.as_dict())

	for so in document_details["Sales Order"]:
		for d in so.get("items"):
			d.remaining_qty = flt(d.qty) - (flt(d.delivered_qty) + flt(d.returned_qty))

	# include the Payment Entry against invoice
	pe_names = map(lambda d: d.name, document_details["Payment Entry"] or [])
	if si_list:
		payment_entry = frappe.db.sql(
			'''select distinct parent as name from `tabPayment Entry Reference` where docstatus=1 and reference_name in (%s)''' %
			', '.join(['%s'] * len(si_list)), tuple(si_list), as_dict=1)
		for pe in payment_entry:
			if pe.name not in pe_names:
				pe_doc = frappe.get_doc("Payment Entry", pe.name).as_dict()
				document_details["Payment Entry"].append(pe_doc)

	# remove payment references to other documents and calculate total paid
	positive_payment_total = 0
	negative_payment_total = 0
	for pe in document_details["Payment Entry"]:
		new_list = []
		for pref in pe.references:
			if (pref.reference_doctype == doctype and pref.reference_name == docname) \
					or (pref.reference_doctype == "Sales Invoice" and pref.reference_name in si_list):
				new_list.append(pref)

				if flt(pref.allocated_amount) < 0:
					negative_payment_total -= flt(pref.allocated_amount)
				else:
					positive_payment_total += flt(pref.allocated_amount)
		pe.references = new_list

	sales_order_total = document_details["Sales Order"][0].rounded_total
	sales_return_total = -sum(map(lambda d: d.rounded_total, document_details["Sales Return"])) if "Sales Return" in document_details else 0.0
	total_outstanding_amount = positive_payment_total - negative_payment_total - sales_order_total + sales_return_total

	document_details["Sales Order"][0].total_payment_amount = positive_payment_total
	document_details["Sales Order"][0].total_refund_amount = negative_payment_total
	document_details["Sales Order"][0].total_return_amount = sales_return_total
	document_details["Sales Order"][0].total_outstanding_amount = total_outstanding_amount

	return document_details

