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
			"label": "Voucher Type",
			"fieldtype": "Data",
			"fieldname": "voucher_type",
			"width": 150
		},
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
		}
	]
	return columns

def get_data(filters):
	if filters.get('company'):
		query = """select 			
				"Payment Entry" as voucher_type,
				pe.party as customer,
				pe.party_name as customer_name,
				0 as debit,
				sum(pe.paid_amount) as credit
				from `tabPayment Entry` as pe
				where pe.docstatus = 1 and pe.party_type = 'Customer' and pe.company='{0}'
				and pe.posting_date >= '{1}' and pe.posting_date <= '{2}'
				group by customer
		union
		select 
				"Sales Order" as voucher_type,
				so.customer,
				so.customer_name,
				sum(so.rounded_total) as debit,
				0 as credit
				from `tabSales Order` as so
				where so.docstatus = 1 and so.status != 'Closed' and so.company = '{0}'
				and so.transaction_date >= '{1}' and so.transaction_date <= '{2}' group by so.customer
				""".format(filters.get('company'), filters.get('from_date'), filters.get('to_date'))

		result = frappe.db.sql(query,as_dict=True)
		print(query)
		data = []
		for row in result:
			row = {
				"voucher_type": row.voucher_type,
				"customer": row.customer,
				"customer_name": row.customer_name,
				"debit": row.debit,
				"credit": row.credit
			}
			data.append(row)
			
		return data
	else:
		return []