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
			"width": 180
		},
		{
			"fieldname": "party_name",
			"fieldtype": "Read Only",
			"label": "Party Name",
			"width": 200
		},
		{
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": "Payment Date",
			"options": "Payment Entry",
			"width": 180
		},
		{
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"label": "Last Payment",
			"width": 180
		},
		{
			"fieldname": "invoice_posting_date",
			"fieldtype": "Date",
			"label": "Last Invoice Date",
			"options": "Sales Invoice",
			"width": 180
		},
		{
			"fieldname": "invoice_amount",
			"fieldtype": "Currency",
			"label": "Last Invoice Amount",
			"width": 180
		},
		{
			"fieldname": "dr_balance",
			"fieldtype": "Currency",
			"label": "DR(OUTSTANDINGS)",
			"width": 180
		},
		{
			"fieldname": "cr_balance",
			"fieldtype": "Currency",
			"label": "CR(OUTSTANDINGS)",
			"width": 180
		}
	]
	return columns

def get_data(filters):
	data = []
	if filters.get('party_type') == "Customer":
		customers = frappe.db.sql("select name, customer_name from `tabCustomer`", as_dict=True)
		for c in customers:
			payment_e = frappe.db.sql("""select 
						name,
						posting_date, 
						party, 
						party_name, 
						paid_amount 
						from `tabPayment Entry` 
						where docstatus = 1 and party_type = 'Customer' and party = '{0}'
						order by posting_date desc limit 1""".format(c.name), as_dict=True)
			
			invoice = frappe.db.sql("""select 
						posting_date as si_date, 
						rounded_total
						from `tabSales Invoice` 
						where docstatus = 1 and customer = '{0}'
						order by posting_date desc limit 1""".format(c.name), as_dict=True)

			gl_entry = frappe.db.sql("""select 
					sum(debit) as debit,
					sum(credit) as credit 
					from `tabGL Entry` 
					where is_cancelled = 0 and party_type = 'Customer' and party = '{0}'""".format(c.name), as_dict=True)

			dr_balance = cr_balance = 0
			if gl_entry:
				if not gl_entry[0].credit:
					gl_entry[0].credit = 0
				if not gl_entry[0].debit:
					gl_entry[0].debit = 0
				balance = gl_entry[0].debit - gl_entry[0].credit
				if balance >= 0:
					dr_balance = balance
				elif balance < 0:
					cr_balance = balance
			row1 = {
				"posting_date": payment_e[0].posting_date if payment_e else None,
				"invoice_posting_date": invoice[0].si_date if invoice else None,
				"party": c.name,
				"party_name": c.customer_name,
				"paid_amount": payment_e[0].paid_amount if payment_e else 0,
				"invoice_amount": invoice[0].rounded_total if invoice else 0,
				"dr_balance": dr_balance,
				"cr_balance": cr_balance
			}
			data.append(row1)
		return data

	if filters.get('party_type') == "Supplier":
		supplier = frappe.db.sql("select name, supplier_name from `tabSupplier`", as_dict=True)
		for s in supplier:
			payment_e = frappe.db.sql("""select 
						name, 
						posting_date, 
						party, 
						party_name, 
						paid_amount 
						from `tabPayment Entry` 
						where docstatus = 1 and party_type = 'Supplier' and party = '{0}'
						order by posting_date desc limit 1""".format(s.name), as_dict=True)

			invoice = frappe.db.sql("""select 
						posting_date as pi_date, 
						rounded_total
						from `tabPurchase Invoice` 
						where docstatus = 1 and supplier = '{0}'
						order by posting_date desc limit 1""".format(s.name), as_dict=True)

			gl_entry = frappe.db.sql("""select 
					sum(debit) as debit,
					sum(credit) as credit 
					from `tabGL Entry` 
					where is_cancelled = 0 and party_type = 'Supplier' and party = '{0}'""".format(s.name), as_dict=True)

			dr_balance = cr_balance = 0
			if gl_entry:
				if not gl_entry[0].credit:
					gl_entry[0].credit = 0
				if not gl_entry[0].debit:
					gl_entry[0].debit = 0
				balance = gl_entry[0].debit - gl_entry[0].credit
				if balance >= 0:
					dr_balance = balance
				elif balance < 0:
					cr_balance = balance
			row1 = {
				"posting_date": payment_e[0].posting_date if payment_e else None,
				"pi_date": invoice[0].first_posting_date if invoice else None,
				"party": s.name,
				"party_name": s.supplier_name,
				"paid_amount": payment_e[0].paid_amount if payment_e else 0,
				"invoice_amount": invoice.first_paid_amount if invoice else 0,
				"dr_balance": dr_balance,
				"cr_balance": cr_balance
			}
			data.append(row1)
		return data
