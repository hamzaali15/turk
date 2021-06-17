# Copyright (c) 2013, Dexciss Technology and contributors
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
			"label": "Date",
			"fieldtype": "Date",
			"fieldname": "posting_date",
			"width": 100
		},
		{
			"label": "Voucher Type",
			"fieldtype": "Data",
			"fieldname": "voucher_type",
			"width": 150
		},
		{
			"label": "PO NO",
			"fieldtype": "Data",
			"fieldname": "po_number",
			"width": 100
		},
		{
			"label": "Voucher",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"fieldname": "voucher_no",
			"width": 150
		},
		{
			"label": "Debit",
			"fieldtype": "Currency",
			"fieldname": "debit",
			"width": 150
		},
		{
			"label": "Credit",
			"fieldtype": "Currency",
			"fieldname": "credit",
			"width": 150
		},
		{
			"label": "Balance",
			"fieldtype": "Currency",
			"fieldname": "balance",
			"width": 150
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select posting_date,po_number,voucher_no,debit,credit,voucher_type from (
		select 
				pe.posting_date ,			
				'' as po_number,
				pe.name as voucher_no,
				pe.paid_amount as debit,
				0 as credit,
				"Payment Entry" as voucher_type
				from `tabPayment Entry` as pe
				where pe.docstatus = 1 and pe.party_type = 'Supplier' and pe.company='{0}'
				and pe.posting_date >= '{1}' and pe.posting_date <= '{2}' and pe.party = '{3}'
		union all
		select 
				po.transaction_date as posting_date,
				po.po_number,
				po.name as voucher_no,
				0 as debit,
				po.rounded_total as credit,
				"Purchase Order" as voucher_type
				from `tabPurchase Order` as po
				where po.docstatus = 1 and po.status != 'Closed' and po.company = '{0}'
				and po.transaction_date >= '{1}' and po.transaction_date <= '{2}' and po.supplier = '{3}'
		union all
		select 
				je.posting_date,
				'' as po_number,
				je.name as voucher_no,
				jea.debit,
				jea.credit,
				je.voucher_type
				from `tabJournal Entry` as je
				left join `tabJournal Entry Account` as jea on je.name = jea.parent
				where je.docstatus = 1 and je.company = '{0}' and je.posting_date >= '{1}' and 
				je.posting_date <= '{2}' and jea.party = '{3}'
				) as t1 order by posting_date """.format(filters.get('company'), filters.get('from_date'), filters.get('to_date'), filters.get('supplier'))

		result = frappe.db.sql(query,as_dict=True)

		data = []
		balance1 = 0
		for row in result:
			if not row.debit:
				row.debit = 0
			if not row.credit:
				row.credit = 0
			row.balance = row.debit-row.credit
			balance1 += row.balance
			row = {
				"posting_date": row.posting_date,
				"voucher_type": row.voucher_type,
				"po_number": row.po_number,
				"voucher_no": row.voucher_no,
				"debit": row.debit,
				"credit": row.credit,
				"balance": balance1,
			}
			data.append(row)
			
		return data
	else:
		return []