import frappe
from frappe import _


def set_supplier_details(si, method):
	for si_item in si.items:
		item = frappe.get_doc("Item", si_item.item_code)
		for item_default in item.item_defaults:
			if item_default.company == si.company and item_default.default_supplier:
				supplier_name = frappe.get_value("Supplier", item_default.default_supplier, "supplier_name")
				si_item.default_supplier = item_default.default_supplier
				si_item.supplier_name = supplier_name


def update_reserved_qty(si, method):
	si.update_reserved_qty()


def create_purchase_invoices_against_sales_taxes(si, method):
	if si.update_stock:
		sales_order_no = ""
		if(si.doctype == "Sales Invoice"):
			for d in si.items:
				if d.sales_order:
					sales_order_no = d.sales_order
		for row in si.taxes:
			if "22750 - Freight Payable" in row.account_head and row.tax_amount>0:
				purchase_invoice=frappe.get_doc(
					{
						'doctype': 'Purchase Invoice',
						"naming_series": "PLC-",
						"remarks": si.name,
						"cust_sales_order": sales_order_no,
						"docstatus": 1,
						"discount_amount": 0,
						"supplier": "LOADER BIKE",
						"supplier_name": "LOADER BIKE",
						"is_paid": 0,
						"company": si.company,
						"set_posting_time": 0,
						"is_return": 0,
						"ignore_pricing_rule": 1,
						"update_stock": 0,
						"submit_on_creation": 1,
						"items": [
							{
								"item_code": "99999",
								"item_name": "FREIGHT CHARGES",
								"qty": 1,
								"cost_center": row.cost_center,
								"expense_account": row.account_head,
								"rate": row.tax_amount,
								"received_qty": 1,
								"uom": "Nos",
								"conversion_factor": 1
							}
						]

					})
				purchase_invoice.insert(ignore_permissions = True)
				frappe.msgprint("Purchase Invoice has been Created.")

			if "22755 - Cutting / Fitting Charges" in row.account_head and row.tax_amount>0 :
				purchase_invoice=frappe.get_doc(
					{
						'doctype': 'Purchase Invoice',
						"naming_series": "P-SO-",
						"remarks": si.name,
						"cust_sales_order": sales_order_no,
						"docstatus": 1,
						"discount_amount": 0,
						"supplier": "Cutting / Fitting",
						"supplier_name": "Cutting / Fitting",
						"is_paid": 0,
						"company": si.company,
						"set_posting_time": 0,
						"is_return": 0,
						"ignore_pricing_rule": 1,
						"update_stock": 0,
						"submit_on_creation": 1,
						"items": [
							{
								"item_code": "99998",
								"item_name": "Cutting / Fitting Charges",
								"qty": 1,
								"cost_center": row.cost_center,
								"expense_account": row.account_head,
								"rate": row.tax_amount,
								"received_qty": 1,
								"uom": "Nos",
								"conversion_factor": 1
							}
						]

					})
				purchase_invoice.insert(ignore_permissions = True)
				frappe.msgprint("Purchase Invoice has been Created.")


def validate_discount_while_return(si, method):
	if si.is_return:
		sales_order = si.cust_sales_order_number
		sales_invoice = si.return_against
		total_discount = 0
		payment_entries_names = set()

		pe = frappe.db.sql("""select t1.name, t1.paid_amount
						from `tabPayment Entry` t1, `tabPayment Entry Reference` t2
						where
						t1.name = t2.parent and t1.docstatus = 1
						and t1.mode_of_payment = %s
						and t2.reference_doctype in ("Sales Order", "Sales Invoice")
						and t2.reference_name in %s""",
						("Discount", (sales_order, sales_invoice)),
						as_dict=1
						)
		for p in pe:
			payment_entries_names.add(p['name'])

		for payment_entry in payment_entries_names:
			discount = frappe.db.get_value("Payment Entry", payment_entry, 'total_allocated_amount')
			total_discount += discount

		if total_discount:
			currency = frappe.db.get_value("Payment Entry", list(payment_entries_names)[0], 'paid_from_account_currency')
			grand_total = frappe.db.get_value("Sales Invoice", sales_invoice, 'grand_total')
			if not abs(si.grand_total) < grand_total:
				frappe.throw(_("Invoice(s) against the Sales Order was settled with discount of amount {0} {1}".format(currency, total_discount)))


def validate_user_warehouse(si, method):
	if si.update_stock:
		user_warehouse = frappe.db.get_value("User",{"name": frappe.session['user']}, "user_warehouse")
		if si.is_return and not si.approval_receive_in_breakage :
			for item in si.items:
				if not (item.warehouse in user_warehouse):
					frappe.throw(_("You are not allowed to submit Invoice in Warehoues:<b> {0} </b>  for Item Code  <b>{1}</b>")
					.format(item.warehouse,item.item_code))
		else:
			for item in si.items:
				if not (item.warehouse in user_warehouse or item.warehouse in (user_warehouse.replace("Normal","Breakage")) or item.warehouse in (user_warehouse.replace("Depot","Breakage"))):
					frappe.throw(_("You are not allowed to submit Invoice in Warehoues:<b> {0} </b>  for Item Code  <b>{1}</b>")
					.format(item.warehouse,item.item_code))


def validate_taxes_and_charges_from_so(si, method):
	if not si.is_return:
		if not si.taxes:
			return

		tax_balance = get_remaining_taxes_and_charges_amount(si, for_validate=True)
		for d in si.taxes:
			if d.charge_type == "Actual":
				if d.account_head not in tax_balance:
					frappe.throw(_("Row #{0}: {1} could not be found in Sales Order").format(d.idx, d.description))

				if d.tax_amount > tax_balance[d.account_head]:
					frappe.throw(_("Row #{0}: {1} can not be greater than remaining amount of {2}")
						.format(d.idx, d.description, tax_balance[d.account_head]))


def get_remaining_taxes_and_charges_amount(self, for_validate):
	sales_orders = set([d.sales_order for d in self.items])
	tax_balance = {}
	for so in sales_orders:
		order_taxes = frappe.db.sql("""
			select account_head, tax_amount
			from `tabSales Taxes and Charges`
			where parenttype='Sales Order' and parent=%s and charge_type='Actual'
		""", [so], as_dict=1)

		for tax in order_taxes:
			tax_balance.setdefault(tax.account_head, 0)
			tax_balance[tax.account_head] += tax.tax_amount

		docstatus_condition = "docstatus=1" if for_validate else "docstatus<2"
		invoice_taxes = frappe.db.sql("""
			select t.account_head, t.tax_amount
			from `tabSales Taxes and Charges` t
			where t.parenttype='Sales Invoice' and t.charge_type='Actual' and t.parent!=%s and exists(
				select i.parent from `tabSales Invoice Item` i where i.sales_order=%s and t.parent=i.parent
			) and {0}
		""".format(docstatus_condition), [self.name, so], as_dict=1)

		for tax in invoice_taxes:
			tax_balance.setdefault(tax.account_head, 0)
			tax_balance[tax.account_head] -= tax.tax_amount

	return tax_balance


@frappe.whitelist()
def split_invoice_between_warehouse(source_name):
	source_doc = frappe.get_doc("Sales Invoice", source_name)

	for d in source_doc.items:
		if not d.warehouse:
			frappe.throw(_("Row {0}: Warehouse not selected for Item {1}".format(d.idx, d.item_code)))

	warehouses = set(map(lambda d: d.warehouse, source_doc.items))
	if len(warehouses) <= 1:
		frappe.throw(_("You can only split invoice if there is more than 1 warehouse selected"))

	first_warehouse = source_doc.items[0].warehouse
	warehouses.remove(first_warehouse)

	doc_list = []
	for warehouse in warehouses:
		doc = frappe.copy_doc(source_doc, ignore_no_copy=1)
		doc.direct_delivery_from_warehouse = 1
		doc.custom_delivery_warehouse = warehouse
		doc.set("taxes", [])
		doc.set("payment_schedule", [])

		doc.set("items", [])
		items = [d for d in source_doc.items if d.warehouse == warehouse]
		for item in items:
			doc.append("items", item)

		doc.set("advances", [])
		doc.save()
		doc.calculate_taxes_and_totals()
		doc.set_advances()
		doc.save()
		doc_list.append(doc.name)

	to_remove = [d for d in source_doc.items if d.warehouse != first_warehouse]
	[source_doc.remove(d) for d in to_remove]
	for i, d in enumerate(source_doc.items):
		d.idx = i + 1
	source_doc.direct_delivery_from_warehouse = 1
	source_doc.custom_delivery_warehouse = first_warehouse
	source_doc.set("advances", [])

	tax_balance = get_remaining_taxes_and_charges_amount(source_doc, for_validate=False)
	for d in source_doc.taxes:
		if d.account_head in tax_balance:
			d.tax_amount = tax_balance[d.account_head]

	source_doc.calculate_taxes_and_totals()
	source_doc.set_advances()
	source_doc.save()

	frappe.msgprint(_("Sales Invoices ({0}) created".format(", ".join(doc_list))))

@frappe.whitelist()
def validate_sales_invoice(sl, method):
	if not sl.return_against and not sl.is_return:
		for res in sl.items:
			if res.sales_order:
				sales_order = frappe.get_doc("Sales Order", res.sales_order)
				if not sales_order.allow_delivery:
					bill_amt = 0
					# paid_amt = sales_order.advance_paid
					paid_amt = 0
					query = """select sum(rounded_total) - sum(outstanding_amount) as rounded_total
							from `tabSales Invoice` where name in (select distinct parent from  
							`tabSales Invoice Item` where sales_order is not null and sales_order = '{0}')
							and docstatus in (0,1)""".format(sales_order.name)

					if not sl.get("__islocal"):
						query += " and name !='{0}'".format(sl.name)
					result = frappe.db.sql(query, as_list=True)
					if result:
						if result[0][0]:
							bill_amt = float(result[0][0])
					paid_query = """select sum(per.allocated_amount) as paid_amt from `tabPayment Entry Reference` as per
								inner join `tabPayment Entry` as pe on pe.name = per.parent
								where per.reference_doctype = 'Sales Invoice' and pe.docstatus = 1 and pe.payment_type = 'Receive' 
								and per.sales_order = '{0}' """.format(sales_order.name)
									
					result = frappe.db.sql(paid_query, as_list=True)
					if result:
						if result[0][0]:
							paid_amt += float(result[0][0])

					paid_query1 = """select sum(per.allocated_amount) as paid_amt from `tabPayment Entry Reference` as per
								inner join `tabPayment Entry` as pe on pe.name = per.parent
								where per.reference_doctype = 'Sales Order' and  pe.docstatus = 1 and pe.payment_type = 'Receive' 
								and per.reference_name = '{0}' """.format(sales_order.name)

					result1 = frappe.db.sql(paid_query1, as_list=True)
					if result1:
						if result1[0][0]:
							paid_amt += float(result1[0][0])

					reaming_amt = abs(paid_amt) - abs(bill_amt)
					diff = sl.rounded_total - reaming_amt
					if sl.rounded_total > reaming_amt and diff > 5:
						frappe.throw(_("Can not allow to Invoice total amount greater then <b>{0}</b>".format(reaming_amt)))
						break