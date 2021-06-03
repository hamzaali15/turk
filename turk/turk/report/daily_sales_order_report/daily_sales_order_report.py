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
			"fieldname": "date",
			"fieldtype": "Date",
			"label": "Date",
			"width": 100
		},
		{
			"fieldname": "po_no",
			"fieldtype": "Link",
			"label": "PO #",
			"options": "Purchase Order",
			"width": 70
		},
		{
			"fieldname": "sales_order",
			"fieldtype": "Link",
			"label": "Sales Order #",
			"options": "Sales Order",
			"width": 130
		},
		{
			"fieldname": "fax_no",
			"fieldtype": "Data",
			"label": "Fax #",
			"width": 100
		},
		{
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"label": "Party Name",
			"width": 200
		},
		{
			"fieldname": "size",
			"fieldtype": "Data",
			"label": "Size",
			"width": 90
		},
		{
			"fieldname": "boxes",
			"fieldtype": "Float",
			"label": "Boxes",
			"width": 90
		},
		{
			"fieldname": "qty",
			"fieldtype": "Float",
			"label": "Meters",
			"width": 90
		},
		{
			"fieldname": "rate",
			"fieldtype": "Currency",
			"label": "Rate",
			"width": 90
		},
		{
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": "Amount",
			"width": 150
		},
		{
			"fieldname": "status",
			"fieldtype": "Data",
			"label": "Status",
			"width": 130
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select
			so.transaction_date as date, 
			so.po_number,
			so.name,
			soi.fax_no,
			so.customer_name,
			itm.size,
			soi.boxes,
			soi.qty,
			soi.rate,
			soi.amount,
			so.status
			from `tabSales Order` as so
			left join `tabSales Order Item` as soi on so.name = soi.parent
			left join `tabItem` as itm on itm.name = soi.item_code
			where so.company = '{0}' and so.docstatus = 1
			order by po_number, date""".format(filters.get('company'))

		if filters.get('sales_order'):
			query += " and so.name = '{0}'".format(filters.get('sales_order'))

		if filters.get('po_no'):
			query += " and so.po_number like '{0}%'".format(filters.get('po_no'))

		if filters.get('from_date'):
			query += " and date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and date <= '{0}'".format(filters.get('to_date'))

		result = frappe.db.sql(query,as_dict=True)
		data = []

		total_amount1 = 0
		current_value= ""
		previous_value=""
		cur_pre_val=""		
		total_amount2 = 0
		i=len(result)

		def subTotal():
			total_row = {
				"date": "",
				"po_no": "",
				"sales_order": "",
				"fax_no": "",
				"customer_name": "",
				"size": "<b>"+"Sub Total"+"</b>",
				"boxes": "",
				"qty": "",
				"rate": "",
				"amount": total_amount2,
				"status": "" 
			}
			data.append(total_row)

		def gTotal():
			total_row1 = {
				"date": "",
				"po_no": "",
				"sales_order": "",
				"fax_no": "",
				"customer_name": "",
				"size": "<b>"+"Grand Total"+"</b>",
				"boxes": "",
				"qty": "",
				"rate": "",
				"amount": total_amount1,
				"status": ""
			}
			data.append(total_row1)

		for row in result:
			i=i-1
			current_value = row.po_number
			if(cur_pre_val != ""):
				if(cur_pre_val != current_value):
					previous_value = cur_pre_val
			if(previous_value == ""):
				previous_value = row.po_number

			if(current_value == previous_value):
				total_amount2 += row.amount
			
			if(current_value != "" and previous_value != ""):
				if(current_value != previous_value):
					subTotal()
					previous_value = ""
					cur_pre_val=row.po_number
					total_amount2 = row.amount
					
			total_amount1 += row.amount
			
			row = {
				"date": row.date,
				"po_no": row.po_number,
				"sales_order": row.name,
				"fax_no": row.fax_no,
				"customer_name": row.customer_name,
				"size": row.size,
				"boxes": row.boxes,
				"qty": row.qty,
				"rate": row.rate,
				"amount": row.amount,
				"status": row.status
			}
			data.append(row)
			if(i==0):
				subTotal()
				gTotal()
		return data
	else:
		return []