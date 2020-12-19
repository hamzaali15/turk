frappe.ui.form.on("Property Detail", {
	tiles_qty: function (frm) { calculate_total(frm); },
	tiles_rate: function (frm) { calculate_total(frm); },
	fittings_qty: function (frm) { calculate_total(frm); },
	fittings_rate: function (frm) { calculate_total(frm); },
	laticrete_qty: function (frm) { calculate_total(frm); },
	laticrete_rate: function (frm) { calculate_total(frm); },
	ceramics_qty: function (frm) { calculate_total(frm); },
	ceramics_rate: function (frm) { calculate_total(frm); },
	accessories_qty: function (frm) { calculate_total(frm); },
	accessories_rate: function (frm) { calculate_total(frm); },
	kitchen_appliances_qty: function (frm) { calculate_total(frm); },
	kitchen_appliances_rate: function (frm) { calculate_total(frm); }
});

function calculate_total(frm) {
	frm.set_value("tiles_amount", (frm.doc.tiles_qty * frm.doc.tiles_rate));
	frm.set_value("fittings_amount", (frm.doc.fittings_qty * frm.doc.fittings_rate));
	frm.set_value("laticrete_amount", (frm.doc.laticrete_qty * frm.doc.laticrete_rate));
	frm.set_value("ceramics_amount", (frm.doc.ceramics_qty * frm.doc.ceramics_rate));
	frm.set_value("accessories_amount", (frm.doc.accessories_qty * frm.doc.accessories_rate));
	frm.set_value("kitchen_appliances_amount", (frm.doc.kitchen_appliances_qty * frm.doc.kitchen_appliances_rate));
	frm.set_value("total_potential", (frm.doc.tiles_amount + frm.doc.fittings_amount + frm.doc.laticrete_amount +
		frm.doc.ceramics_amount + frm.doc.accessories_amount + frm.doc.kitchen_appliances_amount));
}
