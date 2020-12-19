{% include "turk/public/js/utils.js" %}

frappe.ui.form.on("Material Request", "onload", function (frm, cdt, cdn) {
	setup_warehouse_query('warehouse', frm);
	setup_warehouse_query('custom_warehouse_name', frm);

	if (frm.doc.docstatus == 0) {
		var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
		frm.set_value("material_request_type", "Material Transfer");
		$.each(frm.doc.items || [], function (i, d) {
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
		})
	}
});

frappe.ui.form.on("Material Request", "validate", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
		validateBoxes(frm);
	}

});

frappe.ui.form.on('Material Request', {
	company: function (frm) {
		var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
	}
});

frappe.ui.form.on('Material Request Item',
	{
		pieces: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn);
			calculateTotals(frm)
		},
		sqm: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn);
			calculateTotals(frm)
		},
		boxes: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn);
			calculateTotals(frm)
		},
		qty: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
			calculateTotals(frm)
		},
		item_name: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
			calculateTotals(frm)
		},
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
	calculate_total_boxes(cur_frm);
}

function setseries(company) {
	var ret_obj = { twarehouse: "", series: "" };
	switch (company) {
		case "TURK": ret_obj.series = "TC-MR-"; break;
//		case "T.S ENTERPRISES": ret_obj.series = "TE-MR-"; break;
//		case "KALE FAISALABAD": ret_obj.series = "KF-MR-"; break;
//		case "TILE BAZAR": ret_obj.series = "TB-MR-"; break;
	}
	return ret_obj;
}

function calculateTotals(frm) {
	var amount = 0, total_weight = 0;
	$.each(frm.doc["items"] || [], function (i, item) {
		amount += item.amount;
		total_weight += item.qty * item.weight_per_unit;
	});
	frm.set_value("total", amount);
	frm.set_value("total_net_weight", total_weight);
}