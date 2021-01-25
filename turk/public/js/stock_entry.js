{% include "turk/public/js/utils.js" %}

frappe.ui.form.on("Stock Entry", "before_submit", function (frm, cdt, cdn) {
	 if (frm.doc.docstatus == 0) {
	// 	if (frm.doc.purpose != "Material Transfer") {
	// 		frappe.throw("You cannot submit Stock Entry other than Material Transfer. Please change purpose to Material Transfer ");
	// 		frappe.validated = false;
	// 	}
		var is_warehouse_incharge = search_in_roles(frappe.user_roles, "Warehouse Incharge TT")
		$.each(frm.doc.items || [], function (i, d) {
			if (is_warehouse_incharge && (d.t_warehouse.includes("Delivery Depot"))) {
				frappe.throw("You cannot submit Stock Entry to Delivery Depot. Please Duplicate this Stock Entry and Select Transfer Type"); frappe.validated = false;
			}
		})
	}
})

frappe.ui.form.on('Stock Entry', {
	company: function (frm) {
		setup_warehouse_query('s_warehouse', frm);
		setup_warehouse_query('t_warehouse', frm);
		if (frm.doc.docstatus == 0) {
			var ret_obj = setseries(frm.doc.company);
			frm.set_value("naming_series", ret_obj.series);
		}
	},
	transfer_type: function (frm) {
		setWarehouses(frm);
	},
	refresh: function(frm) {
		if (frm.doc.docstatus===0) {
			frm.add_custom_button(__('Sales Return'), function() {
				erpnext.utils.map_current_doc({
					method: "turk.utils.make_stock_entry",
					source_doctype: "Sales Invoice",
					target: frm,
					date_field: "posting_date",
					setters: {
						customer: frm.doc.customer || undefined,
					},
					get_query_filters: {
						docstatus: 1,
						is_return:1,
						company:frm.doc.company
					}
				})
			}, __("Get items from"));
		}
	}
});

function search_in_roles(roles_array, role_string) {
	for (var i = 0; i < roles_array.length; ++i) {
		if (roles_array[i].includes(role_string)) {
			return true;
		}
	}
	return false;
}

function company_initial(company, res) {
	if (company == 'TURK') { res = res + " TC"; }
//	else if (company == 'T.S ENTERPRISES') { res = res + " TE"; }
//	else if (company == 'TILE BAZAR') { res = res + " TB"; }
//	else if (company == 'KALE FAISALABAD') { res = res + " KF"; }
	return res;
}

frappe.ui.form.on("Stock Entry", "onload", function (frm, cdt, cdn) {
	var ret_obj = setseries(frm.doc.company);
	frm.set_value("naming_series", ret_obj.series);
	if (frm.doc.docstatus == 0) {
		$.each(frm.doc.items || [], function (i, d) {
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
		})
	}
});

frappe.ui.form.on("Stock Entry", "validate", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		var ret_obj = setseries(frm.doc.company);
		frm.set_value("naming_series", ret_obj.series);
		$.each(frm.doc.items || [], function (i, d) {
			if (frm.doc.from_warehouse != d.s_warehouse && i == 0) {
				frm.set_value('from_warehouse', d.s_warehouse);
			}
			setWarehouses(frm);
		});
		calculate_total_boxes(frm);
	}
});

// function SetUserWarehouse(source) {
// 	if (cur_frm.doc.docstatus == 0) {
// 		frappe.call({
// 			method: "frappe.client.get",
// 			args: { doctype: "User", filters: { "name": frappe.session.user }, fieldname: "user_warehouse" },
// 			callback: function (r) {
// 				if (r.message.user_warehouse) {
// 					if (source == "To") {
// 						cur_frm.set_value('to_warehouse', r.message.user_warehouse);
// 					}
// 					if (source == "From") {
// 						cur_frm.set_value('from_warehouse', r.message.user_warehouse);
// 					}
// 				}
// 			}
// 		})
// 	}
// }

frappe.ui.form.on('Stock Entry Detail',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); }
	})

function CalculateSQM(crow, field, cdt, cdn) {
	if (typeof crow.def_boxes != 'undefined' && crow.def_boxes && crow.def_boxes > 0) {
		var total_piece = 0.0;
		switch (field) {
			case "pieces": total_piece = Math.round(crow.pieces + (crow.boxes * crow.def_pieces)); break;
			case "boxes": total_piece = Math.round(crow.boxes * crow.def_pieces); break;
			case "sqm": total_piece = Math.round(crow.sqm / (crow.def_boxes / crow.def_pieces)); break;
			case "qty": total_piece = Math.round(crow.qty / (crow.def_boxes / crow.def_pieces));
		}
		var new_sqm = parseFloat((total_piece * (crow.def_boxes / crow.def_pieces)).toFixed(4));
		crow.boxes = Math.floor((new_sqm / crow.def_boxes).toFixed(4));
		crow.pieces = (total_piece % crow.def_pieces);
		frappe.model.set_value(cdt, cdn, 'qty', new_sqm);
		crow.sqm = new_sqm;
		cur_frm.refresh_field("items");
	}
	else {
		var new_sqm = 0;
		switch (field) {
			case "pieces": new_sqm = crow.pieces; break;
			case "boxes": new_sqm = crow.boxes; break;
			case "sqm": new_sqm = crow.sqm; break;
			case "qty": new_sqm = crow.qty; break;
		}
		crow.sqm = new_sqm; crow.boxes = new_sqm; crow.pieces = new_sqm; crow.qty = new_sqm;
		cur_frm.refresh_field("items");
	}
}

function setseries(company) {
	var ret_obj = { series: "" };
	switch (company) {
		case "Turk Tiles": ret_obj.series = "TT-STE-"; break;
	}
	return ret_obj;
}

function setWarehouses(frm) {
	if (frm.doc.transfer_type == 'OUTWARD' && frm.doc.docstatus == 0) {
		if (search_in_roles(frappe.user_roles, "Warehouse Incharge TT")) {
			frm.set_value('to_warehouse', company_initial(frm.doc.company, "Transit -"));
			SetUserWarehouse("From");
		}
		else if (search_in_roles(frappe.user_roles, "Delivery Officer TT")) { frm.set_value('to_warehouse', ""); SetUserWarehouse("From"); }
	}
	if (frm.doc.transfer_type == 'INWARD' && frm.doc.docstatus == 0) {
		if (search_in_roles(frappe.user_roles, "Warehouse Incharge TT") || search_in_roles(frappe.user_roles, "Delivery Officer TC")) {
			frm.set_value('from_warehouse', company_initial(frm.doc.company, "Transit -"));
			SetUserWarehouse("To");
		}
	}
}