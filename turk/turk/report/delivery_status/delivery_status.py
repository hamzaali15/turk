# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	if not filters: filters = {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_data(filters):
	return frappe.db.sql("""
		select so.name, so.owner, so.customer_name, so.transaction_date, soi.item_code, soi.item_name, soi.qty, soi.boxes, soi.pieces,
  		mr.qty, mr.boxes, mr.pieces, if(sed.docstatus = 1, 'Submitted', 'Pending'), sed.qty, sed.boxes, sed.pieces, si.qty,
  		if(
    		soi.amount = soi.billed_amt,
    		0,
    		ifnull(soi.qty, 0) - ifnull(si.qty, 0)
  		)
		from
		`tabSales Order Item` soi
		left join `tabSales Order` so on so.name = soi.parent
		left join (
			select
			tmr.docstatus,
			sum(if(tmr.docstatus = 1, tmri.qty, 0)) qty,
			sum(if(tmr.docstatus = 1, tmri.boxes, 0)) boxes,
			sum(if(tmr.docstatus = 1, tmri.pieces, 0)) pieces,
			tmri.sales_order,
			tmri.item_code,
			tmri.custom_warehouse_name
			from
			`tabMaterial Request` tmr
			inner join `tabMaterial Request Item` tmri on tmr.name = tmri.parent
			where
			tmri.sales_order is not null
			group by
			tmri.item_code,
			tmri.sales_order
		) mr on mr.sales_order = soi.parent
		and mr.item_code = soi.item_code
		left join (
			select
			se.docstatus,
			sum(if(se.docstatus = 1, sed.qty, 0)) qty,
			sum(if(se.docstatus = 1, sed.boxes, 0)) boxes,
			sum(if(se.docstatus = 1, sed.pieces, 0)) pieces,
			sed.sales_order,
			sed.item_code,
			sed.s_warehouse,
			sed.t_warehouse
			from
			`tabStock Entry Detail` sed
			inner join `tabStock Entry` se on sed.parent = se.name
			where
			sed.sales_order is not null
			and se.posting_date >= %(from_date) s
			and sed.t_warehouse like '%%Transit%%'
			group by
			sed.item_code,
			sed.sales_order,
			sed.s_warehouse
		) as sed on sed.item_code = soi.item_code
		and sed.sales_order = soi.parent
		left join (
		select
		si.docstatus,
		sum(if(si.docstatus = 1, sii.qty, 0)) qty,
		sum(if(si.docstatus = 1, sii.boxes, 0)) boxes,
		sum(if(si.docstatus = 1, sii.pieces, 0)) pieces,
		sii.sales_order,
		sii.item_code,
		sii.warehouse
		from
		`tabSales Invoice Item` sii
		inner join `tabSales Invoice` si on sii.parent = si.name
		where
		sii.sales_order is not null
		and si.posting_date >= %(from_date) s
		and si.is_return != 1
		group by
		sii.item_code,
		sii.sales_order
		) as si on si.item_code = soi.item_code
		and si.sales_order = soi.parent
		where
		so.docstatus = 1
		and so.status not in ('Closed')
		and so.transaction_date >= %(from_date) s
		and so.transaction_date <= %(to_date) s
		and so.company = %(company) s
		order by
		so.transaction_date desc

	""", filters, as_dict=False)

def get_columns():
	"""return columns"""

	columns = [
		_("Bill No")+":Link/Sales Order:100",
		_("Created By")+":Link/User:100",
		_("Customer")+":Data:110",
		_("Date")+":Date:80",
		_("Code")+":Link/Item:70",
		_("Item Name")+":Data:200",
		_("(SO)SQM")+":Float:70",
		_("(SO)Boxes")+":Int:70",
		_("(SO)Pieces")+":Int:70",
		_("(RQ)SQM")+":Int:70",
		_("(RQ)Boxes")+":Int:70",
		_("(RQ)Pieces")+":Int:70",
		_("(SE)Status")+":Data:100",
		_("(SE)QM")+":Float:70",
		_("(SE)Boxes")+":Int:70",
		_("(SE)Pieces")+":Int:70",
		_("Deliverd")+":Float:70",
		_("Remaining")+":Float:70",

	]

	return columns
