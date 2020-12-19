// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */


frappe.query_reports["Sales Return by Salesman"] = {
	"filters": [
		{
            "fieldname":"company",
            "label": __("Company"),
            "fieldtype": "Link",
	     	"options": "Company",
            "reqd": 1
        } ,
		{
			"fieldname":"sales_order",
			"label": __("Sales Order"),
			"fieldtype": "Data"
		}
	]
}
