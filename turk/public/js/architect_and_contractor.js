frappe.ui.form.on("Architect and Contractor", {
	cell_no: function (frm) {
		validate_number(frm);
	},
	cell_no_2: function (frm) {
		validate_number(frm);
	}
});

function validate_number(frm) {
	if (frm.doc.cell_no) {
		var reg = /[^0-9]/g;
		frm.set_value("cell_no", frm.doc.cell_no.replace(reg, ''));
		if (!(frm.doc.cell_no.length == 11 || reg.test(frm.doc.cell_no))) {
			frappe.throw("Phone Number should be 11 digit and Numbers only. ");
			frappe.validated = false;
			return;
		}
	}
	if (frm.doc.cell_no_2) {
		var reg = /[^0-9]/g;
		frm.set_value("cell_no_2", frm.doc.cell_no_2.replace(reg, ''));
		if (!(frm.doc.cell_no_2.length == 11 || reg.test(frm.doc.cell_no_2))) {
			frappe.throw("Phone Number should be 11 digit and Numbers only. ");
			frappe.validated = false; return;
		}
	}
}