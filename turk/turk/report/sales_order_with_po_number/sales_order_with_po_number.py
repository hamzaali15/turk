# Copyright (c) 2013, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import frappe, erpnext
from erpnext import get_company_currency, get_default_company
from erpnext.accounts.report.utils import get_currency, convert_to_presentation_currency
from frappe.utils import getdate, cstr, flt, fmt_money
from frappe import _, _dict
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.report.financial_statements import get_cost_centers_with_children
from six import iteritems
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions, get_dimension_with_children
from collections import OrderedDict

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		{
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"label": "Sales Order",
			"options": "Sales Order",
			"width": 100
		},
		{
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer Code",
			"options": "Customer",
			"width": 120
		 },
		{
			"fieldname": "customer_name",
			"fieldtype": "Read Only",
			"label": "Customer Name",
			"width": 200
		},
		{
			"fieldname": "po_number",
			"fieldtype": "Read Only",
			"label": "PO Number",
			"width": 100
		},
		{
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"label": "Purchase Order",
			"options": "Purchase Order",
			"width": 120
		},
		{
			"fieldname": "supplier",
			"fieldtype": "Link",
			"label": "Supplier Code",
			"options": "Supplier",
			"width": 110
		 },
		{
			"fieldname": "supplier_name",
			"fieldtype": "Read Only",
			"label": "Supplier Name",
			"width": 200
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select 
			so.name,
			so.customer,
			so.customer_name,
			so.po_number,
			po.name as po_no,
			po.supplier,
			po.supplier_name
			from `tabSales Order` as so
			left join `tabPurchase Order` as po on so.po_number = po.po_number
			where po.docstatus = 1 and so.docstatus = 1 and  so.company = '{0}'""".format(filters.get('company'))

		if filters.get('from_date'):
			query += " and so.date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and so.date <= '{0}'".format(filters.get('to_date'))

		if filters.get('po_number'):
			query += " and so.po_number = '{0}'".format(filters.get('po_number'))

		if filters.get('customer'):
			query += " and so.customer = '{0}'".format(filters.get('customer'))

		result = frappe.db.sql(query,as_dict=True)
		data = []
		
		for row in result:
			row = {
				"sales_order": row.name,
				"customer": row.customer,
				"customer_name": row.customer_name,
				"po_number": row.po_number,
				"purchase_order": row.po_no,
				"supplier": row.supplier,
				"supplier_name": row.supplier_name
			}
			data.append(row)
		return data
	else:
		return []