{% include "turk/public/js/utils.js" %}

frappe.ui.form.on("Delivery Note", "before_submit", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		var ret_obj = setseries(frm.doc.company); cur_frm.set_value("naming_series", ret_obj.series);
		var isdelivery_officer = search_in_roles(frappe.user_roles, "Delivery Officer");
		$.each(frm.doc.items || [], function (i, d) {
			if (isdelivery_officer && (d.warehouse.includes('Delivery Depot') == false)) {
				frappe.throw("you are not allowed to submit Delivery Note with Delivery Depot in warehouse");
				frappe.validated = false; return;
			}
		})
	}
})

frappe.ui.form.on("Delivery Note", "onload", function (frm, cdt, cdn) {

	setup_warehouse_query('warehouse', frm);

	if (frm.doc.docstatus == 0) {
		$.each(frm.doc.items || [], function (i, d) {
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
		})
		frm.get_field("custom_delivery_warehouse").get_query = function (doc, cdt, cdn) {
			return {
				filters: { 'company': doc.company }
			}
		}
		var tcost_center = "";
		$.each(frm.doc.items || [], function (i, d) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Sales Order",
					filters: { "name": d.against_sales_order },
					fieldname: "cost_center"
				},
				callback: function (r) {
					d.cost_center = r.message.cost_center
					cur_frm.refresh_field("items");
				}
			})
		})
	}
});

frappe.ui.form.on("Delivery Note", "validate", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		var ret_obj = setseries(frm.doc.company); cur_frm.set_value("naming_series", ret_obj.series);
		var tcost_center = "Test";
	//	if (!frm.doc.custom_delivery_warehouse) { frm.set_value("custom_delivery_warehouse", "Delivery Depot"); }
		$.each(frm.doc.items || [], function (i, d) {
		//	if (frm.doc.direct_delivery_from_warehouse && frm.doc.custom_delivery_warehouse != "Delivery Depot") { d.warehouse = frm.doc.custom_delivery_warehouse; }
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Sales Order",
					filters: { "name": d.against_sales_order },
					fieldname: "cost_center"
				},
				callback: function (r) {
					d.cost_center = r.message.cost_center;

				}
			})
		});

		calculate_total_boxes(frm);
//		if (frm.doc.custom_delivery_warehouse.includes("Delivery Depot -")) { frm.set_value("custom_delivery_warehouse", "Delivery Depot"); }
		cur_frm.refresh_field("items");

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

frappe.ui.form.on('Delivery Note', {
	company: function (frm) {
		var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
	}
});

frappe.ui.form.on('Delivery Note Item',
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
	var ret_obj = { twarehouse: "", series: "" };
	switch (company) {
		case "TURK": ret_obj.series = "TC-DN-"; break;
//		case "T.S ENTERPRISES": ret_obj.series = "TE-DN-"; break;
//		case "KALE FAISALABAD": ret_obj.series = "KF-DN-"; break;
//		case "TILE BAZAR": ret_obj.series = "TB-DN-"; break;
	}
	return ret_obj;
}
