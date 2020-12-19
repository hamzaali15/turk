# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe



def execute(filters=None):
	columns = [
		{"fieldname": "sales_order", "label": "ID", "fieldtype": "Link", "options": "Sales Order", "width": 100},
		{"fieldname": "salesman", "label": "Salesman", "fieldtype": "Data", "width": 100},
		{"fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer", "width": 100},
		{"fieldname": "customer_name", "label": "Customer Name", "fieldtype": "Data", "width": 100},
		{"fieldname": "transaction_date", "label": "Date", "fieldtype": "Date", "width": 100},
		{"fieldname": "total", "label": "Total", "fieldtype": "Currency", "width": 100},
		{"fieldname": "payment", "label": "Payment", "fieldtype": "Currency", "width": 100},
		{"fieldname": "returns", "label": "Returns", "fieldtype": "Currency", "width": 100},
		{"fieldname": "return_payment", "label": "Returns Payment", "fieldtype": "Currency", "width": 100},
		{"fieldname": "pending", "label": "Pending", "fieldtype": "Currency", "width": 100},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
		{"fieldname": "delivery_status", "label": "Delivery", "fieldtype": "Data", "width": 100},
		{"fieldname": "billing_status", "label": "Billing", "fieldtype": "Data", "width": 100},
		{"fieldname": "per_delivered", "label": "Delivered", "fieldtype": "Percent", "width": 100},
		{"fieldname": "per_billed", "label": "Billed Percent", "fieldtype": "Percent", "width": 100},
		{"fieldname": "owner", "label": "Owner", "fieldtype": "Link", "options": "User", "width": 100},
		{"fieldname": "allow_delivery", "label": "Allow Delivery", "fieldtype": "Check", "width": 100},
		{"fieldname": "delivery_approval_comments", "label": "Delivery Comments", "fieldtype": "Data", "width": 150},
		{"fieldname": "company", "label": "Company", "fieldtype": "Link", "options": "Company", "width": 100}
	]

	sales_orders = frappe.db.sql("""
		select
			so.name as sales_order, usr.full_name as salesman, so.customer, so.customer_name, so.transaction_date,
			so.status, so.delivery_status, so.billing_status, so.per_delivered, so.per_billed, so.owner, so.company,
			so.rounded_total, so.grand_total, so.allow_delivery, so.delivery_approval_comments
		from `tabSales Order` so
		inner join `tabUser` usr on usr.name=so.owner
		where so.transaction_date between %(fdate)s and %(tdate)s
		and so.company = %(company)s and so.docstatus=1
		order by so.transaction_date desc
	""", filters, as_dict=1)

	gl_entries = frappe.db.sql("""
		select * from (
		select
			so.name as sales_order, gle.voucher_type, gle.against_voucher_type,
			gle.against_voucher, gle.credit-gle.debit as amount
		from `tabGL Entry` gle
		inner join `tabSales Order` so
			on (gle.against_voucher_type='Sales Order' and gle.against_voucher=so.name)
		where voucher_no != against_voucher and so.transaction_date between %(fdate)s and %(tdate)s
		and so.company = %(company)s and so.docstatus=1

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
		and so.company = %(company)s and so.docstatus=1
		) tabglentry order by sales_order
	""", filters, as_dict=1)
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

		so.pending = so.total - so.payment - so.returns + so.return_payment

	return columns, sales_orders