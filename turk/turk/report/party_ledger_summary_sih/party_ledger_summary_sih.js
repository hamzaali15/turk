// Copyright (c) 2016, RC and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Party Ledger Summary SIH"] = {
	"filters": [
		{
            "fieldname": "party_type",
            "fieldtype": "Link",
            "label": "Party Type",
            "options": "Party Type",
            "mandatory": 1
        }
	]
};
