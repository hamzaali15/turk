import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from frappe.model.mapper import get_mapped_doc
import math

def unset_needs_approval(so, method):
	frappe.get_doc('Authorization Control').validate_approving_authority(so.doctype, so.company, so.base_grand_total, so)
	so.needs_approval = 0
	so.approval_by = ''
	for item in so.items:
		item.custom_approver_role = ''
		item.needs_approval = 0


def validate_items_rate_and_update_boxes(so, method):
	saved_item_rows = frappe.get_all("Sales Order Item", fields=["name"], filters = {"parent": so.name, "docstatus": 1})
	items_changed = len(saved_item_rows)!=len(so.items)

	if items_changed:
		set_boxes_in_items(so)
		set_total_boxes(so)
		set_average_valuation_rate(so, method)
		frappe.msgprint(_("The items for Sales Order {0} have been updated".format(so.name)))


def set_boxes_in_items(so):
	for item in so.items:
		if item.def_boxes and item.def_pieces:
			total_piece = round(item.qty / (flt(item.def_boxes) / flt(item.def_pieces)))
			new_sqm = total_piece * (flt(item.def_boxes) / flt(item.def_pieces))
			item.boxes = math.floor(round(new_sqm / flt(item.def_boxes), 4))
			item.pieces = total_piece % flt(item.def_pieces)
			item.sqm = new_sqm

		elif not item.def_boxes:
			item.boxes = item.qty
			item.pieces = item.qty
			item.sqm = item.qty
		if not item.warehouse and so.items[0].warehouse:
			item.warehouse = so.items[0].warehouse


def set_total_boxes(so):
	totalqty, totalbox, totalpieces, loosetotal = 0, 0, 0, 0
	for item in so.items:
		totalqty += item.qty
		totalbox += item.boxes
		totalpieces += item.pieces
		loosetotal += (cint(item.boxes) * cint(item.def_pieces)) + item.pieces
	so.cust_total_qty = totalqty
	so.cust_total_box = totalbox
	so.cust_total_pieces = totalpieces
	so.custom_loose_total = loosetotal


@frappe.whitelist()
def check_to_allow_delivery(so, to_create):
	so = frappe.get_doc("Sales Order", so)

	# if to_create == "Material Request":
	# 	if (not so.allow_delivery and so.advance_paid < so.rounded_total):
	# 		frappe.throw(_('Not allowed to create the Material Request before Payment'))

	if to_create == "Sales Invoice":
		if not so.allow_delivery:
			# if so.advance_paid < so.rounded_total:
			# 	frappe.throw(_('Not allowed to create the Sales Invoice before Payment'))
			# else:
			cheque_payments = frappe.db.sql("""
				select pe.name
				from `tabPayment Entry Reference` pref
				inner join `tabPayment Entry` pe on pe.name = pref.parent
				inner join `tabMode of Payment` mop on mop.name = pe.mode_of_payment
				where pref.reference_doctype = 'Sales Order' and pref.reference_name = %s and mop.name like '%%cheque%%'
				""", so.name)
			if cheque_payments:
				frappe.throw(_("Payment made by cheque. Delivery requires approval."))
	elif to_create == "Delivery Note":
		if not so.allow_delivery:
			if so.advance_paid < so.rounded_total:
				frappe.throw(_('Not allowed to create the Delivery Note before Payment'))
			else:
				cheque_payments = frappe.db.sql("""
					select pe.name
					from `tabPayment Entry Reference` pref
					inner join `tabPayment Entry` pe on pe.name = pref.parent
					inner join `tabMode of Payment` mop on mop.name = pe.mode_of_payment
					where pref.reference_doctype = 'Sales Order' and pref.reference_name = %s and mop.type = 'Bank'
				""", so.name)
				if cheque_payments:
					frappe.throw(_("Payment made by cheque. Delivery requires approval."))
	return True


def set_average_valuation_rate(so, method):
	for item in so.items:
		if not item.custom_valuation_rate:
			item_found_in_bin = frappe.get_all("Bin", filters={'item_code': item.item_code, "valuation_rate": [">", 0]}, fields=['*'])
			bin_with_same_company = []
			for bin_item in item_found_in_bin:
				bin_company = frappe.db.get_value("Warehouse", bin_item.warehouse, "company")
				if so.company == bin_company:
					bin_with_same_company.append(bin_item)

			if bin_with_same_company:
				total_valuation = 0.0
				for bin_item in bin_with_same_company:
					total_valuation += bin_item.valuation_rate
				average_valuation_rate = total_valuation / len(bin_with_same_company)
			else:
				average_valuation_rate = '0.00'
			item.custom_valuation_rate = average_valuation_rate


@frappe.whitelist()
def make_so_updation(source_name, target_doc=None):
	return get_mapped_doc("Sales Order", source_name, 	{
		"Sales Order": {
			"doctype": "Sales Order Updation",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Sales Order Item": {
			"doctype": "SO Updation Item",
			"add_if_empty": True
		}
	}, target_doc)
