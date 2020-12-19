from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("TURK"),
			"items": [
				{
					"type": "doctype",
					"name": "Sales Order Updation",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Sales Order Summary",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Gross Profit Analysis",
					"doctype": "Sales Invoice",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Gross Profit",
					"doctype": "Sales Invoice",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Accounts Receivable Summary",
					"doctype": "Sales Invoice",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Gross Profit based on Sales Order",
					"doctype": "Sales Order",
					"onboard": 1,
				},

				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Orders With Payment",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Pending Sales Order",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Delivery Status",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Unbilled Customer Orders",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Stock Balance Qty",
					"doctype": "Stock Ledger Entry",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Stock Ledger Qty",
					"doctype": "Stock Ledger Entry",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Low Stock Balance Qty",
					"doctype": "Stock Ledger Entry",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Salesmans Sales Orders With Payment",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Salesmans Pending Sales Orders",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Delivery Status Salesman",
					"doctype": "Sales Order",
					"onboard": 1,
				},
			]
		}
	]
