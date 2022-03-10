# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "turk"
app_title = "TURK"
app_publisher = "RC"
app_description = "Customizations for TURK"
app_icon = "octicon octicon-file-directory"
app_color = "green"
app_email = "developer@rccorner.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/turk/css/turk.css"
# app_include_js = "/assets/turk/js/turk.js"

# include js, css files in header of web template
# web_include_css = "/assets/turk/css/turk.css"
# web_include_js = "/assets/turk/js/turk.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

doctype_js = {
		"Address": "public/js/address.js",
		"Architect and Contractor": "public/js/architect_and_contractor.js",
		"Authorization Rule": "public/js/authorization_rule.js",
		"Customer": "public/js/customer.js",
		"Delivery Note" : "public/js/delivery_note.js",
		"Item": "public/js/item.js",
		"Journal Entry": "public/js/journal_entry.js",
		"Landed Cost Voucher": "public/js/landed_cost_voucher.js",
		"Material Request" : "public/js/material_request.js",
		"Opportunity": "public/js/opportunity.js",
		"Payment Entry": "public/js/payment_entry.js",
		"Property Detail": "public/js/property_detail.js",
		"Purchase Invoice" : "public/js/purchase_invoice.js",
		"Purchase Order" : "public/js/purchase_order.js",
		"Purchase Receipt" : "public/js/purchase_receipt.js",
		"Quotation" : "public/js/quotation.js",
		"Request for Quotation": "public/js/request_for_quotation.js",
		"Salary Slip" : "public/js/salary_slip.js",
		"Sales Invoice" : "public/js/sales_invoice.js",
		"Sales Order" : "public/js/sales_order.js",
		"Stock Entry" : "public/js/stock_entry.js",
		"Stock Reconciliation" : "public/js/stock_reconciliation.js",
		"Supplier Quotation": "public/js/supplier_quotation.js"
	}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "turk.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "turk.install.before_install"
# after_install = "turk.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "turk.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
	"Sales Order": {
		"validate": "turk.hook_events.sales_order.set_average_valuation_rate",
		"before_submit": "turk.hook_events.sales_order.unset_needs_approval",
		"before_update_after_submit": "turk.hook_events.sales_order.validate_items_rate_and_update_boxes"
	},
	"Sales Invoice": {
		"validate": [
			"turk.hook_events.sales_invoice.validate_discount_while_return",
			"turk.hook_events.sales_invoice.validate_taxes_and_charges_from_so",
			"turk.utils.add_location",
			"turk.hook_events.sales_invoice.validate_sales_invoice"
		],
		"before_insert": "turk.hook_events.sales_invoice.set_supplier_details",
		"on_submit": [
			"turk.hook_events.sales_invoice.update_reserved_qty",
			"turk.hook_events.sales_invoice.create_purchase_invoices_against_sales_taxes",
			"turk.hook_events.party_link.create_invoice_adj_jv"
		],
		"on_cancel": [
			"turk.hook_events.sales_invoice.update_reserved_qty",
			"turk.hook_events.party_link.cancel_adjusted_jv"
		]
	},
	"Payment Entry": {
		"validate": "turk.hook_events.payment_entry.validate_sales_order"
	},
	"Opportunity": {
		"validate": "turk.utils.send_followup_sms"
	},
	"Purchase Invoice" :{
		"validate": "turk.utils.add_location",
		"on_submit": "turk.hook_events.party_link.create_invoice_adj_jv",
		"on_cancel": "turk.hook_events.party_link.cancel_adjusted_jv"
	},
	"Journal Entry" :{
		"on_cancel" : "turk.hook_events.party_link.prevent_linked_jv_cancellation"
	}
}


jenv = {
	"methods" : [
	"get_qrcode_image:turk.utils.get_qrcode_image"
	]
}


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"turk.tasks.all"
# 	],
# 	"daily": [
# 		"turk.tasks.daily"
# 	],
# 	"hourly": [
# 		"turk.tasks.hourly"
# 	],
# 	"weekly": [
# 		"turk.tasks.weekly"
# 	]
# 	"monthly": [
# 		"turk.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "turk.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "turk.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "turk.task.get_dashboard_data"
# }

