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
				sum(po.total) as credit,
				(select sum(pe.paid_amount) from `tabPayment Entry` as pe where pe.docstatus = 1 and
				pe.party = po.supplier and pe.posting_date >= '{1}' and pe.posting_date <= '{2}' 
				group by pe.party) as debit,
				(select sum(jea.credit) from `tabJournal Entry` as je
				left join `tabJournal Entry Account` as jea on je.name = jea.parent 
				where je.docstatus = 1 and jea.party = po.supplier and je.posting_date >= '{1}' 
				and je.posting_date <= '{2}' group by jea.party) as credit1,
				((select sum(pe.paid_amount) from `tabPayment Entry` as pe 
				where pe.docstatus = 1 and pe.posting_date >= '{1}' and pe.posting_date <= '{2}'
				and	pe.party = po.supplier group by pe.party) - sum(po.total)) as balance
				from `tabPurchase Order` as po
				where po.docstatus = 1 and po.status != 'Closed' and po.company = '{0}'
				and po.transaction_date >= '{1}' and po.transaction_date <= '{2}' group by po.supplier
				""".format(filters.get('company'), filters.get('from_date'), filters.get('to_date'))

		result = frappe.db.sql(query,as_dict=True)

		data = []
		total_credit = 0
		balance1 = 0
		for row in result:
			if row.credit1:
				total_credit = row.credit + row.credit1
			else:
				row.credit1 = 0
				total_credit = row.credit + row.credit1

			if not row.debit:
				row.debit = 0

			if row.balance and row.credit1:
				balance1 = row.balance - row.credit1
			elif row.balance:
				row.credit = 0
				balance1 = row.balance - row.credit1
			elif row.credit:
				row.balance = 0
				balance1 = row.balance - row.credit1
			
			row = {
				"supplier": row.supplier,
				"supplier_name": row.supplier_name,
				"debit": row.debit,
				"credit": total_credit,
				"balance": balance1
			}
			data.append(row)
			
		return data
	else:
		return []