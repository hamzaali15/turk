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
			"fieldname": "party",
			"fieldtype": "Read Only",
			"label": "Party",
			"width": 120
		},
		{
			"fieldname": "party_name",
			"fieldtype": "Read Only",
			"label": "Party Name",
			"width": 120
		},
		{
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Last Payment",
			"width": 120
		},
		{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Payment Date",
			"options": "Payment Entry",
			"width": 120
		},
		{
			"fieldname": "dr_balance",
			"fieldtype": "Currency",
			"label": "DR(OUTSTANDINGS)",
			"width": 120
		},
		{
			"fieldname": "cr_balance",
			"fieldtype": "Currency",
			"label": "CR(OUTSTANDINGS)",
			"width": 120
		}
	]
	return columns

def get_data(filters):
	if filters.get('party_type') == "Customer":
		pay_type = "Receive"
	if filters.get('party_type') == "Supplier":
		pay_type = "pay"
	if filters.get('party_type') in ('Customer', 'Supplier'):
		query = """select
			p.name,
			p.posting_date,
			p.party,
			p.party_name,
			p.paid_amount
			from `tabPayment Entry` as p
			join (select party, max(posting_date) as MaxDate from `tabPayment Entry` group by party) as pe
			on p.party = pe.party
			where p.docstatus = 1 and p.payment_type = '{0}' and p.party_type = '{1}' and p.posting_date = pe.MaxDate
			group by p.party""".format(pay_type, filters.get('party_type'))

		result = frappe.db.sql(query,as_dict=True)
		data = []
		
		for row in result:
			query1 = """select
				sum(debit) as debit,
				sum(credit) as credit
				from `tabGL Entry`
				where is_cancelled = 0 and party = '{0}' group by party """.format(row.party)

			result1 = frappe.db.sql(query1,as_dict=True)
			for row1 in result1:
				balance, dr_balance, cr_balance = 0, 0, 0
				if not row1.credit:
					row.credit = 0
				if not row1.debit:
					row.debit = 0
				balance = row1.debit - row1.credit
				if balance >= 0:
					dr_balance = balance
				elif balance < 0:
					cr_balance = balance
				row1 = {
					"posting_date": row.posting_date,
					"party": row.party,
					"party_name": row.party_name,
					"paid_amount": row.paid_amount,
					"dr_balance": dr_balance,
					"cr_balance": cr_balance
				}
				data.append(row1)
		return data
	else:
		frappe.msgprint("Please Select Customer or Supplier as Party Type")