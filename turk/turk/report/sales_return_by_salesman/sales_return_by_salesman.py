# Copyright (c) 2013, RC and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe.utils import cint, getdate, add_days
from frappe import _

def execute(filters=None):
	if not filters: filters ={}

	sales_order1=sales_order2=""
	conditions = ""
	if filters.get("company"): conditions = " and company = '{}' ".format(filters.get("company"))

	if filters.get("sales_order"):
		sales_order1 = " and sales_order like '%{}%' ".format(filters.get("sales_order"))
		sales_order2 = " and cust_shipment_no like '%{}%' ".format(filters.get("sales_order"))
	else:
		conditions += " and posting_date >= '{}' ".format(add_days(getdate(),-20))



	columns = get_columns()
	data = get_invoice_details(conditions,sales_order1,sales_order2)

	return columns, data

def get_invoice_details(conditions,sales_order1,sales_order2):
	sql_query = """select si.name,si.return_against,sii.sales_order,si.posting_date,si.customer
	,si.customer_name,si.cust_phone_number , si.rounded_total,si.sales_order_owner ,si.company,si.update_stock
		from `tabSales Invoice` si inner join `tabSales Invoice Item` sii
		on si.name=sii.parent
		where
		si.is_return=1 and si.docstatus=1 {0} {1}
		group by si.name

		union

		select pr.name,0,pr.cust_shipment_no,pr.posting_date,pr.supplier,pr.supplier_name,'',pr.rounded_total,
		pr.cust_sales_order_owner,pr.company,1
		from `tabPurchase Receipt` pr
		where pr.supplier='S-00095' and pr.docstatus=1 {0} {2}
 		""".format(conditions,sales_order1,sales_order2)
	return frappe.db.sql(sql_query, as_list=1)

def get_columns():
	return [
		_("Return No") + ":Link/Sales Invoice:100",
		_("Retrun Against") + ":Link/Sales Invoice:100",
		_("Sales Order") + ":Link/Sales Order:100",
		_("Date") + ":Date:80",
		_("Customer") + ":Link/Customer:80",
		_("Customer Name") + ":Data:120",
		_("Mobile Number") + ":Data:100",
		_("Total") + ":Currency:120",
		_("Sales Man") + ":Link/User:100",
		_("Company") + ":Link/Company:100"
	]