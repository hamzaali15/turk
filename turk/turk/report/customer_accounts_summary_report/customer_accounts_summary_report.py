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
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer",
			"fieldname": "customer",
			"width": 150
		},
		{
			"label": "Customer Name",
			"fieldtype": "Data",
			"fieldname": "customer_name",
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
				so.customer,
				so.customer_name,
				sum(so.rounded_total) as debit,
				sum(pe.paid_amount) as credit,
				(sum(so.rounded_total) - sum(pe.paid_amount)) as balance
				from `tabSales Order` as so
				left join `tabPayment Entry` as pe on pe.party = so.customer
				where so.docstatus = 1 and so.status != 'Closed' and so.company = '{0}'
				and so.transaction_date >= '{1}' and so.transaction_date <= '{2}' group by so.customer
				""".format(filters.get('company'), filters.get('from_date'), filters.get('to_date'))

		result = frappe.db.sql(query,as_dict=True)
		
		data = []
		for row in result:
			# balance = row.debit - row.credit
			row = {
				"customer": row.customer,
				"customer_name": row.customer_name,
				"debit": row.debit,
				"credit": row.credit,
				"balance": row.balance
			}
			data.append(row)
		return data
	else:
		return []