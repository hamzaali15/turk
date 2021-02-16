// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Order with PO Number"] = {
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
           "fieldname": "from_date",
           "fieldtype": "Date",
           "label": "From Date"
       },
       {
           "fieldname": "to_date",
           "fieldtype": "Date",
           "label": "TO Date"
       },
       {
			"fieldname": "po_number",
			"fieldtype": "Data",
			"label": "PO Number"
    	},
    	{
			"fieldname": "customer",
			"fieldtype": "Link",
			"label": "Customer Code",
			"mandatory": 0,
			"options": "Customer"
		}
	]
};
