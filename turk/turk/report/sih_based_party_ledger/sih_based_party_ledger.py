# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe

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
			"width": 150
		},
		{
			"label": "Voucher Type",
			"fieldtype": "Data",
			"fieldname": "voucher_type",
			"width": 150
		},
		{
			"label": "Voucher No.",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"fieldname": "voucher_no",
			"width": 150
		},
		{
			"label": "Shipment No.",
			"fieldtype": "Data",
			"fieldname": "shipment_no",
			"width": 150
		},
		{
			"label": "PO No.",
			"fieldtype": "Data",
			"fieldname": "po_no",
			"width": 150
		},
		{
			"label": "FAX No.",
			"fieldtype": "Data",
			"fieldname": "fax_no",
			"width": 150
		},
		{
			"fieldname": "item_code",
			"fieldtype": "Link",
			"label": "Item Code",
			"options": "Item",
			"width": 150
		},
		{
			"fieldname": "item_name",
			"fieldtype": "data",
			"label": "Item Name",
			"width": 170
		},
		{
			"fieldname": "qty",
			"fieldtype": "Float",
			"label": "Quantity",
			"width": 150
		},
		{
			"fieldname": "boxes",
			"fieldtype": "Float",
			"label": "Boxes",
			"width": 150
		},
		{
			"fieldname": "rate",
			"fieldtype": "Currency",
			"label": "Rate",
			"width": 150
		},
		{
			"fieldname": "debit",
			"fieldtype": "Currency",
			"label": "Debit",
			"width": 150
		},
		{
			"fieldname": "credit",
			"fieldtype": "Currency",
			"label": "Credit",
			"width": 150
		},
		{
			"fieldname": "balance",
			"fieldtype": "Currency",
			"label": "Balance",
			"width": 150
		},
		{
			"label": "Remarks",
			"fieldtype": "Data",
			"fieldname": "remarks",
			"width": 150
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		if filters.get('party_type') == "Customer":
			query = """select 
				so.posting_date as date,
				"Sales Invoice" as voucher_type,
				so.name as voucher_no,
				so.shipment_no,
				so.po_number,
				soi.fax_no,
				soi.item_code,
				soi.item_name,
				soi.qty,
				soi.boxes,
				soi.rate,
				soi.amount as debit,
				0 as credit,
				so.remarks
				from `tabSales Invoice` as so
				left join `tabSales Invoice Item` as soi on so.name = soi.parent
				where so.docstatus = 1 and so.company = '{0}' and so.customer = '{1}' and so.posting_date >= '{2}' and so.posting_date <= '{3}' 
			union all
			select 
				pe.posting_date as date,
				"Payment Entry" as voucher_type,
				pe.name as voucher_no,
				'',
				'',
				'',
				'',
				'',
				0,
				0,
				0,
				0 as debit,
				pe.paid_amount as credit,
				pe.remarks
				from `tabPayment Entry` as pe
				where pe.docstatus = 1 and pe.party_type = 'Customer' and pe.company = '{0}' and pe.party = '{1}' and pe.posting_date >= '{2}' and pe.posting_date <= '{3}'
			union all
			select 
				je.posting_date as date,
				je.voucher_type,
				je.name as voucher_no,
				'',
				'',
				'',
				'',
				'',
				0,
				0,
				0,
				jea.debit,
				jea.credit,
				je.remark as remarks
				from `tabJournal Entry` as je
				left join `tabJournal Entry Account` as jea on je.name = jea.parent
				where je.docstatus = 1 and jea.party_type = 'Customer' and je.company = '{0}' and jea.party = '{1}' and je.posting_date >= '{2}' and je.posting_date <= '{3}'
				order by date
			""".format(filters.get('company'),filters.get('party'),filters.get('from_date'),filters.get('to_date'))

		if filters.get('party_type') == "Supplier":
			query = """select 
				po.posting_date as date,
				"Purchase Invoice" as voucher_type,
				po.name as voucher_no,
				po.shipment_no,
				po.po_number,
				poi.fax_no,
				poi.item_code,
				poi.item_name,
				poi.qty,
				poi.boxes,
				poi.rate,
				0 as debit,
				poi.amount as credit,
				po.remarks
				from `tabPurchase Invoice` as po
				left join `tabPurchase Invoice Item` as poi on po.name = poi.parent
				where po.docstatus = 1 and po.company = '{0}' and po.supplier = '{1}' and po.posting_date >= '{2}' and po.posting_date <= '{3}' 
			union all
			select 
				pe.posting_date as date,
				"Payment Entry" as voucher_type,
				pe.name as voucher_no,
				'',
				'',
				'',
				'',
				'',
				0,
				0,
				0,
				pe.paid_amount as debit,
				0 as credit,
				pe.remarks
				from `tabPayment Entry` as pe
				where pe.docstatus = 1 and pe.party_type = 'Supplier' and pe.company = '{0}' and pe.party = '{1}' and pe.posting_date >= '{2}' and pe.posting_date <= '{3}'
			union all
			select 
				je.posting_date as date,
				je.voucher_type,
				je.name as voucher_no,
				'',
				'',
				'',
				'',
				'',
				0,
				0,
				0,
				jea.debit,
				jea.credit,
				je.remark as remarks
				from `tabJournal Entry` as je
				left join `tabJournal Entry Account` as jea on je.name = jea.parent
				where je.docstatus = 1 and jea.party_type = 'Supplier' and je.company = '{0}' and jea.party = '{1}' and je.posting_date >= '{2}' and je.posting_date <= '{3}'
				order by date
			""".format(filters.get('company'),filters.get('party'),filters.get('from_date'),filters.get('to_date'))
		result = frappe.db.sql(query,as_dict=True)
		data = []

		total_qty = 0
		total_boxes = 0
		total_debit = 0
		total_credit = 0
		current_value= ""
		previous_value=""
		cur_pre_val=""
		total_qty1 = 0
		total_boxes1 = 0
		total_debit1 = 0
		total_credit1 = 0

		i=len(result)

		def subTotal():
			total_row = {
				"date": "",
				"voucher_type": "",
				"voucher_no": "",
				"shipment_no": "",
				"po_no": "",
				"fax_no": "",
				"item_code": "",
				"item_name": "<b>"+"Sub Total"+"</b>",
				"qty": total_qty1,
				"boxes": total_boxes1,
				"rate": "",
				"debit": total_debit1,
				"credit": total_credit1,
				"balance": "",
				"remarks": ""
			}
			data.append(total_row)

		def gTotal():
			total_row1 = {
				"date": "",
				"voucher_type": "",
				"voucher_no": "",
				"shipment_no": "",
				"po_no": "",
				"fax_no": "",
				"item_code": "",
				"item_name": "<b>"+"Grand Total"+"</b>",
				"qty": total_qty,
				"boxes": total_boxes,
				"rate": "",
				"debit": total_debit,
				"credit": total_credit,
				"balance": "",
				"remarks": ""
			}
			data.append(total_row1)

		balance1 = 0
		
		for row in result:
			i=i-1

			current_value = row.voucher_no
			if(cur_pre_val != ""):
				if(cur_pre_val != current_value):
					previous_value = cur_pre_val
			if(previous_value == ""):
				previous_value = row.voucher_no	

			if(current_value == previous_value):
				total_qty1 += row.qty
				total_boxes1 += row.boxes
				total_debit1 += row.debit
				total_credit1 += row.credit	

			if(current_value != "" and previous_value != ""):
				if(current_value != previous_value):
					subTotal()
					previous_value = ""
					cur_pre_val = row.voucher_no
					total_qty1 = row.qty
					total_boxes1 = row.boxes
					total_debit1 = row.debit
					total_credit1 = row.credit

			row.balance = row.debit - row.credit
			balance1 += row.balance

			total_debit += row.debit
			total_credit += row.credit

			total_boxes += float(row.boxes)
			total_qty += float(row.qty)

			row = {
				"date": row.date,
				"voucher_type": row.voucher_type,
				"voucher_no": row.voucher_no,
				"shipment_no": row.shipment_no,
				"po_no": row.po_number,
				"fax_no": row.fax_no,
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": row.qty,
				"boxes": row.boxes,
				"rate": row.rate,
				"debit": row.debit,
				"credit": row.credit,
				"balance": balance1,
				"remarks": row.remarks
			}
			data.append(row)
			if(i==0):
				subTotal()
				gTotal()
		return data
	else:
		return []
