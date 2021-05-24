// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Wise Party Ledger"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
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
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options": "Party Type",
			"default": "",
			"reqd": 1,
			on_change: function() {
				frappe.query_report.set_filter_value('party', "");
			}
		},
		{
		
			"label": 'Party',
			"fieldname": 'party',
			"fieldtype": 'Dynamic Link',
			"options": 'party_type',
			"reqd": 1,
			on_change: function() {
				var party_type = frappe.query_report.get_filter_value('party_type');
				var parties = frappe.query_report.get_filter_value('party');
				var fieldname = erpnext.utils.get_party_name(party_type) || "name";
				frappe.db.get_value(party_type, parties, fieldname, function(value) {
					frappe.query_report.set_filter_value('party_name', value[fieldname]);
				});
			}
		},
		{
			"fieldname":"party_name",
			"label": __("Party Name"),
			"fieldtype": "Data",
			"read_only": 1
		}
	]
};
