// frappe.ui.form.on("Journal Entry", "validate", function (frm, cdt, cdn) {
// 	// var ret_obj = setseries(frm.doc.company);
// 	// cur_frm.set_value("naming_series", ret_obj.series);
// });

// frappe.ui.form.on('Journal Entry', {
// 	company: function (frm) {
// 		var ret_obj = setseries(frm.doc.company);
// 		frm.set_value("naming_series", ret_obj.series);
// 	}
// });

// function setseries(company) {
// 	var ret_obj = { twarehouse: "", series: "" };
// 	switch (company) {
// 		case "Turk Tiles": ret_obj.series = "TT-JV-"; break;
// 	}
// 	return ret_obj;
// }

frappe.ui.form.on("Journal Entry Account", "party", function (frm, cdt, cdn) {
	var item = locals[cdt][cdn];
	if (item.party_type == "Customer") {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Customer",
				filters: { "name": item.party },
				fieldname: "customer_name"
			},
			callback: function (r) {
				if (r.message.customer_name) {
					frappe.model.set_value(cdt, cdn, 'party_name', r.message.customer_name);
				}
			}
		});
	}
	if (item.party_type == "Supplier") {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Supplier",
				filters: { "name": item.party },
				fieldname: "supplier_name"
			},
			callback: function (r) {
				if (r.message.supplier_name) {
					frappe.model.set_value(cdt, cdn, 'party_name', r.message.supplier_name);
				}
			}
		});
	}
});