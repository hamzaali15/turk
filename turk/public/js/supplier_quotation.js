frappe.ui.form.on("Payment Entry", "onload", function (frm, cdt, cdn) {
	var ret_obj = setseries(frm.doc.company);
	frm.set_value("naming_series", ret_obj.series);
});

frappe.ui.form.on("Payment Entry", "validate", function (frm, cdt, cdn) {
	if (frm.doc.unallocated_amount > 0 && frm.doc.party == "LOADER BIKE") {
		msgprint("Excess Payment Cannot be given for this Supplier");
		frappe.validated = false;
		return;
	}
	var ret_obj = setseries(frm.doc.company);
	cur_frm.set_value("naming_series", ret_obj.series);
});

frappe.ui.form.on('Payment Entry', {
	company: function (frm) {
		var ret_obj = setseries(frm.doc.company);
		frm.set_value("naming_series", ret_obj.series);
	}
});

function setseries(company) {
	var ret_obj = { twarehouse: "", series: "" };
	switch (company) {
		case "TURK": ret_obj.series = "TC-SQT-"; break;
//		case "T.S ENTERPRISES": ret_obj.series = "TE-SQT-"; break;
//		case "KALE FAISALABAD": ret_obj.series = "KF-SQT-"; break;
//		case "TILE BAZAR": ret_obj.series = "TB-SQT-"; break;
	}
	return ret_obj;
}
