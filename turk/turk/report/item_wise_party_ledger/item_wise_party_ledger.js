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
		// {
		// 	"fieldname":"account",
		// 	"label": __("Account"),
		// 	"fieldtype": "Link",
		// 	"options": "Account",
		// 	"get_query": function() {
		// 		var company = frappe.query_report.get_filter_value('company');
		// 		return {
		// 			"doctype": "Account",
		// 			"filters": {
		// 				"company": company,
		// 			}
		// 		}
		// 	}
		// },
		
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
			"reqd": 1,
			on_change: function(query_report) {
				let customer = query_report.get_values().customer;
				if(customer) {
					frappe.db.get_value('Customer', customer, "customer_name", function(value) {
						frappe.query_report.set_filter_value("customer_name", value.customer_name);
					});
				} else {
					frappe.query_report.set_filter_value("customer_name", "");
				}
			}
		},
		{
			"fieldname":"customer_name",
			"label": __("Customer Name"),
			"fieldtype": "Data",
			"read_only": 1
		}







		// {
		// 	"fieldname":"party_type",
		// 	"label": __("Party Type"),
		// 	"fieldtype": "Link",
		// 	"options": "Party Type",
		// 	"default": "",
		// 	on_change: function() {
		// 		frappe.query_report.set_filter_value('party', "");
		// 	}
		// },
		// {
		// 	"fieldname":"party",
		// 	"label": __("Party"),
		// 	"fieldtype": "Link",
		// 	// "reqd": 1,
		// 	get_data: function(txt) {
		// 		if (!frappe.query_report.filters) return;

		// 		let party_type = frappe.query_report.get_filter_value('party_type');
		// 		if (!party_type) return;

		// 		return frappe.db.get_link_options(party_type, txt);
		// 	},
		// 	on_change: function(query_report) {
		// 		let customer = query_report.get_values().customer;
		// 		if(customer) {
		// 			frappe.db.get_value('Customer', customer, "customer_name", function(value) {
		// 				frappe.query_report.set_filter_value("customer_name", value.customer_name);
		// 			});
		// 		}
		// 		else {
		// 			frappe.query_report.set_filter_value("customer_name", "");
		// 		}
		// 	}
		// },
		// {
		// 	"fieldname":"party_name",
		// 	"label": __("Party Name"),
		// 	"fieldtype": "Data",
		// 	"read_only": 1
		// },
		

		
		
// 		{
// 			"fieldname":"party",
// 			"label": __("Party"),
// 			"fieldtype": "MultiSelectList",
// 			get_data: function(txt) {
// 				if (!frappe.query_report.filters) return;

// 				let party_type = frappe.query_report.get_filter_value('party_type');
// 				if (!party_type) return;

// 				return frappe.db.get_link_options(party_type, txt);
// 			},
// 			on_change: function() {
// 				var party_type = frappe.query_report.get_filter_value('party_type');
// 				var parties = frappe.query_report.get_filter_value('party');

// 				// if(!party_type || parties.length === 0 || parties.length > 1) {
// 				// 	frappe.query_report.set_filter_value('party_name', "");
// 				// 	return;
// 				// } else {
// 				// 	var party = parties[0];
// 				// 	var fieldname = erpnext.utils.get_party_name(party_type) || "name";
// 				// 	frappe.db.get_value(party_type, party, fieldname, function(value) {
// 				// 		frappe.query_report.set_filter_value('party_name', value[fieldname]);
// 				// 	});
// 				// }
// 			}
// 		},
// 		{
// 			"fieldname":"party_name",
// 			"label": __("Party Name"),
// 			"fieldtype": "Data",
// 			"read_only": 1
// 		}
	]
};
