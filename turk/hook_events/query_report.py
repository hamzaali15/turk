import frappe
from frappe.desk.query_report import get_script as core_get_script
from frappe.desk.query_report import run as core_run

CUSTOM_REPORT_OVERRIDES = {
	"General Ledger": {
		"app": "turk",
		"folder": ["turk", "report", "general_ledger"],
		"html": "general_ledger.html",
		"extra_js": "general_ledger_extra.js",
	},
}


@frappe.whitelist()
def get_script(report_name: str):
	result = core_get_script(report_name)

	override = CUSTOM_REPORT_OVERRIDES.get(report_name)
	if not override:
		return result

	html_path = frappe.get_app_path(override["app"], *override["folder"], override["html"])
	with open(html_path) as f:
		result["html_format"] = f.read()

	if override.get("extra_js"):
		js_path = frappe.get_app_path(override["app"], *override["folder"], override["extra_js"])
		with open(js_path) as f:
			result["script"] = (result.get("script") or "") + "\n\n" + f.read()

	return result


@frappe.whitelist()
@frappe.read_only()
def run(report_name, filters=None, user=None, ignore_prepared_report=False, custom_columns=None,
	is_tree=False, parent_field=None, are_default_filters=True):
	"""Run the report, then flag General Ledger rows that belong to a return Sales Invoice (Credit Note)
	so the print format can colour them."""
	result = core_run(
		report_name,
		filters=filters,
		user=user,
		ignore_prepared_report=ignore_prepared_report,
		custom_columns=custom_columns,
		is_tree=is_tree,
		parent_field=parent_field,
		are_default_filters=are_default_filters,
	)

	if report_name == "General Ledger" and isinstance(result, dict):
		rows = [r for r in (result.get("result") or []) if isinstance(r, dict)]
		names = {r.get("voucher_no") for r in rows if r.get("voucher_type") == "Sales Invoice" and r.get("voucher_no")}
		if names:
			returns = set(
				frappe.get_all("Sales Invoice", filters={"name": ["in", list(names)], "is_return": 1}, pluck="name")
			)
			for r in rows:
				if r.get("voucher_type") == "Sales Invoice" and r.get("voucher_no") in returns:
					r["is_return"] = 1

	return result
