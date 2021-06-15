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
			"label": "FAX NO",
			"fieldtype": "Data",
			"fieldname": "fax_no",
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
		query = """select posting_date,fax_no,voucher_no,debit,credit,voucher_type from (
			select 
				pe.posting_date ,			
				'' as fax_no,
				pe.name as voucher_no,
				0 as debit,
				pe.paid_amount as credit,
				"Payment Entry" as voucher_type
				from `tabPayment Entry` as pe
				where pe.docstatus = 1 and pe.party_type = 'Customer' and pe.company='{0}'
				and pe.posting_date >= '{1}' and pe.posting_date <= '{2}' and pe.party = '{3}'
			union
			select 
				so.transaction_date as posting_date,
				so.fax_no,
				so.name as voucher_no,
				so.rounded_total as debit,
				0 as credit,
				"Sales Order" as voucher_type
				from `tabSales Order` as so
				where so.docstatus = 1 and so.status != 'Closed' and so.company = '{0}'
				and so.transaction_date >= '{1}' and so.transaction_date <= '{2}' and so.customer = '{3}'
			union
			select 
				je.posting_date as date,
				'' as fax_no,
				je.name as voucher_no,
				jea.debit,
				jea.credit,
				je.voucher_type
				from `tabJournal Entry` as je
				left join `tabJournal Entry Account` as jea on je.name = jea.parent
				where je.docstatus = 1 and jea.party_type = 'Customer' and je.company = '{0}' and je.posting_date >= '{1}' 
				and je.posting_date <= '{2}' and jea.party = '{3}') as t1 
				order by posting_date """.format(filters.get('company'), filters.get('from_date'), filters.get('to_date'), filters.get('customer'))

		result = frappe.db.sql(query,as_dict=True)

		data = []
		balance1 = 0
		for row in result:
			row.balance = row.debit-row.credit
			balance1 += row.balance
			row = {
				"posting_date": row.posting_date,
				"voucher_type": row.voucher_type,
				"fax_no": row.fax_no,
				"voucher_no": row.voucher_no,
				"debit": row.debit,
				"credit": row.credit,
				"balance": balance1,
			}
			data.append(row)
			
		return data
	else:
		return []