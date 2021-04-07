# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


class UnbilledCustomerOrdersReport(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.filters.from_date = getdate(self.filters.from_date or nowdate())
		self.filters.to_date = getdate(self.filters.to_date or nowdate())

	def run(self):
		if self.filters.from_date > self.filters.to_date:
			frappe.throw(_("From Date must be before To Date"))

		columns = self.get_columns()
		data = self.get_data()
		return columns, data

	def get_columns(self):
		columns = [
			{
				"label": _("Date"),
				"fieldtype": "Date",
				"fieldname": "posting_date",
				"width": 80
			},
			{
				"label": _("Payment Entry"),
				"fieldtype": "Dynamic Link",
				"options": "voucher_type",
				"fieldname": "voucher_no",
				"width": 120
			},
			{
				"label": _("Sales Order"),
				"fieldtype": "Link",
				"options": "Sales Order",
				"fieldname": "sales_order",
				"width": 100
			},
			{
				"label": _("Debit"),
				"fieldtype": "Currency",
				"fieldname": "debit",
				"width": 120
			},
			{
				"label": _("Credit"),
				"fieldtype": "Currency",
				"fieldname": "credit",
				"width": 120
			},
			{
				"label": _("Balance"),
				"fieldtype": "Currency",
				"fieldname": "balance",
				"width": 120
			}
		]

		return columns

	def get_data(self):
		return self.get_gl_entries()

	def get_gl_entries(self):
		data = []
		total_debit = total_credit = 0

		opening_balance = frappe._dict({
			"posting_date": self.filters.from_date,
			"voucher_no": "Opening Balance",
			"debit": 0.0,
			"credit": 0.0,
			"balance": 0.0
		})
		closing_balance = frappe._dict({
			"posting_date": self.filters.to_date,
			"voucher_no": "Closing Balance",
			"debit": 0.0,
			"credit": 0.0,
			"balance": 0.0
		})
		self.gl_entries = frappe.db.sql("""
				select
					posting_date, voucher_no,
					if(sum(debit-credit) > 0, sum(debit-credit), 0) as debit,
					if(sum(debit-credit) < 0, -sum(debit-credit), 0) as credit
				from
					`tabGL Entry`
				where
					docstatus < 2 and party_type='Customer' and party = %(customer)s and posting_date < %(from_date)s
					and company = %(company)s
				group by voucher_no
				order by posting_date""", self.filters, as_dict=True)
		for gle in self.gl_entries:
			opening_balance.debit += gle.debit
			opening_balance.credit += gle.credit

		sales_inv_gl = frappe.db.sql("""
			select
			null as posting_date, null as voucher_no, 
			(select distinct sii.sales_order from  
				`tabSales Invoice Item` as sii where sii.sales_order is not null and sii.parent = si.name ) as sales_order,
			if(sum(gl.debit-gl.credit) > 0, sum(gl.debit-gl.credit), 0) as debit,
			if(sum(gl.debit-gl.credit) < 0, -sum(gl.debit-gl.credit), 0) as credit,
			0 as balance
			from
			`tabGL Entry` as gl
			inner join `tabSales Invoice` as si on si.name = gl.voucher_no
			where
			gl.docstatus < 2 and gl.party_type='Customer' and gl.party = %(customer)s
			and gl.posting_date >= %(from_date)s
			and gl.posting_date <= %(to_date)s
			and gl.company = %(company)s
			and gl.voucher_type = 'Sales Invoice'
			group by gl.voucher_type, sales_order
			order by gl.posting_date""", self.filters, as_dict=True)
		for res in sales_inv_gl:
			if res.get('debit'):
				total_debit += res.get('debit')
			if res.get('name'):
				split_name_lst = (res.get('name')).split(",")
				if split_name_lst:
					gl = frappe.get_doc("GL Entry", split_name_lst[0])
					res['posting_date'] = gl.posting_date

		payment_ent_gl = frappe.db.sql("""select
				null as posting_date, gl.voucher_no, 
				null as sales_order,
				if(sum(gl.debit-gl.credit) > 0, sum(gl.debit-gl.credit), 0) as debit,
				if(sum(gl.debit-gl.credit) < 0, -sum(gl.debit-gl.credit), 0) as credit,
				0 as balance
				from
				`tabGL Entry` as gl
				inner join `tabPayment Entry` as si on si.name = gl.voucher_no
				where
				gl.docstatus < 2 and gl.party_type='Customer' and gl.party = %(customer)s
				and gl.posting_date >= %(from_date)s
				and gl.posting_date <= %(to_date)s
				and gl.company = %(company)s
				and gl.voucher_type = 'Payment Entry'
				group by gl.voucher_no, sales_order
				order by gl.posting_date""", self.filters, as_dict=True)
		for res in payment_ent_gl:
			if res.get('credit'):
				total_credit += res.get('credit')
			if res.get('name'):
				split_name_lst = (res.get('name')).split(",")
				if split_name_lst:
					gl = frappe.get_doc("GL Entry", split_name_lst[0])
					res['posting_date'] = gl.posting_date

		closing_balance.debit += total_debit
		closing_balance.credit += total_credit

		data.append(opening_balance)
		if not sales_inv_gl and not payment_ent_gl:
			closing_balance.debit += opening_balance.debit
			closing_balance.credit += opening_balance.credit

		if sales_inv_gl:
			data.extend(sales_inv_gl)
		if payment_ent_gl:
			data.extend(payment_ent_gl)
		data.append(closing_balance)
		unbilled_orders = self.get_unbilled_orders()
		data.extend(unbilled_orders)
		self.calculate_running_total(data)
		return data

	def get_unbilled_orders(self):
		unbilled_orders = frappe.db.sql("""
			select
				so.transaction_date as posting_date, so.name as sales_order,
				so.rounded_total as debit,
				sum(ifnull(si.rounded_total, 0)) as credit
			from `tabSales Order` so
			left join `tabSales Invoice` si on si.docstatus=1 and si.is_return!=1 and exists(
				select item.name
				from `tabSales Invoice Item` item
				where item.parent = si.name and item.sales_order = so.name
			)
			where
				so.docstatus = 1 and so.status != 'Closed' and per_billed < 98.98
				and so.customer=%(customer)s and so.company=%(company)s
			group by so.name
			having debit-credit > 0
			order by transaction_date
		""", self.filters, as_dict=1)
		return unbilled_orders

	def calculate_running_total(self, data):
		for i, d in enumerate(data):
			d.balance = d.debit - d.credit
			if i > 0 and d.voucher_type != 'Closing Balance':
				prev_row = data[i-1]
				d.balance += prev_row.balance

def execute(filters=None):
	return UnbilledCustomerOrdersReport(filters).run()