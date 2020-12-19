frappe.ui.form.on("Address", "onload", function(frm, cdt, cdn) {
	frm.set_query('territory', {'is_group': 0});
});