from __future__ import unicode_literals


import frappe
from frappe import  _
from frappe.defaults import get_user_default_as_list
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.model.mapper import get_mapped_doc
from frappe.core.doctype.sms_settings.sms_settings import send_sms
from frappe.utils import nowdate, flt, cstr, today, nowtime

from erpnext.controllers.queries import get_doctype_wise_filters, get_fields
import json
from collections import defaultdict

# import frappe.utils
# from frappe.utils import cstr, flt, getdate, cint, nowdate, add_days, get_link_to_form, strip_html
# from six import string_types
# from frappe.model.utils import get_fetch_values
# from frappe.model.mapper import get_mapped_doc
# from erpnext.stock.stock_balance import update_bin_qty, get_reserved_qty
# from frappe.desk.notifications import clear_doctype_notifications
# from frappe.contacts.doctype.address.address import get_company_address
# from erpnext.controllers.selling_controller import SellingController
# from frappe.automation.doctype.auto_repeat.auto_repeat import get_next_schedule_date
# from erpnext.selling.doctype.customer.customer import check_credit_limit
# from erpnext.stock.doctype.item.item import get_item_defaults
# from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
# from erpnext.manufacturing.doctype.production_plan.production_plan import get_items_for_material_requests
# from erpnext.accounts.doctype.sales_invoice.sales_invoice import validate_inter_company_party, update_linked_doc,\
# 	unlink_inter_company_doc


@frappe.whitelist()
def get_item_details(args):
	"""
		custom script for returning the stock information for a item

	Parameters
	----------
	txt: search text string
	item_code: item_code,
	customer: frm.doc.customer,
	update_stock: frm.doc.update_stock,
	company: frm.doc.company,
	order_type: frm.doc.order_type,
	transaction_date: frm.doc.transaction_date,
	doctype: frm.doc.doctype,
	name: frm.doc.name


	Return
	------
	dict of warehouse wise all stocks

	"""
	if isinstance(args, str):
		args = json.loads(args)

	args = frappe._dict(args)
	item_list = []

	if args.item_code:
		# if item code is given only search for the given field
		item_code = args.item_code
		item_warehouse = frappe.db.get_value("Item", item_code, "default_warehouse")
		user_default_warehouse_list = get_user_default_as_list('Warehouse')
		user_default_warehouse = user_default_warehouse_list[0]if len(user_default_warehouse_list) == 1 else ""
		warehouse = user_default_warehouse or item_warehouse or args.warehouse
		item_list = [item_code]

	else:
		# search the given items from the seach fields
		# doctype, txt, searchfield, start, page_len, filters, as_dict=False
		items = custom_item_query("Item", args.txt, "name", 0, 50, {"is_sales_item": 1}, True)
		item_dict =	{d.name: ", ".join(d.values()) for d in items}
		item_list = item_dict.keys()

	custom_uom_info = frappe.get_all("Item", fields=["name", "boxes", "pieces"],
		filters=[["name", "in", item_list]])

	out = defaultdict(dict)
	for item in custom_uom_info:
		out[item.name] = {}
		out[item.name]["item_details"] = item_dict[item.name]
		out[item.name]["item_stock_totals"] = {"actual_qty": 0, "reserved_qty": 0}
		out[item.name]["uom_box"] = item.boxes
		out[item.name]["uom_pieces"] = item.pieces
		out[item.name]["warehouse_details"] = {}

	# for item in item_list:
	# 	out[item] = {}
	# 	out[item]["item_details"] = item_dict[item]
	# 	out[item]["item_stock_totals"] = {"actual_qty": 0, "reserved_qty": 0}


	# filters["filters"].push(["Warehouse", "rejected_warehouse", "!=", 1]);
	warehouses = frappe.db.get_all("Warehouse", fields=["name"], filters=[["company", "=", args.company], ["rejected_warehouse", "!=", 1]])
	warehouses_list = [warehouse.name for warehouse in warehouses]

	item_details = frappe.db.get_all("Bin", fields=["item_code", "warehouse", "actual_qty", "projected_qty", "reserved_qty"],
						filters=[["item_code", "in", item_list], ["warehouse", "in", warehouses_list]])


	for item in item_details:
		out[item.item_code]["warehouse_details"][item.warehouse] = item
		out[item.item_code]["warehouse_details"][item.warehouse]["uom_box"] = out[item.item_code]["uom_box"]
		out[item.item_code]["warehouse_details"][item.warehouse]["uom_pieces"] = out[item.item_code]["uom_pieces"]

		# out[item.item_code]["item_details"] = item_dict[item.item_code]
		# if "item_stock_totals" not in out[item.item_code]:
		# 	out[item.item_code].update({"item_stock_totals": {"actual_qty": 0, "reserved_qty": 0}})

		out[item.item_code]["item_stock_totals"]["actual_qty"] += item.actual_qty
		out[item.item_code]["item_stock_totals"]["reserved_qty"] += item.reserved_qty

	# item_details = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse},
	# 		["projected_qty", "actual_qty"], as_dict=True) \
	# 		or {"projected_qty": 0, "actual_qty": 0}

	# out.update({warehouse: item_details})

	return out




def custom_item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	namesearch = '('
	for strparam in txt.split("%"):
		namesearch += " tabItem.item_name like '%" + strparam +"%' and"
	namesearch = namesearch.rsplit(' ', 1)[0]
	namesearch += ' )'

	conditions = []

	return frappe.db.sql("""
	select tabItem.name, tabItem.item_name as item_name, tabItem.item_group
	from tabItem
	left join tabBin on tabBin.item_code = tabItem.name
	where tabItem.docstatus < 2
		and tabItem.has_variants=0
		and tabItem.disabled=0
		and (tabItem.end_of_life > %(today)s or ifnull(tabItem.end_of_life, '0000-00-00')='0000-00-00')
		and (tabItem.`{key}` LIKE %(txt)s
			or tabItem.item_group LIKE %(txt)s
			or  {namesearch}
			)
		{fcond} {mcond}
	group by tabItem.name
	order by
		sum(ifnull(tabBin.actual_qty - tabBin.reserved_qty, 0)) desc,
		if(locate(%(_txt)s, tabItem.name), locate(%(_txt)s, tabItem.name), 99999),
		if(locate(%(_txt)s, tabItem.item_name), locate(%(_txt)s, tabItem.item_name), 99999),
		tabItem.idx desc,
		tabItem.name, tabItem.item_name
	limit %(start)s, %(page_len)s """.format(
		key=searchfield,
		fcond=get_filters_cond(doctype, filters, conditions).replace('%', '%%'),
		mcond=get_match_cond(doctype).replace('%', '%%'),namesearch=namesearch.replace('%', '%%')),
		{
			"today": nowdate(),
			"txt": "%%%s%%" % txt,
			"_txt": txt.replace("%", ""),
			"start": start,
			"page_len": page_len
		}, as_dict=as_dict)




@frappe.whitelist()
def warehouse_query(doctype, txt, searchfield, start, page_len, filters):
	# Should be used when item code is passed in filters.
	conditions, bin_conditions = [], []
	filter_dict = get_doctype_wise_filters(filters)

	sub_query = """ select round(`tabBin`.actual_qty, 2) from `tabBin`
		where `tabBin`.warehouse = `tabWarehouse`.name
		{bin_conditions} """.format(
		bin_conditions=get_filters_cond(doctype, filter_dict.get("Bin"),
			bin_conditions, ignore_permissions=True))
		# CONCAT_WS(" : ", "Actual Qty", ifnull( ({sub_query}), 0) ) as actual_qty

	query = """select `tabWarehouse`.name,
		ifnull( ({sub_query}), 0) as custom_qty
		from `tabWarehouse`
		where
		   `tabWarehouse`.`{key}` like '{txt}'
			{fcond} {mcond}
		order by
			custom_qty desc
		limit
			{start}, {page_len}
		""".format(
			sub_query=sub_query,
			key=frappe.db.escape(searchfield),
			fcond=get_filters_cond(doctype, filter_dict.get("Warehouse"), conditions),
			mcond=get_match_cond(doctype),
			start=start,
			page_len=page_len,
			txt=frappe.db.escape('%{0}%'.format(txt))
		)

	return frappe.db.sql(query)


'''

txt: m
searchfield: name
query: erpnext.controllers.queries.item_query
filters: {"is_sales_item":1}
doctype: Item

'''

def set_item_so_detail(item):
	so_detail = frappe.db.sql_list("""
						select name
						from `tabSales Order Item`
						where docstatus = 1 and parent = %s and item_code = %s
					""", [item.sales_order, item.item_code])

	if not so_detail:
		frappe.throw(_("Row {0}: Item {1} can not be found in Sales Order {2}").format(
			item.idx, item.item_code, item.sales_order))

	item.so_detail = so_detail[-1]


@frappe.whitelist()
def update_item_qty_based_on_sales_order(items):
	from six import string_types
	import json
	if isinstance(items, string_types):
		items = json.loads(items)

	out = {}

	for item in items:
		item = frappe._dict(item)
		if item.qty > 0:
			if item.sales_order:
				row = {}
				if not item.so_detail:
					set_item_so_detail(item)
					row['so_detail'] = item.so_detail

				so_item = frappe.get_value("Sales Order Item", item.so_detail, ["qty", "rate"], as_dict=1)
				if not so_item:
					frappe.msgprint("Row {0}: Ignoring Item {1}. Could not find Sales Order Item in {2}".format(
						item.idx, item.item_code, item.sales_order))

				row['rate'] = so_item.rate

				invoiced_qty = frappe.db.sql("""
					select sum(item.qty)
					from `tabSales Invoice Item` item
					inner join `tabSales Invoice` si on si.name = item.parent
					where si.docstatus < 2 and si.is_return != 1 and item.so_detail = %s and item.parent != %s
				""", [item.so_detail, item.parent])
				invoiced_qty = invoiced_qty[0][0] if invoiced_qty else 0
				invoiced_qty = flt(invoiced_qty)

				remaining_qty = max(0, so_item.qty - invoiced_qty)
				if remaining_qty< flt(item.qty):
					row['qty'] = remaining_qty

				out[item.name] = row

	return out

@frappe.whitelist()
def get_qrcode_image(item_code):
	import pyqrcode
	code = pyqrcode.create(item_code)
	image_as_str = code.png_as_base64_str(scale=5)
	return image_as_str


@frappe.whitelist()
def get_last_item_price(item_code,price_list):
	item_price_list = frappe.db.get_all('Item Price',
		fields = ['name', 'price_list_rate'], filters = {'item_code': item_code,'price_list': price_list})
	if item_price_list:
		return item_price_list[-1]


@frappe.whitelist()
def warehouse_query(doctype, txt, searchfield, start, page_len, filters):
	# Should be used when item code is passed in filters.
	conditions, bin_conditions = [], []
	filter_dict = get_doctype_wise_filters(filters)

	query = """select `tabWarehouse`.name,
		CONCAT_WS(" : ", "Actual Qty", ifnull(round(`tabBin`.actual_qty, 2), 0 )) actual_qty
		from `tabWarehouse` left join `tabBin`
		on `tabBin`.warehouse = `tabWarehouse`.name {bin_conditions}
		where
			`tabWarehouse`.`{key}` like {txt}
			{fcond} {mcond}
		order by ifnull(`tabBin`.actual_qty, 0) desc
		limit
			{start}, {page_len}
		""".format(
			bin_conditions=get_filters_cond(doctype, filter_dict.get("Bin"),bin_conditions, ignore_permissions=True),
			key=searchfield,
			fcond=get_filters_cond(doctype, filter_dict.get("Warehouse"), conditions),
			mcond=get_match_cond(doctype),
			start=start,
			page_len=page_len,
			txt=frappe.db.escape('%{0}%'.format(txt))
		)

	return frappe.db.sql(query)


@frappe.whitelist()
def get_total_item_qty(company, item_code):
	warehouses = frappe.db.get_all("Warehouse", fields=["name"], filters=[["company", "=", company], ["rejected_warehouse", "!=", 1]])
	warehouses_list = [warehouse.name for warehouse in warehouses]

	item_in_warehouses = frappe.db.get_all("Bin", fields=["item_code", "actual_qty", "reserved_qty"],
						filters=[["item_code", "=", item_code], ["warehouse", "in", warehouses_list]])
	total_available_qty = 0
	for item in item_in_warehouses:
		total_available_qty += item.actual_qty - item.reserved_qty

	return total_available_qty


@frappe.whitelist()
def ts_make_purchase_receipt(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty) - flt(obj.received_qty)
		target.received_qty = target.qty
		target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
		target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
		target.base_amount = (flt(obj.qty) - flt(obj.received_qty)) * \
			flt(obj.rate) * flt(source_parent.conversion_rate)

	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	doc = get_mapped_doc("Purchase Order", source_name,	{
		"Purchase Order": {
			"doctype": "Purchase Receipt",
			"field_map": {
				"per_billed": "per_billed",
				"supplier_warehouse":"supplier_warehouse"
			},
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		"Purchase Order Item": {
			"doctype": "Purchase Receipt Item",
			"field_map": {
				"name": "purchase_order_item",
				"parent": "purchase_order",
				"bom": "bom",
				"material_request": "material_request",
				"material_request_item": "material_request_item"
			},
			"postprocess": update_item,
			"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
		},
		"Purchase Taxes and Charges": {
			"doctype": "Purchase Taxes and Charges",
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

	return doc


@frappe.whitelist()
def ts_make_purchase_order(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty) - flt(obj.received_qty)
		target.received_qty = target.qty
		target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
		target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
		target.base_amount = (flt(obj.qty) - flt(obj.received_qty)) * \
			flt(obj.rate) * flt(source_parent.conversion_rate)

	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	doc = get_mapped_doc("Sales Order", source_name,	{
		"Sales Order": {
			"doctype": "Purchase Order",
			"field_map": {
				"per_billed": "per_billed",
				"supplier_warehouse":"supplier_warehouse",
				"inter_company_order_reference": ""
			},
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		"Sales Order Item": {
			"doctype": "Purchase Order Item",
			"field_map": {
				"name": "sales_order_item",
				"parent": "sales_order",
				"bom": "bom",
				"material_request": "material_request",
				"material_request_item": "material_request_item"
			},
			"postprocess": update_item,
			"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
		},
		"Purchase Taxes and Charges": {
			"doctype": "Purchase Taxes and Charges",
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)
	doc.inter_company_order_reference = None	
	return doc


@frappe.whitelist()
def get_delivered_qty(sales_order, item_code, so_item_row):
	'''
		returns qty of item in sales order items that needs to be delivered yet,
		considering submitted as well as draft invoices.

		:param sales_order: str, Doctype - Sales Order, Field - name
		:param item_code: str, Doctype - Sales Order Item, Field - item_code
		:so_item_row: str, Doctype: - Sales Order Item, Field - name
	'''

	sales_order = frappe.get_doc("Sales Order", sales_order)

	invoices = frappe.get_all("Sales Invoice", filters = {"cust_sales_order_number": sales_order.name, "docstatus": ["<", 2], 'is_return': 0})
	delivered_qty = 0
	for invoice in invoices:
		sales_invoice = frappe.get_doc("Sales Invoice", invoice.name)
		for item in sales_invoice.items:
			if item.item_code == item_code and item.so_detail == so_item_row:
				delivered_qty += item.qty
	return delivered_qty

@frappe.whitelist()
def make_payment(salaryslipname):
	salaryslip = frappe.get_doc("Salary Slip",salaryslipname)
	deduction_account = frappe.get_value("Account",{"company":salaryslip.company,"account_number":22610})
	doc = frappe.new_doc("Payment Entry")
	doc.update(
		{"company":salaryslip.company,
		"payment_type":"Pay",
		"salary_slip_id":salaryslipname,
		"party_type": "Employee",
		"party":salaryslip.employee,
		"paid_to":deduction_account,
		"paid_amount":salaryslip.rounded_total,
		"deductions":[{"account":deduction_account,"amount":salaryslip.rounded_total}]
		})

	doc.setup_party_account_field()
	doc.set_missing_values()
	doc.set_exchange_rate()

	return doc.as_dict()


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty = abs(flt(source_doc.qty))
		target_doc.boxes = abs(int(source_doc.boxes))
		target_doc.pieces = abs(int(source_doc.pieces))
		target_doc.sqm = abs(flt(source_doc.sqm))

	doc = get_mapped_doc("Sales Invoice", source_name, {
		"Sales Invoice": {
			"doctype": "Stock Entry",
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Sales Invoice Item": {
			"doctype": "Stock Entry Detail",
			"field_map": {
				"stock_qty": "transfer_qty"
			},
			"postprocess": update_item
		}
	}, target_doc)

	return doc


@frappe.whitelist()
def ts_make_sales_invoice(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty)
		target.received_qty = target.qty
		target.stock_qty = flt(obj.qty) * flt(obj.conversion_factor)
		target.amount = flt(obj.qty) * flt(obj.rate)
		target.base_amount = flt(obj.qty) * flt(obj.rate) * flt(source_parent.conversion_rate)

		expense_account = frappe.db.get_values("Company", source_parent.company, ["default_expense_account"])[0]
		item_expense_account = frappe.db.get_value("Item Default", {'parent': target.item_code, 'company': source_parent.company}, ["expense_account"])
		target.expense_account = item_expense_account or expense_account

	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	doc = get_mapped_doc("Purchase Invoice", source_name,	{
		"Purchase Invoice": {
			"doctype": "Sales Invoice",
			"field_map": {
				"per_billed": "per_billed",
				"supplier_warehouse":"supplier_warehouse",
			},
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		"Purchase Invoice Item": {
			"doctype": "Sales Invoice Item",
			"field_map": {
				"name": "purchase_invoice_item",
				"parent": "purchase_invoice",
				"bom": "bom",
				"material_request": "material_request",
				"material_request_item": "material_request_item"
			},
			"postprocess": update_item,
			# "condition": lambda doc: abs(doc.received_qty) < abs(doc.qty)
		},
		"Purchase Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)
	return doc


def send_followup_sms(opportunity, method):
	def validate_number(number_list):
		validated_number_list=[]
		for n in number_list:
			if '03' == n[:2]:
				n = '92' + n[1:]
			if '923' != n[:3] or len(n) != 12:
				frappe.throw(_("Phone Number is not Valid to Send SMS in Follow Up Table.  Please Check number again."))
			validated_number_list.append(n)
		return validated_number_list

	for d in opportunity.followup:
		if d.send_message and not d.message_sent and len(d.sms_message) > 10:
			if not d.sms_message and d.send_message:
				frappe.throw(_("Please set SMS Message Row no {0}").format(d.idx))
			number_list = []
			if d.owner_sms_cell:
				number_list.append(d.owner_sms_cell)
			if d.architect_sms_cell:
				number_list.append(d.architect_sms_cell)
			if d.contractor_cell_no:
				number_list.append(d.contractor_cell_no)
			if number_list:
				if len(d.sms_message) > 305:
					frappe.throw(_("Message Length should be less than 2 Messages (305 characters) ."))
				number_list = validate_number(set(number_list))
				send_sms(number_list, cstr(d.sms_message),opportunity.company)
				d.message_sent = 1
				d.db_update()


@frappe.whitelist()
def address_query(doctype, txt, searchfield, start, page_len, filters):
	conditions = []
	fields = ['name','address_line1', 'city', 'country']
	fields = get_fields("Address", fields)
	searchfields = frappe.get_meta("Address").get_search_fields()
	searchfields = " or ".join([field + " like %(txt)s" for field in searchfields])
	return frappe.db.sql("""select {fields} from `tabAddress`
		where docstatus < 2
			and ({scond}) and disabled=0
			{fcond} {mcond}
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			idx desc,
			address_title
		limit %(start)s, %(page_len)s""".format(**{
			"fields": ", ".join(fields),
			"scond": searchfields,
			"mcond": get_match_cond(doctype),
			"fcond": get_filters_cond(doctype, filters, conditions).replace('%', '%%'),
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})


@frappe.whitelist()
def get_sales_order_items(sales_order):
	sales_order_items = frappe.get_all("Sales Order Item", fields=["name"], filters = {"parent": sales_order, "docstatus": 1})
	return sales_order_items

@frappe.whitelist()
def change_pi_status(self, method):
	pi_doc = frappe.get_doc("Purchase Invoice", self.purchase_invoice)
	if pi_doc:
		if pi_doc.docstatus == 1:
			if self.total_qty == pi_doc.total_qty:
					pi_doc.delivery_status = "Completed"
					pi_doc.db_update()

@frappe.whitelist()
def add_location(self, method):
	for d in self.items:
		location_name = ""
		itm_doc = frappe.db.sql("""select location_name from `tabLocation Item` where parent='{0}'""".format(d.item_code))
		if itm_doc:
			location_name += str(itm_doc)
			d.location_name = location_name