// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */


frappe.query_reports["Gross Profit TC"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"group_by",
			"label": __("Group By"),
			"fieldtype": "Select",
			"options": "Invoice\nItem Code\nItem Group\nItem Size\nItem Color\nItem Texture\nItem Type\nBrand\nWarehouse\nCustomer\nCustomer Group\nTerritory\nSales Person\nSalesman\nProject",
			"default": "Invoice"
		},
	]
}