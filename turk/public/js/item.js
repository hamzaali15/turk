frappe.ui.form.on('Item', {
	default_supplier: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	size: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	brand: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	item_group: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	type: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	cust_product_code: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	item_color: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	texture: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	boxes: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	pieces: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	grade_tone_desc: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	},
	tone: function (frm) {
		frm.set_value('item_name', generate_name(frm));
	}
});

function generate_name(frm) {
	if (frm.doc.generate_auto_name) {
		var cust_item_name = "";
		if (frm.doc.default_supplier) {
			if (frm.doc.default_supplier.length > 5) {
				cust_item_name += "S-" + frm.doc.default_supplier.slice(-5);
			}
			else {
				cust_item_name += " " + frm.doc.default_supplier;
			}
		}
		if (frm.doc.size) {
			cust_item_name += " " + frm.doc.size;
		}
		if (frm.doc.brand) {
			cust_item_name += " " + frm.doc.brand;
		}
		if (frm.doc.item_group) {
			cust_item_name += " " + frm.doc.item_group;
		}
		if (frm.doc.type) {
			cust_item_name += " " + frm.doc.type;
		}
		if (frm.doc.cust_product_code) {
			cust_item_name += " " + frm.doc.cust_product_code;
		}
		if (frm.doc.cust_company_code) {
			cust_item_name += " " + frm.doc.cust_company_code;
		}
		if (frm.doc.item_color) {
			cust_item_name += " " + frm.doc.item_color;
		}
		if (frm.doc.texture) {
			cust_item_name += " " + frm.doc.texture;
		}
		if (frm.doc.pieces) {
			if (frm.doc.pieces != 1) {
				cust_item_name += " " + frm.doc.pieces + "-TILES";
			}
			else {
				cust_item_name += " " + frm.doc.pieces;
			}
		}
		if (frm.doc.boxes) {
			cust_item_name += "/" + frm.doc.boxes;
		}
		if (frm.doc.grade_tone_desc) {
			cust_item_name += " " + frm.doc.grade_tone_desc;
		}
		if (frm.doc.tone) {
			cust_item_name += " " + frm.doc.tone;
		}
		return cust_item_name;
	}
	else {
		return frm.doc.item_name;
	}
}