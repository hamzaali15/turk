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
			"label": "Supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"fieldname": "supplier",
			"width": 150
		},
		{
			"label": "Supplier Name",
			"fieldtype": "Data",
			"fieldname": "supplier_name",
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
		query = """select 
				po.supplier,
				po.supplier_name,
				sum(po.rounded_total) as credit,
				sum(pe.paid_amount) as debit,
				(sum(pe.paid_amount) - sum(po.rounded_total)) as balance
				from `tabPurchase Order` as po
				left join `tabPayment Entry Reference` as per on per.reference_name = po.name
				left join `tabPayment Entry` as pe on pe.name = per.parent
				where po.docstatus = 1 and po.status != 'Closed' and po.company = '{0}'
				and po.transaction_date >= '{1}' and po.transaction_date <= '{2}' group by po.supplier
				""".format(filters.get('company'), filters.get('from_date'), filters.get('to_date'))

		result = frappe.db.sql(query,as_dict=True)

		data = []
		for row in result:
			row = {
				"supplier": row.supplier,
				"supplier_name": row.supplier_name,
				"debit": row.debit,
				"credit": row.credit,
				"balance": row.balance
			}
			data.append(row)
			
		return data
	else:
		return []