// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Purchase Order Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": "Company",
			"mandatory": 1,
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "purchase_order",
			"fieldtype": "Link",
			"label": "SO #",
			"mandatory": 0,
			"options": "Purchase Order"
		},
		{
			"fieldname": "po_no",
			"fieldtype": "Data",
			"label": "PO #",
			"mandatory": 0
		},
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date"
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "TO Date"
		}
	]
};