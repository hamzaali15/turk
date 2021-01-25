{% include "turk/public/js/utils.js" %}
frappe.provide('turk.stock');


frappe.ui.form.on('Purchase Receipt', {
	company: function (frm) { if (frm.doc.docstatus == 0) { var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series); } },

	charge_to_supplier: function (frm) {
		if (frm.doc.docstatus == 0) {
		//	frm.set_value("charge_to_company", (parseFloat(frm.doc.breakage_total_amount) - parseFloat(frm.doc.charge_to_supplier)));
		}
	}
});

frappe.ui.form.on("Purchase Receipt", "validate", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		validateBoxes(frm);
		var ret_obj = setseries(frm.doc.company);
		frm.set_value("naming_series", ret_obj.series);
		CalculateBreakage(frm);
		$.each(frm.doc.items || [], function (i, d) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "User",
					filters: { "name": frappe.session.user },
					fieldname: "user_warehouse"
				},
				callback: function (r) {
					if (r.message.user_warehouse) {
						d.warehouse = r.message.user_warehouse;
					}
					if (d.rejected_qty > 0) {
						d.rejected_warehouse = r.message.user_warehouse.replace("Normal", "Breakage");
					}
				}
			})
		});
		//calculate_total_boxes(frm);
	}
});

frappe.ui.form.on("Purchase Receipt", "onload", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		$.each(frm.doc.items || [], function (i, d) {
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "received_qty", cdt, cdn); }
		})
		$.each(frm.doc.items || [], function (i, d) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "User",
					filters: { "name": frappe.session.user },
					fieldname: "user_warehouse"
				},
				callback: function (r) {
					if (r.message.user_warehouse) { d.warehouse = r.message.user_warehouse; }
					d.rejected_warehouse = r.message.user_warehouse.replace("Normal", "Breakage");
				}
			})
		})
		frm.refresh_field("items");
	}
});

frappe.ui.form.on("Purchase Receipt", "before_submit", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		if (frm.doc.supplier != "S-00095") {
			if (!frm.doc.is_return) {
			//	frm.set_value("discount_amount", (-1 * parseFloat(frm.doc.charge_to_company)));
			}
		}
		$.each(frm.doc.items || [], function (i, d) {
			var tempitemname = d.item_name;
			if (tempitemname.includes("Dummy") == true) {
				frappe.throw("You cannot submit Purchase Receipt if it contains dummy Item");
				frappe.validated = false;
			}
		})
	}
})

frappe.ui.form.on('Purchase Receipt Item',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		received_qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "received_qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "received_qty", cdt, cdn); },
		rejected_qty: function (frm, cdt, cdn) { CalculateBreakage(frm); },
		rate: function (frm, cdt, cdn) { CalculateBreakage(frm); },
		rejected_boxes: function (frm, cdt, cdn) {
			var row = locals[cdt][cdn];
			var total_piece = 0;
			if (typeof row.def_boxes != 'undefined' && row.def_boxes) {
				var total_piece = Math.round(row.rejected_boxes * row.def_pieces);
				var new_rej_sqm = parseFloat((total_piece * (row.def_boxes / row.def_pieces)).toFixed(4));
				if (new_rej_sqm > 0) {
					row.rejected_boxes = Math.floor((new_rej_sqm / row.def_boxes).toFixed(4));
				} else { row.rejected_boxes = Math.ceil((new_rej_sqm / row.def_boxes).toFixed(4)); }
				row.rejected_pieces = (total_piece % row.def_pieces);
				frappe.model.set_value(cdt, cdn, 'rejected_qty', new_rej_sqm);
				frm.refresh_field("items");
			}
		},
		rejected_pieces: function (frm, cdt, cdn) {
			var row = locals[cdt][cdn];
			var total_piece = 0;
			var total_piece = Math.round(row.rejected_pieces + (row.rejected_boxes * row.def_pieces));
			var new_rej_sqm = parseFloat(total_piece * (row.def_boxes / row.def_pieces));
			row.rejected_boxes = Math.floor(new_rej_sqm / row.def_boxes);
			row.rejected_pieces = (total_piece % row.def_pieces);
			frappe.model.set_value(cdt, cdn, 'rejected_qty', new_rej_sqm);
			frm.refresh_field("items");
		},
		item_code: function (frm, cdt, cdn) {
			frappe.model.set_value(cdt, cdn, "received_qty", 1);
			CalculateSQM(locals[cdt][cdn], "received_qty", cdt, cdn);
		}
	})

function CalculateSQM(crow, field, cdt, cdn) {
	if (typeof crow.def_boxes != 'undefined' && crow.def_boxes && crow.def_boxes > 0) {
		var total_piece = 0.0;
		switch (field) {
			case "pieces": total_piece = Math.round(crow.pieces + (crow.boxes * crow.def_pieces)); break;
			case "boxes": total_piece = Math.round(crow.boxes * crow.def_pieces); break;
			case "sqm": total_piece = Math.round(crow.sqm / (crow.def_boxes / crow.def_pieces)); break;
			case "received_qty": total_piece = Math.round(crow.received_qty / (crow.def_boxes / crow.def_pieces));
		}
		var new_sqm = parseFloat((total_piece * (crow.def_boxes / crow.def_pieces)).toFixed(4));
		if (new_sqm > 0) {
			crow.boxes = Math.floor((new_sqm / crow.def_boxes).toFixed(4));
		}
		else {
			crow.boxes = Math.ceil((new_sqm / crow.def_boxes).toFixed(4));
		}
		crow.pieces = (total_piece % crow.def_pieces);
		frappe.model.set_value(cdt, cdn, 'received_qty', new_sqm);
		crow.sqm = new_sqm;
		cur_frm.refresh_field("items");
	}
	else {
		var new_sqm = 0;
		switch (field) {
			case "pieces": new_sqm = crow.pieces; break;
			case "boxes": new_sqm = crow.boxes; break;
			case "sqm": new_sqm = crow.sqm; break;
			case "received_qty": new_sqm = crow.qty; break;
		}
		crow.sqm = new_sqm; crow.boxes = new_sqm; crow.pieces = new_sqm; crow.received_qty = new_sqm;
		cur_frm.refresh_field("items");
	}
}
function setseries(company) {
	var ret_obj = { series: "" };
	switch (company) {
		case "TURK": ret_obj.series = "TT-PR-"; break;
	}

	return ret_obj;
}

function CalculateBreakage(frm) {
	var total_breakage = 0;
	$.each(frm.doc.items || [], function (i, d) {
		if (d.rejected_qty > 0) { total_breakage += d.rejected_qty * d.rate; }
	})
	//frm.set_value('breakage_total_amount', total_breakage);
	//frm.set_value('charge_to_company', total_breakage - frm.doc.charge_to_supplier);
}

turk.stock.PurchaseReceiptController = erpnext.stock.PurchaseReceiptController.extend({
	refresh: function () {
		this._super();
		if (!this.frm.doc.is_return && this.frm.doc.status != "Closed") {
			if (this.frm.doc.docstatus == 0) {
				cur_frm.remove_custom_button(__("Purchase Order"), "Get items from");

				this.frm.add_custom_button(__('Purchase Order'),
					function () {
						erpnext.utils.map_current_doc({
							method: "turk.utils.ts_make_purchase_receipt",
							source_doctype: "Purchase Order",
							target: me.frm,
							setters: {
								supplier: me.frm.doc.supplier || undefined,
							},
							get_query_filters: {
								docstatus: 1,
								status: ["not in", ["Closed", "On Hold"]],
								per_received: ["<", 99.99],
								company: me.frm.doc.company
							}
						})
					}, __("Get items from"));
			}
		}
	}
});

$.extend(cur_frm.cscript, new turk.stock.PurchaseReceiptController({ frm: cur_frm }));
