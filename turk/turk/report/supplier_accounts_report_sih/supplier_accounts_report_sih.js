// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Supplier Accounts Report SIH"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default":	frappe.user_defaults.company,
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier",
			"reqd": 1,
			on_change: function(query_report) {
				let supplier = query_report.get_values().supplier;
				if(supplier) {
					frappe.db.get_value('Supplier', supplier, "supplier_name", function(value) {
						frappe.query_report.set_filter_value("supplier_name", value.supplier_name);
					});
				} else {
					frappe.query_report.set_filter_value("supplier_name", "");
				}
			}
		},
		{
			"fieldname":"supplier_name",
			"label": __("supplier Name"),
			"fieldtype": "Data",
			"read_only": 1
		}
	]
};