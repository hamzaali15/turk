{% include "turk/public/js/utils.js" %}
frappe.provide('turk.buying');

frappe.ui.form.on("Purchase Order", {
	schedule_date: function (frm) {
		if (frm.doc.docstatus == 0) {
			$.each(frm.doc.items || [], function (i, d) {
			d.expected_delivery_date = frm.doc.schedule_date;
				d.schedule_date = frm.doc.schedule_date;
			})
		}
	},
	company: function (frm) {
		var ret_obj = setseries(frm.doc.company);
		frm.set_value("naming_series", ret_obj.series);
	}
});
frappe.ui.form.on("Purchase Order", "onload", function (frm, cdt, cdn) {
	var ret_obj = setseries(frm.doc.company);
	frm.set_value("naming_series", ret_obj.series);
	$.each(frm.doc.items || [], function (i, d) {
		if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
	})
});

frappe.ui.form.on("Purchase Order", "validate", function (frm, cdt, cdn) {
	var ret_obj = setseries(frm.doc.company);
	validateBoxes(frm);
	frm.set_value("naming_series", ret_obj.series);
	$.each(frm.doc.items || [], function (i, d) {
		d.warehouse = ret_obj.twarehouse;
	})
	calculate_total_boxes(frm);
});


frappe.ui.form.on('Purchase Order Item',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_code: function (frm, cdt, cdn) {
			frappe.model.set_value(cdt, cdn, "qty", 1);
			frappe.model.set_value(cdt, cdn, "discount_percentage", 0);
			frappe.model.set_value(cdt, cdn, "discount_amount", 0);
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
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
		case "TURK": ret_obj.twarehouse = "Head Office - TC"; ret_obj.series = "TC-PO-"; break;
//		case "T.S ENTERPRISES": ret_obj.twarehouse = "Head Office - TE"; ret_obj.series = "TE-PO-"; break;
//		case "KALE FAISALABAD": ret_obj.twarehouse = "Head Office - KF"; ret_obj.series = "KF-PO-"; break;
//		case "TILE BAZAR": ret_obj.twarehouse = "Head Office - TB"; ret_obj.series = "TB-PO-"; break;
	}
	return ret_obj;
}

ts.buying.PurchaseOrderController = erpnext.buying.PurchaseOrderController.extend({
	refresh: function (doc, cdt, cdn) {
		this._super(doc);
		var allow_receipt = false;
		var is_drop_ship = false;

		for (var i in cur_frm.doc.items) {
			var item = cur_frm.doc.items[i];
			if (item.delivered_by_supplier !== 1) {
				allow_receipt = true;
			} else {
				is_drop_ship = true;
			}

			if (is_drop_ship && allow_receipt) {
				break;
			}
		}
		cur_frm.remove_custom_button(__("Receipt"), "Create");

		if (doc.docstatus == 1) {
			if (doc.status != "Closed") {
				if (doc.status != "On Hold") {
					if (flt(doc.per_received, 2) < 100 && allow_receipt) {
						cur_frm.add_custom_button(__('Receipt'), this.ts_make_purchase_receipt, __('Create'));
					}
				}
			}

		}
	},
	ts_make_purchase_receipt: function () {
		frappe.model.open_mapped_doc({
			method: "turk.utils.ts_make_purchase_receipt",
			frm: cur_frm
		})
	}
});

$.extend(cur_frm.cscript, new ts.buying.PurchaseOrderController({ frm: cur_frm }));
