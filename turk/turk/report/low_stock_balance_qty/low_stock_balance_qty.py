# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition

def execute(filters=None):
	if not filters: filters = {}

	validate_filters(filters)

	columns = get_columns()
	items = get_items(filters)
	sle = get_stock_ledger_entries(filters, items)

	# if no stock ledger entry found return
	if not sle:
		return columns, []

	iwb_map = get_item_warehouse_map(filters, sle)
	dataitems = {}
	for (company,item, warehouse) in sorted(iwb_map):
		warehouse_item = iwb_map[(company,item, warehouse)]
		key = (company,item)
		if key not in dataitems:
			dataitems[key] = frappe._dict({
				"opening_qty": 0.0,
				"in_qty": 0.0,
				"out_qty": 0.0,
				"bal_qty": 0.0,
				"val_rate": 0.0
			})
		dataitems[key].opening_qty += warehouse_item.opening_qty
		dataitems[key].in_qty += warehouse_item.in_qty
		dataitems[key].out_qty += warehouse_item.out_qty
		dataitems[key].bal_qty += warehouse_item.bal_qty
		dataitems[key].val_rate += warehouse_item.val_rate

	iwb_map = dataitems

	item_map = get_item_details(items, sle, filters)
	reserved_stock = get_company_reserved_stock(filters)

	data = []
	for (company,item) in sorted(iwb_map):
		if item_map.get(item):
			qty_dict = iwb_map[(company,item)]

			availble_qty = (qty_dict.bal_qty - reserved_stock[item]["reserved_qty"])

			boxes = 1
			pieces = 1
			if item_map[item]["boxes"] == boxes:
				boxes = availble_qty
			else:
				boxes = availble_qty/item_map[item]["boxes"]

			if item_map[item]["pieces"] == pieces:
				pieces = 0
			else:
				pieces = (availble_qty/(item_map[item]["boxes"]/item_map[item]["pieces"]))%item_map[item]["pieces"]

			report_data = [item, item_map[item]["item_name"],
				item_map[item]["item_group"],
				item_map[item]["brand"],item_map[item]["bin_location"],item_map[item]["size"],
				item_map[item]["default_supplier"],
				item_map[item]["cust_supplier_name"],
				item_map[item]["stock_uom"], qty_dict.opening_qty,
				qty_dict.in_qty,
				qty_dict.out_qty,
				qty_dict.bal_qty,
				reserved_stock[item]["reserved_qty"],
				availble_qty,
				boxes,
				pieces,
				company
			]

			if filters.get('show_variant_attributes', 0) == 1:
				variants_attributes = get_variants_attributes()
				report_data += [item_map[item].get(i) for i in variants_attributes]

			data.append(report_data)

	if filters.get('show_variant_attributes', 0) == 1:
		columns += ["{}:Data:100".format(i) for i in get_variants_attributes()]

	return columns, data

def get_columns():
	"""return columns"""

	columns = [
		_("Item")+":Link/Item:100",
		_("Item Name")+"::150",
		_("Item Group")+":Link/Item Group:100",
		_("Brand")+":Link/Brand:90",
		_("Bin Location")+":Link/Warehouse:90",
		_("Size")+"::90",
		_("Supplier Code")+":Link/Supplier:100",
		_("Supplier")+"::140",
		_("Stock UOM")+":Link/UOM:90",
		_("Opening Qty")+":Float:100",
	#	_("Opening Value")+":Float:110",
		_("In Qty")+":Float:80",
	#	_("In Value")+":Float:80",
		_("Out Qty")+":Float:80",
	#	_("Out Value")+":Float:80",
		_("Balance Qty(SQM)")+":Float:100",
		_("Hold Qty(SQM)")+":Float:100",
		_("Available Qty(SQM)")+":Float:100",
	#	_("Valuation Rate")+":Float:90",
		_("Boxes")+":Int:60",
		_("Pieces")+":Int:60",
		_("Company")+":Link/Company:100"
	]

	return columns

def get_conditions(filters):
	conditions = ""
	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))

	if filters.get("to_date"):
		conditions += " and sle.posting_date <= %s" % frappe.db.escape(filters.get("to_date"))
	else:
		frappe.throw(_("'To Date' is required"))

	#if filters.get("company"):
	#	warehouse_details = frappe.db.get_value("Warehouse",
	#		filters.get("warehouse"), ["lft", "rgt"], as_dict=1)
	if filters.get("company"):
		conditions += " and sle.warehouse in (select name from `tabWarehouse` wh \
			where rejected_warehouse!=1 and company='%s')"%(filters.get("company"))

	return conditions

def get_stock_ledger_entries(filters, items):
	item_conditions_sql = ''
	if items:
		item_conditions_sql = ' and sle.item_code in ({})'\
			.format(', '.join([frappe.db.escape(i, percent=False) for i in items]))

	conditions = get_conditions(filters)

	return frappe.db.sql("""
		select
			sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
			sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference
		from
			`tabStock Ledger Entry` sle force index (posting_sort_index)
		where sle.docstatus < 2 %s %s
		order by sle.posting_date, sle.posting_time, sle.name""" %
		(item_conditions_sql, conditions), as_dict=1)

def get_item_warehouse_map(filters, sle):
	iwb_map = {}
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))

	for d in sle:
		key = (d.company, d.item_code, d.warehouse)
		if key not in iwb_map:
			iwb_map[key] = frappe._dict({
				"opening_qty": 0.0, "opening_val": 0.0,
				"in_qty": 0.0, "in_val": 0.0,
				"out_qty": 0.0, "out_val": 0.0,
				"bal_qty": 0.0, "bal_val": 0.0,
				"val_rate": 0.0
			})

		qty_dict = iwb_map[(d.company, d.item_code, d.warehouse)]

		if d.voucher_type == "Stock Reconciliation":
			qty_diff = flt(d.qty_after_transaction) - qty_dict.bal_qty
		else:
			qty_diff = flt(d.actual_qty)

		value_diff = flt(d.stock_value_difference)

		if d.posting_date < from_date:
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff

		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if qty_diff > 0:
				qty_dict.in_qty += qty_diff
				qty_dict.in_val += value_diff
			else:
				qty_dict.out_qty += abs(qty_diff)
				qty_dict.out_val += abs(value_diff)

		qty_dict.val_rate = d.valuation_rate
		qty_dict.bal_qty += qty_diff
		qty_dict.bal_val += value_diff

	iwb_map = filter_items_with_no_transactions(iwb_map)

	return iwb_map

def filter_items_with_no_transactions(iwb_map):
	for (company, item, warehouse) in sorted(iwb_map):
		qty_dict = iwb_map[(company, item, warehouse)]

		no_transactions = True
		float_precision = cint(frappe.db.get_default("float_precision")) or 3
		for key, val in qty_dict.items():
			val = flt(val, float_precision)
			qty_dict[key] = val
			if key != "val_rate" and val:
				no_transactions = False

		if no_transactions:
			iwb_map.pop((company, item, warehouse))

	return iwb_map

def get_items(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("brand"):
			conditions.append("item.brand=%(brand)s")
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))

	items = []
	if conditions:
		items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
			.format(" and ".join(conditions)), filters)
	return items

def get_company_reserved_stock(filters):

	reserved_items = []
	reserved_items = frappe.db.sql("""select item_code,sum(reserved_qty)reserved_qty from tabBin
		where warehouse in (select name from tabWarehouse where company='%s' and rejected_warehouse!=1)
		group by item_code """ %(filters.get("company")), as_dict=1)
	order_reserved_items = {}
	for ritems in reserved_items:
		order_reserved_items.setdefault(ritems.item_code, ritems)
	return order_reserved_items

def get_item_details(items, sle, filters):
	item_details = {}
	if not items:
		items = list(set([d.item_code for d in sle]))

	if items:
		for item in frappe.db.sql("""
			select name, item_name, description,default_supplier, cust_supplier_name, item_group, brand, bin_location, size ,stock_uom , boxes, pieces
			from `tabItem`
			where name in ({0}) and ifnull(disabled, 0) = 0
			""".format(', '.join([frappe.db.escape(i, percent=False) for i in items])), as_dict=1):
				item_details.setdefault(item.name, item)

	if filters.get('show_variant_attributes', 0) == 1:
		variant_values = get_variant_values_for(item_details.keys())
		item_details = {k: v.update(variant_values.get(k, {})) for k, v in item_details.items()}

	return item_details

def validate_filters(filters):
	if not (filters.get("item_code") or filters.get("company")):
		sle_count = flt(frappe.db.sql("""select count(name) from `tabStock Ledger Entry`""")[0][0])
		if sle_count > 500000:
			frappe.throw(_("Please set filter based on Item"))

def get_variants_attributes():
	'''Return all item variant attributes.'''
	return [i.name for i in frappe.get_all('Item Attribute')]

def get_variant_values_for(items):
	'''Returns variant values for items.'''
	attribute_map = {}
	for attr in frappe.db.sql('''select parent, attribute, attribute_value
		from `tabItem Variant Attribute` where parent in (%s)
		''' % ", ".join(["%s"] * len(items)), tuple(items), as_dict=1):
			attribute_map.setdefault(attr['parent'], {})
			attribute_map[attr['parent']].update({attr['attribute']: attr['attribute_value']})

	return attribute_map