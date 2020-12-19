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
		select
		tsm.cost_center,
		tsm.salesman,
		ifnull(rounded_total,0),
		ifnull(canceld_sale,0),
		ifnull(sales_return,0),
		ifnull(old_system_return,0),
		(ifnull(rounded_total,0)-ifnull(canceld_sale,0)-ifnull(sales_return,0)-ifnull(old_system_return,0)),
		ifnull(cash_sale,0),
		ifnull(credit_sale,0),
		ifnull(Recovery,0)

		from (select name as salesman,user_costcenter as cost_center from tabUser where user_warehouse in (select name from `tabWarehouse` where company=%(company)s)) as tsm
		left join
		( select sum(rounded_total) as rounded_total, sum(advance_paid) as advance_paid,
		sum(if(customer_group="Cash Customer",rounded_total,0)) as cash_sale,
		sum(if(customer_group="Credit Customer",rounded_total,0)) as credit_sale,
		owner
		from `tabSales Order` where docstatus>=1 and company= %(company)s and transaction_date>=%(fdate)s and transaction_date<=%(tdate)s group by owner)

		tso on tsm.salesman = tso.owner left join

		(select cost_center,owner,sum(rounded_total) canceld_sale from `tabSales Order` where docstatus=2 and date(modified)>=%(fdate)s and date(modified)<=%(tdate)s group by owner) tco on tsm.salesman= tco.owner

		left join

		(select ts.cost_center,sales_order_owner, abs(sum(tsi.net_amount)) as sales_return from `tabSales Invoice` tc inner join `tabSales Invoice Item` tsi on tc.name=tsi.parent where is_return=1 and tc.docstatus=1 and company= %(company)s and tc.posting_date>=%(fdate)s and tc.posting_date<=%(tdate)s group by tc.sales_order_owner) tsr

		on tsm.salesman=tsr.sales_order_owner left join

		(select '',cust_sales_order_owner,abs(sum(rounded_total)) Old_system_return from `tabPurchase Receipt` tpi where tpi.docstatus=1 and company= %(company)s and tpi.posting_date>=%(fdate)s and tpi.posting_date<=%(tdate)s group by tpi.cust_sales_order_owner) osr on tsm.salesman=osr.cust_sales_order_owner
		left join

		(select '',cust_sales_order_owner,sum(allocated_amount) as Recovery from `tabPayment Entry Reference` tper inner join `tabPayment Entry` tpe on tper.parent=tpe.name where tpe.posting_date>= %(fdate)s and tpe.posting_date<= %(tdate)s group by tper.cust_sales_order_owner) as per on tsm.salesman=per.cust_sales_order_owner order by tsm.cost_center,tsm.salesman;

	""", filters, as_dict=False)

def get_columns():
	"""return columns"""

	columns = [
		_("Branch")+":Data:150",
		_("Salesman")+":Link/User:150",
		_("Gross Sale")+":Currency:100",
		_("Canceld Sale")+":Currency:100",
		_("Sales Return")+":Currency:100",
		_("Old Sys Return")+":Currency:100",
		_("Net Sale")+":Currency:100",
		_("Cash Sale")+":Currency:100",
		_("Credit Sale")+":Currency:100",
		_("Recovery")+":Currency:100",
	]

	return columns
