# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from erpnext.stock.utils import get_incoming_rate
from erpnext.controllers.queries import get_match_cond
from frappe.utils import flt, cint


def execute(filters=None):
	if not filters: filters = frappe._dict()
	filters.currency = frappe.get_cached_value('Company',  filters.company,  "default_currency")

	gross_profit_data = GrossProfitGenerator(filters)

	data = []

	group_wise_columns = frappe._dict({
		"sales_order": ["parent", "customer", "customer_group", "transaction_date","item_code", "item_name","item_group", "brand", "description", \
			"warehouse", "qty", "base_rate", "buying_rate", "base_amount",
			"buying_amount", "gross_profit", "gross_profit_percent"],
			})

	columns = get_columns(group_wise_columns, filters)

	for src in gross_profit_data.grouped_data:
		row = []
		for col in group_wise_columns.get(scrub(filters.group_by)):
			row.append(src.get(col))

		row.append(filters.currency)
		data.append(row)

	return columns, data


def get_columns(group_wise_columns, filters):
	columns = []
	column_map = frappe._dict({
		"parent": _("Sales Order") + ":Link/Sales Order:120",
		"transaction_date": _("Transaction Date") + ":Date:100",
		"item_code": _("Item Code") + ":Link/Item:100",
		"item_name": _("Item Name") + ":Data:100",
		"item_group": _("Item Group") + ":Link/Item Group:100",
		"brand": _("Brand") + ":Link/Brand:100",
		"description": _("Description") +":Data:100",
		"warehouse": _("Warehouse") + ":Link/Warehouse:100",
		"qty": _("Qty") + ":Float:80",
		"base_rate": _("Avg. Selling Rate") + ":Currency/currency:100",
		"buying_rate": _("Buying Rate") + ":Currency/currency:100",
		"base_amount": _("Selling Amount") + ":Currency/currency:100",
		"buying_amount": _("Buying Amount") + ":Currency/currency:100",
		"gross_profit": _("Gross Profit") + ":Currency/currency:100",
		"gross_profit_percent": _("Gross Profit %") + ":Percent:100",
		"sales_person": _("Sales person"),
		"allocated_amount": _("Allocated Amount") + ":Currency/currency:100",
		"customer": _("Customer") + ":Link/Customer:100",
		"customer_group": _("Customer Group") + ":Link/Customer Group:100",
		"territory": _("Territory") + ":Link/Territory:100"
	})

	for col in group_wise_columns.get(scrub(filters.group_by)):
		columns.append(column_map.get(col))

	columns.append({
		"fieldname": "currency",
		"label" : _("Currency"),
		"fieldtype": "Link",
		"options": "Currency",
		"hidden": 1
	})

	return columns


class GrossProfitGenerator(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters)

		self.load_invoice_items()
		self.process()

	def process(self):
		self.grouped = {}
		self.grouped_data = []
		self.currency_precision = cint(frappe.db.get_default("currency_precision")) or 3
		self.float_precision = cint(frappe.db.get_default("float_precision")) or 2
		for row in self.si_list:
			row.base_amount = flt(row.base_net_amount, self.currency_precision)
			if row.custom_valuation_rate:
				row.buying_amount = flt(row.custom_valuation_rate) * row.qty
				row.buying_rate = flt(row.custom_valuation_rate)

			else:
				row.buying_amount = 0
				row.buying_rate = 0.0
			row.gross_profit = flt(row.base_amount - row.buying_amount, self.currency_precision)
			if row.base_amount:
				row.gross_profit_percent = flt((row.gross_profit / row.base_amount) * 100.0, self.currency_precision)
			else:
				row.gross_profit_percent = 0.0
			if row.qty:
				row.base_rate = flt(row.base_amount / row.qty, self.float_precision)
			self.grouped.setdefault(row.get(scrub(self.filters.group_by)), []).append(row)
		if self.grouped:
			self.get_average_rate_based_on_group_by()

	def get_average_rate_based_on_group_by(self):
		# sum buying / selling totals for group
		for key in list(self.grouped):
			for i, row in enumerate(self.grouped[key]):
				if row.qty or row.base_amount:
					row = self.set_average_rate(row)
					self.grouped_data.append(row)

	def set_average_rate(self, new_row):
		new_row.gross_profit = flt(new_row.base_amount - new_row.buying_amount, self.currency_precision)
		new_row.gross_profit_percent = flt(((new_row.gross_profit / new_row.base_amount) * 100.0), self.currency_precision) \
			if new_row.base_amount else 0
		new_row.buying_rate = flt(new_row.buying_amount / new_row.qty, self.float_precision) if new_row.qty else 0
		new_row.base_rate = flt(new_row.base_amount / new_row.qty, self.float_precision) if new_row.qty else 0

		return new_row

	def load_invoice_items(self):
		conditions = ""
		if self.filters.company:
			conditions += " and company = %(company)s"
		if self.filters.from_date:
			conditions += " and `tabSales Order`.transaction_date >= %(from_date)s"
		if self.filters.to_date:
			conditions += " and `tabSales Order`.transaction_date <= %(to_date)s"

		if self.filters.get("sales_order"):
			conditions += " and `tabSales Order`.name = %(sales_order)s"

		self.si_list = frappe.db.sql("""
			select
				`tabSales Order Item`.parenttype, `tabSales Order Item`.parent,
				`tabSales Order`.transaction_date,
				`tabSales Order`.project,
				`tabSales Order`.customer, `tabSales Order`.customer_group,
				`tabSales Order`.territory, `tabSales Order Item`.item_code,
				`tabSales Order Item`.item_name, `tabSales Order Item`.custom_valuation_rate,
				`tabSales Order Item`.description,
				`tabSales Order Item`.warehouse, `tabSales Order Item`.item_group,
				`tabSales Order Item`.brand, `tabSales Order Item`.stock_qty as qty,
				`tabSales Order Item`.base_net_rate, `tabSales Order Item`.base_net_amount,
				`tabSales Order Item`.name as "item_row"
			from
				`tabSales Order` inner join `tabSales Order Item`
					on `tabSales Order Item`.parent = `tabSales Order`.name
			where
				`tabSales Order`.docstatus=1 {conditions} {match_cond}
			order by
				`tabSales Order`.transaction_date desc
		""".format(conditions=conditions, match_cond = get_match_cond('Sales Order')), self.filters, as_dict=1)
