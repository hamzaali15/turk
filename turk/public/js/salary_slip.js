frappe.ui.form.on("Salary Slip", {
	refresh: function (frm) {
		if (frm.doc.docstatus == 1) {
			var label = __("Make Payment");
			frm.add_custom_button(label, function () {
				frappe.model.open_mapped_doc({
					method: "turk.utils.make_payment",
					frm: frm
				})
			});
		}
	}

})