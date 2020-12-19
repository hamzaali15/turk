{% include "turk/public/js/utils.js" %}

frappe.ui.form.on("Quotation", "onload", function (frm, cdt, cdn) {
	var ret_obj = setseries(frm.doc.company);
	frm.set_value("naming_series", ret_obj.series);
	$.each(frm.doc.items || [], function (i, d) {
		if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
	})
	if (frm.doc.quotation_to == "Customer") {
		set_address_query(frm, frm.doc.party_name);
	}
});

frappe.ui.form.on("Quotation", "validate", function (frm, cdt, cdn) {
	validateBoxes(frm);
	var ret_obj = setseries(frm.doc.company);
	frm.set_value("naming_series", ret_obj.series);
	$.each(frm.doc.items || [], function (i, d) {
		d.warehouse = ret_obj.twarehouse
	})
});

frappe.ui.form.on("Quotation", "refresh", function (frm, cdt, cdn) {
	if (frm.doc.quotation_to == "Customer") {
		frm.fields_dict.party_name.get_query = function (doc, cdt, cdn) {
			return { query: "erpnext.controllers.queries.customer_query" }
		}
		set_address_query(frm, frm.doc.party_name);
	}
	if (frm.doc.docstatus == 0 && frm.doc.company) {
		$.each(frm.doc.items || [], function (i, d) {
			set_total_qty(frm, d.doctype, d.name, d.item_code);
		})
	}
});

frappe.ui.form.on('Quotation Item',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		company: cur_frm.cscript.company = function (doc, cdt, cdn) { var ret_obj = setseries(doc.company); cur_frm.set_value("naming_series", ret_obj.series); },
		item_code: function (frm, cdt, cdn) {
			frappe.model.set_value(cdt, cdn, "qty", 1);
			frappe.model.set_value(cdt, cdn, "discount_percentage", 0);
			frappe.model.set_value(cdt, cdn, "discount_amount", 0);
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
			set_total_qty(frm, cdt, cdn);
		}
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
	var ret_obj = { twarehouse: "", series: "" };
	switch (company) {
		case "TURK": ret_obj.series = "TC-QTN-"; break;
	//	case "T.S ENTERPRISES": ret_obj.series = "TE-QTN-"; break;
	//	case "KALE FAISALABAD": ret_obj.series = "KF-QTN-"; break;
	//	case "TILE BAZAR": ret_obj.series = "TB-QTN-"; break;
	}
	return ret_obj;
}
