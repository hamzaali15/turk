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
			"fieldname": "date1",
			"fieldtype": "Date",
			"label": "Date",
			"width": 100
		},
		{
			"fieldname": "po_no1",
			"fieldtype": "Link",
			"label": "PO #",
			"options": "Purchase Order",
			"width": 70
		},
		{
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"label": "Purchase Order #",
			"options": "Purchase Order",
			"width": 130
		},
		{
			"fieldname": "fax_no1",
			"fieldtype": "Data",
			"label": "Fax #",
			"width": 100
		},
		{
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"label": "Party Name",
			"width": 200
		},
		{
			"fieldname": "item_name1",
			"fieldtype": "Data",
			"label": "Item Name",
			"width": 200
		},
		{
			"fieldname": "size1",
			"fieldtype": "Data",
			"label": "Size",
			"width": 90
		},
		{
			"fieldname": "boxes1",
			"fieldtype": "Float",
			"label": "Boxes",
			"width": 90
		},
		{
			"fieldname": "qty1",
			"fieldtype": "Float",
			"label": "Meters",
			"width": 90
		},
		{
			"fieldname": "rate1",
			"fieldtype": "Currency",
			"label": "Rate",
			"width": 90
		},
		{
			"fieldname": "amount1",
			"fieldtype": "Currency",
			"label": "Amount",
			"width": 150
		},
		{
			"fieldname": "emp",
			"fieldtype": "Data",
			"label": " ",
			"width": 100
		},
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
			"fieldname": "item_name",
			"fieldtype": "Data",
			"label": "Item Name",
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
			"label": "QTY",
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
			po.transaction_date as date1, 
			po.po_number as po_number1,
			po.name as po_name,
			poi.fax_no as fax_no1,
			po.supplier_name,
			poi.item_name as item_name1,
			itm.size as size1,
			poi.boxes as boxes1,
			poi.qty as qty1,
			poi.rate as rate1,
			poi.amount as amount1,
			so.transaction_date as date, 
			so.po_number,
			so.name,
			soi.fax_no,
			so.customer_name,
			soi.item_name,
			itm.size,
			soi.boxes,
			soi.qty,
			soi.rate,
			soi.amount,
			so.delivery
			from 
			`tabSales Order` as so 	inner join `tabSales Order Item` as soi on so.name = soi.parent			
 			left join `tabPurchase Order Item` as poi on soi.fax_no = poi.fax_no and poi.item_code=soi.item_code
			left join `tabPurchase Order` as po on po.name = poi.parent
			left join `tabItem` as itm on itm.name = soi.item_code
			where so.company = '{0}' and so.docstatus = 1 and so.status != 'Closed'""".format(filters.get('company'))

		if filters.get('sales_order'):
			query += " and so.name = '{0}'".format(filters.get('sales_order'))

		if filters.get('po_no'):
			query += " and po.name = '{0}'".format(filters.get('po_no'))

		if filters.get('from_date'):
			query += " and so.transaction_date >= '{0}'".format(filters.get('from_date'))

		if filters.get('to_date'):
			query += " and so.transaction_date <= '{0}'".format(filters.get('to_date'))
		
		result = frappe.db.sql(query,as_dict=True)
		data = []
	
		total_amount1 = 0
		total_boxes1 = 0
		total_qty1 = 0
		current_value = ""
		previous_value = ""
		cur_pre_val = ""		
		total_amount2 = 0
		total_boxes2 = 0
		total_qty2 = 0

		total_amount11 = 0
		total_boxes11 = 0
		total_qty11 = 0
		current_value1 = ""
		previous_value1 = ""
		cur_pre_val1 = ""		
		total_amount22 = 0
		total_boxes22 = 0
		total_qty22 = 0
		i=len(result)

		def subTotal():
			total_row = {
				"date1": "",
				"po_no1": "",
				"purchase_order": "",
				"fax_no1": "",
				"supplier_name": "",
				"item_name1": "",
				"size1": "<b>"+"Sub Total"+"</b>",
				"boxes1": total_boxes22,
				"qty1": total_qty22,
				"rate1": "",
				"amount1": total_amount22,

				"date": "",
				"po_no": "",
				"sales_order": "",
				"fax_no": "",
				"customer_name": "",
				"item_name": "",
				"size": "<b>"+"Sub Total"+"</b>",
				"boxes": total_boxes2,
				"qty": total_qty2,
				"rate": "",
				"amount": total_amount2,
				"status": "" 
			}
			data.append(total_row)

		def gTotal():
			total_row1 = {
				"date1": "",
				"po_no1": "",
				"purchase_order": "",
				"fax_no1": "",
				"supplier_name": "",
				"item_name1": "",
				"size1": "<b>"+"Grand Total"+"</b>",
				"boxes1": total_boxes11,
				"qty1": total_qty11,
				"rate1": "",
				"amount1": total_amount11,

				"date": "",
				"po_no": "",
				"sales_order": "",
				"fax_no": "",
				"customer_name": "",
				"item_name": "",
				"size": "<b>"+"Grand Total"+"</b>",
				"boxes": total_boxes1,
				"qty": total_qty1,
				"rate": "",
				"amount": total_amount1,
				"status": ""
			}
			data.append(total_row1)

		for row in result:
			i=i-1
			current_value = row.po_number
			current_value1 = row.po_number1
			if(cur_pre_val != ""):
				if(cur_pre_val != current_value):
					previous_value = cur_pre_val
			if(cur_pre_val1 != ""):
				if(cur_pre_val1 != current_value1):
					previous_value1 = cur_pre_val1
			if(previous_value == ""):
				previous_value = row.po_number
			if(previous_value1 == ""):
				previous_value1 = row.po_number1

			if(current_value == previous_value):
				total_amount2 += row.amount
				total_boxes2 += row.boxes
				total_qty2 += row.qty
			if(current_value1 == previous_value1):
				if row.amount1:
					total_amount22 += row.amount1
				if row.boxes1:
					total_boxes22 += row.boxes1
				if row.qty1:
					total_qty22 += row.qty1
			
			if(current_value != "" and previous_value != ""):
				if(current_value != previous_value):
					subTotal()
					previous_value = ""
					cur_pre_val=row.po_number
					total_amount2 = row.amount
					total_boxes2 = row.boxes
					total_qty2 = row.qty
			if(current_value1 != "" and previous_value1 != ""):
				if(current_value1 != previous_value1):
					# subTotal()
					previous_value1 = ""
					cur_pre_val1 = row.po_number1
					total_amount22 = row.amount1
					total_boxes22 = row.boxes1
					total_qty22 = row.qty1
					
			total_amount1 += row.amount
			total_boxes1 += row.boxes
			total_qty1 += row.qty

			if row.amount1:
				total_amount11 += row.amount1
			if row.boxes1:
				total_boxes11 += row.boxes1
			if row.qty1:
				total_qty11 += row.qty1
			
			row = {
				"date1": row.date1,
				"po_no1": row.po_number1,
				"purchase_order": row.po_name,
				"fax_no1": row.fax_no1,
				"supplier_name": row.supplier_name,
				"item_name1": row.item_name1,
				"size1": row.size1,
				"boxes1": row.boxes1,
				"qty1": row.qty1,
				"rate1": row.rate1,
				"amount1": row.amount1,
				"emp": "",
				"date": row.date,
				"po_no": row.po_number,
				"sales_order": row.name,
				"fax_no": row.fax_no,
				"customer_name": row.customer_name,
				"item_name": row.item_name,
				"size": row.size,
				"boxes": row.boxes,
				"qty": row.qty,
				"rate": row.rate,
				"amount": row.amount,
				"status": row.delivery
			}
			data.append(row)
			if(i==0):
				subTotal()
				gTotal()
		return data
	else:
		return []