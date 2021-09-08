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
				sum(so.total) as debit,
				(select sum(pe.paid_amount) from `tabPayment Entry` as pe where pe.docstatus = 1 and
				pe.party = so.customer and pe.posting_date >= '{1}' and pe.posting_date <= '{2}' 
				group by pe.party) as credit,
				(select sum(jea.debit) from `tabJournal Entry` as je
				left join `tabJournal Entry Account` as jea on je.name = jea.parent 
				where je.docstatus = 1 and jea.party = so.customer and je.posting_date >= '{1}' 
				and je.posting_date <= '{2}' group by jea.party) as debit1,
				(sum(so.total) - (select sum(pe.paid_amount) from `tabPayment Entry` as pe 
				where pe.docstatus = 1 and pe.posting_date >= '{1}' and pe.posting_date <= '{2}'
				and	pe.party = so.customer group by pe.party)) as balance
				from `tabSales Order` as so
				where so.docstatus = 1 and so.status != 'Closed' and so.company = '{0}'
				and so.transaction_date >= '{1}' and so.transaction_date <= '{2}' group by so.customer
				""".format(filters.get('company'), filters.get('from_date'), filters.get('to_date'))

		result = frappe.db.sql(query,as_dict=True)
		data = []
		total_debit = 0
		balance1 = 0
		for row in result:
			if not row.credit :
				row.credit = 0
				balance1 = row.debit - row.credit
				total_debit = row.debit
			else:
				if row.debit1:
					total_debit = row.debit + row.debit1
				else:
					row.debit1 = 0
					total_debit = row.debit + row.debit1

				if row.balance and row.debit1:
					balance1 = row.balance + row.debit1
				elif row.balance:
					row.debit1 = 0
					balance1 = row.balance + row.debit1
				elif row.debit1:
					row.balance = 0
					balance1 = row.balance + row.debit1
			
			row = {
				"customer": row.customer,
				"customer_name": row.customer_name,
				"debit": total_debit,
				"credit": row.credit,
				"balance": balance1
			}
			data.append(row)
		return data
	else:
		return []