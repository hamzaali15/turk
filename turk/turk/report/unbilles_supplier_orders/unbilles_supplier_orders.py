# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate


class UnbilledSupplierOrdersReport(object):
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
				"label": _("Voucher Type"),
				"fieldtype": "Data",
				"fieldname": "voucher_type",
				"width": 120
			},
			{
				"label": _("Voucher"),
				"fieldtype": "Dynamic Link",
				"options": "voucher_type",
				"fieldname": "voucher_no",
				"width": 120
			},
			{
				"label": _("Purchase Order"),
				"fieldtype": "Link",
				"options": "Purchase Order",
				"fieldname": "po",
				"width": 120
			},
			{
				"label": _("Against Voucher Type"),
				"fieldtype": "Data",
				"fieldname": "against_voucher_type",
				"width": 120
			},
			{
				"label": _("Against Voucher"),
				"fieldtype": "Dynamic Link",
				"options": "against_voucher_type",
				"fieldname": "against_voucher",
				"width": 120
			},
			{
				"label": _("Debit"),
				"fieldtype": "Currency",
				"fieldname": "debit",
				"width": 110
			},
			{
				"label": _("Credit"),
				"fieldtype": "Currency",
				"fieldname": "credit",
				"width": 110
			},
			{
				"label": _("Balance"),
				"fieldtype": "Currency",
				"fieldname": "balance",
				"width": 110
			}
		]

		return columns

	def get_data(self):
		self.get_gl_entries()
		self.get_unbilled_orders()

		opening_balance = frappe._dict({
			"posting_date": self.filters.from_date,
			"voucher_type": "Opening Balance",
			"debit": 0.0,
			"credit": 0.0,
			"balance": 0.0
		})
		ledger_rows = []
		closing_balance = frappe._dict({
			"posting_date": self.filters.to_date,
			"voucher_type": "Closing Balance",
			"debit": 0.0,
			"credit": 0.0,
			"balance": 0.0
		})
		unbilled_rows = []

		for gle in self.gl_entries:
			if gle.posting_date < self.filters.from_date:
				opening_balance.debit += gle.debit
				opening_balance.credit += gle.credit
			else:
				ledger_rows.append(gle)

			closing_balance.debit += gle.debit
			closing_balance.credit += gle.credit

		for d in self.unbilled_orders:
			unbilled_rows.append(d)

		invoices = []
		for d in ledger_rows:
			if d.voucher_type == "Purchase Invoice":
				invoices.append(d.voucher_no)
		invoice_order_nos = self.get_invoice_order_nos(invoices)
		for d in ledger_rows:
			if d.voucher_type == "Purchase Invoice":
				d.po = invoice_order_nos.get(d.voucher_no)

		data = [opening_balance] + ledger_rows + [closing_balance] + unbilled_rows
		self.calculate_running_total(data)
		return data

	def get_gl_entries(self):
		self.gl_entries = frappe.db.sql("""
			select
				posting_date, voucher_type, voucher_no,
				if(sum(debit-credit) > 0, sum(debit-credit), 0) as debit,
				if(sum(debit-credit) < 0, -sum(debit-credit), 0) as credit,
				GROUP_CONCAT(DISTINCT against_voucher_type SEPARATOR ', ') as against_voucher_type,
				GROUP_CONCAT(DISTINCT against_voucher SEPARATOR ', ') as against_voucher
			from
				`tabGL Entry`
			where
				docstatus < 2 and party_type='Supplier' and party = %(supplier)s and posting_date <= %(to_date)s
				and company = %(company)s
			group by voucher_type, voucher_no
			order by posting_date""", self.filters, as_dict=True)

	def get_unbilled_orders(self):
		self.unbilled_orders = frappe.db.sql("""
			select
				po.transaction_date as posting_date, po.name as po,
				po.rounded_total as debit,
				sum(ifnull(pi.rounded_total, 0)) as credit
			from `tabPurchase Order` po
			left join `tabPurchase Invoice` pi on pi.docstatus=1 and pi.is_return!=1 and exists(
				select item.name
				from `tabPurchase Invoice Item` item
				where item.parent = pi.name and item.purchase_order = po.name
			)
			where
				po.docstatus = 1 and po.status != 'Closed' and per_billed<98.98
				and po.supplier=%(supplier)s and po.company=%(company)s
			group by po.name
			having debit-credit > 0
			order by transaction_date
		""", self.filters, as_dict=1)

	def get_invoice_order_nos(self, invoices):
		if not invoices:
			return {}

		res = frappe.db.sql("""
			select parent, GROUP_CONCAT(DISTINCT purchase_order SEPARATOR ', ')
			from `tabPurchase Invoice Item`
			where parent in ({invoices})
			group by parent
		""".format(invoices=", ".join(["%s"] * len(invoices))), invoices)
		return dict(res)

	def calculate_running_total(self, data):
		for i, d in enumerate(data):
			d.balance = d.debit - d.credit
			if i > 0 and d.voucher_type != 'Closing Balance':
				prev_row = data[i-1]
				d.balance += prev_row.balance


def execute(filters=None):
	return UnbilledSupplierOrdersReport(filters).run()

	# columns, data = [], []
	# return columns, data
