// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Gross Profit based on Sales Order"] = {
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
			"fieldname":"sales_order",
			"label": __("Sales Order"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Sales Order",
			get_query: () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company,
					}
				}
			}
		},
		{
			"fieldname":"group_by",
			"label": __("Group By"),
			"fieldtype": "Data",
			"options": "Sales Order",
			"default": "Sales Order",
			"hidden" :1
		},
	]
};
