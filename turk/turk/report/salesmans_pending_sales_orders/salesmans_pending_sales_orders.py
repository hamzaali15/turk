# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _



def execute(filters=None):
	user = frappe.session.user
	filters["user"] = user
	customer_filter = ""
	if not (filters.get("customer_group")):
		frappe.throw(_("Please set Customer Group First"))
	else:
		customer_filter = """ and customer_group in (select name from `tabCustomer Group`
						where lft>=(select lft from `tabCustomer Group` where name = '{0}')
			and rgt<=(select rgt from `tabCustomer Group` where name = '{0}' ))""".format(filters.get("customer_group"))

	#frappe.throw(_(customer_filter))
	columns = [
		{"fieldname": "sales_order", "label": _("ID"), "fieldtype": "Link", "options": "Sales Order", "width": 100},
		{"fieldname": "salesman", "label": _("Salesman"), "fieldtype": "Data", "width": 100},
		{"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 100},
		{"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 100},
		{"fieldname": "transaction_date", "label": _("Date"), "fieldtype": "Date", "width": 100},
		{"fieldname": "total", "label": _("Total"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "payment", "label": _("Payment"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "returns", "label": _("Returns"), "fieldtype": "Currency", "width": 100},
	#	{"fieldname": "return_payment", _("label"): "Returns Payment", "fieldtype": "Currency", "width": 100},
		{"fieldname": "pending", "label": _("Pending"), "fieldtype": "Currency", "width": 100},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 100},
		{"fieldname": "delivery_status", "label": _("Delivery"), "fieldtype": "Data", "width": 100},
		{"fieldname": "billing_status", "label": _("Billing"), "fieldtype": "Data", "width": 100},
		{"fieldname": "per_delivered", "label": _("Delivered"), "fieldtype": "Int", "width": 100},
		{"fieldname": "per_billed", "label": _("Billed Percent"), "fieldtype": "Int", "width": 100},
		{"fieldname": "owner", "label": _("Owner"), "fieldtype": "Link", "options": "User", "width": 100},
		{"fieldname": "allow_delivery", "label": _("Allow Delivery"), "fieldtype": "Check", "width": 100},
		{"fieldname": "delivery_approval_comments", "label": _("Delivery Comments"), "fieldtype": "Data", "width": 150},
		{"fieldname": "company", "label": _("Company"), "fieldtype": "Link", "options": "Company", "width": 100}
	]

	sql_query = """
		select
			so.name as sales_order, usr.full_name as salesman, so.customer, so.customer_name, so.transaction_date,
			so.status, so.delivery_status, so.billing_status, so.per_delivered, so.per_billed, so.owner, so.company,
			so.rounded_total, so.grand_total, so.allow_delivery, so.delivery_approval_comments
		from `tabSales Order` so
		inner join `tabUser` usr on usr.name=%(user)s
		where so.transaction_date between %(fdate)s and %(tdate)s
		and so.company = %(company)s and so.docstatus=1
		and so.owner = %(user)s
		and so.status not in ('Closed') {0}
		order by so.transaction_date desc
		""".format(customer_filter)

	sales_orders = frappe.db.sql(sql_query, filters, as_dict=1)

	gl_entries = frappe.db.sql("""
		select
			so.name as sales_order, gle.voucher_type, gle.against_voucher_type,
			gle.against_voucher, gle.credit-gle.debit as amount
		from `tabGL Entry` gle
		inner join `tabSales Order` so
			on (gle.against_voucher_type='Sales Order' and gle.against_voucher=so.name)
		where voucher_no != against_voucher and so.transaction_date between %(fdate)s and %(tdate)s
		and so.company = %(company)s and so.docstatus=1 and so.status not in ('Closed') {0}

		union all

		select
			so.name as sales_order, gle.voucher_type, gle.against_voucher_type,
			gle.against_voucher, gle.credit-gle.debit as amount
		from `tabGL Entry` gle
		inner join `tabSales Order` so
			on ((gle.against_voucher_type='Sales Invoice')
			 and gle.against_voucher in
			 (select distinct si.parent from `tabSales Invoice Item` si where si.sales_order=so.name )
		  )
		where voucher_no != against_voucher  and so.transaction_date between %(fdate)s and %(tdate)s
		and so.company = %(company)s and so.docstatus=1 and so.status not in ('Closed') {0}
	""".format(customer_filter), filters, as_dict=1)
	order_gle = {}
	for gle in gl_entries:
		order_gle.setdefault(gle.sales_order, [])
		order_gle[gle.sales_order].append(gle)

	data = []
	for so in sales_orders:
		so.total = so.rounded_total or so.grand_total
		so.payment = so.returns = so.return_payment = so.pending = 0
		for gle in order_gle.get(so.sales_order, []):
			if gle.voucher_type == "Sales Invoice" and gle.against_voucher_type == "Sales Invoice":
				so.returns += gle.amount
			elif gle.amount < 0:
				so.return_payment -= gle.amount
			else:
				so.payment += gle.amount

		so.pending = so.total - so.payment - so.returns  + so.return_payment
		if so.pending > 1 :
			data.append(so)


	return columns, data
