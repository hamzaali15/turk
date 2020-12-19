{% include "turk/public/js/utils.js" %}

frappe.ui.form.on("Stock Reconciliation", "before_submit", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		if (search_in_roles(frappe.user_roles, "Purchase Manager TC") && Math.abs(frm.doc.difference_amount) >= 500) {
			frappe.throw("you are not allowed to submit Adjustment if difference is above 500 pkr");
			frappe.validated = false;
		}
	}
})

frappe.ui.form.on("Stock Reconciliation", "onload", function (frm, cdt, cdn) {
	var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
});

frappe.ui.form.on("Stock Reconciliation", "validate", function (frm, cdt, cdn) {
	if (frm.doc.unallocated_amount > 0 && frm.doc.party == "LOADER BIKE") {
		msgprint("Excess Payment Cannot be given for this Supplier");
		frappe.validated = false;
		return;
	}
	var ret_obj = setseries(frm.doc.company);
	frm.set_value("naming_series", ret_obj.series);
});

frappe.ui.form.on('Stock Reconciliation', {
	company: function (frm) {
		var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
	}
});

frappe.ui.form.on('Stock Reconciliation Item',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) {
			frappe.model.set_value(cdt, cdn, "qty", 1);
		}
	})

function setseries(company) {
	var ret_obj = { twarehouse: "", series: "" };
	switch (company) {
		case "TURK": ret_obj.series = "TC-SR-"; break;
//		case "T.S ENTERPRISES": ret_obj.series = "TE-SR-"; break;
//		case "KALE FAISALABAD": ret_obj.series = "KF-SR-"; break;
//		case "TILE BAZAR": ret_obj.series = "TB-SR-"; break;
	}
	return ret_obj;
}

function search_in_roles(roles_array, role_string) {
	for (var i = 0; i < roles_array.length; ++i) {
		if (roles_array[i].includes(role_string)) {
			return true;
		}
	}
	return false;
}

