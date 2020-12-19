// Copyright (c) 2020, RC and contributors
// For license information, please see license.txt
{% include "turk/public/js/utils.js" %}

frappe.ui.form.on('Sales Order Updation', {
	refresh: function (frm) {
		frm.disable_save();
		var deleteRowButtonWrapper = $('*[data-fieldname="items"]');
		deleteRowButtonWrapper.find('.grid-remove-rows').hide();
	},
	sales_order: function (frm) {
		loadItems(frm);
		$.each(frm.doc.items || [], function (i, d) {
			set_total_qty(frm, d.doctype, d.name, d.item_code);
		})
	},
	reload_items_btn: function (frm) {
		if (frm.doc.sales_order) {
			loadItems(frm);
		}
	},
	update_items_btn: function (frm) {
		if (validateQty(frm) != false) {
			if (Math.abs(frm.doc.difference) > 5.00) {
				frappe.throw(__("The new total of the items should not exceed the difference of amount 5."));
				return false;
			}

			frappe.call({
				method: 'turk.utils.get_sales_order_items',
				freeze: true,
				args: {
					'sales_order': frm.doc.sales_order,
				},
				callback: function (r) {
					if (r.message) {
						if (r.message.length == frm.doc.items.length) {
							frappe.throw(__("Please add a new item row to update the Sales Order!"));
							return false;
						}
						frappe.call({
							method: 'erpnext.controllers.accounts_controller.update_child_qty_rate',
							freeze: true,
							args: {
								'parent_doctype': "Sales Order",
								'trans_items': frm.doc.items,
								'parent_doctype_name': frm.doc.sales_order,
								'child_docname': "items"
							},
							callback: function() {
								frappe.set_route("Form", "Sales Order", frm.doc.sales_order);
							}
						});
					}
				}
			});
		}
	}
});

frappe.ui.form.on('SO Updation Item',
	{
		pieces: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn);
			calculateNewTotal(frm);
		},
		boxes: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn);
			calculateNewTotal(frm);
		},
		qty: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
			calculateNewTotal(frm);
		},
		sqm: function (frm, cdt, cdn) {
			CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn);
			calculateNewTotal(frm);
		},
		rate: function (frm, cdt, cdn) {
			calculateNewTotal(frm);
		},
		item_code: function (frm, cdt, cdn) {
			var row = locals[cdt][cdn];
			frappe.db.get_value('Item', { 'name': row.item_code }, 'item_name', (r) => {
				frappe.model.set_value(cdt, cdn, "item_name", r.item_name);
				frappe.model.set_value(cdt, cdn, "qty", 1);
			});
			set_total_qty(frm, cdt, cdn);
			$.each(frm.doc.items || [], function (i, d) {
				set_total_qty(frm, d.doctype, d.name, d.item_code);
			})
			frappe.db.get_value('Item Price', { 'item_code': row.item_code, 'price_list': 'Standard Selling' }, 'price_list_rate', (r) => {
				if (r) {
					frappe.model.set_value(cdt, cdn, "rate", r.price_list_rate);
				}
			});
		}
	}
);

function calculateNewTotal(frm) {
	var newTotal = 0;
	frm.doc.items.forEach((item) => {
		newTotal += item.qty * item.rate;
	});
	frm.set_value("new_total", newTotal.toFixed(2));
	frm.set_value("difference", String((frm.doc.total - (newTotal).toFixed(2)).toFixed(2)));
}

function loadItems(frm) {
	if (frm.doc.sales_order) {
		frm.clear_table("items");
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Sales Order",
				name: frm.doc.sales_order,
			},
			callback(r) {
				if (r.message) {
					var so = r.message;
					var itemsReloaded = checkIfOriginalItemsReloaded(frm, so);
					var total = 0;
					if (itemsReloaded == false) {
						reloadItems(frm, so, total);
					}
					frm.refresh_field("items");
				}
			}
		});
	}
}

function getDeliveredQty(sales_order, item_code, so_item_row) {
	var delivered_qty;
	if (sales_order && item_code) {
		frappe.call({
			method: "turk.utils.get_delivered_qty",
			args: {
				sales_order: sales_order,
				item_code: item_code,
				so_item_row: so_item_row
			},
			async: false,
			callback(r) {
				delivered_qty = r.message;
			}
		})
	}
	return delivered_qty;
}

function validateQty(frm) {
	var validated;

	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Sales Order",
			name: frm.doc.sales_order,
		},
		freeze: true,
		async: false,
		callback(r) {
			if (r.message) {
				validated = validateItems(frm, r.message, validated);
			}
		}
	});
	return validated;
}

function checkIfOriginalItemsReloaded(frm, so) {
	var soItems = so.items;
	var updationItems = frm.doc.items;
	if (updationItems.length != soItems.length) {
		return false
	}
	soItems.forEach((soItem) => {
		updationItems.forEach((updationItem) => {
			if (soItem.item_code != updationItem.item_code || soItem.name != updationItem.docname || soItem.rate != updationItem.rate || soItem.qty != updationItem.qty) {
				return false
			}
		})
	})
	return true
}

function reloadItems(frm, so, total) {
	so.items.forEach(d => {
		var newRow = frappe.model.add_child(frm.doc, "SO Updation Item", "items");
		frappe.model.set_value(newRow.doctype, newRow.name, "qty", d.qty);
		newRow.item_code = d.item_code
		newRow.item_name = d.item_name
		newRow.delivered_qty = String(getDeliveredQty(frm.doc.sales_order, d.item_code, d.name))
		newRow.boxes = d.boxes
		newRow.pieces = d.pieces
		newRow.sqm = d.sqm
		newRow.def_boxes = d.def_boxes
		newRow.def_pieces = d.def_pieces
		newRow.rate = d.rate
		newRow.docname = d.name
		newRow.delivery_date = d.delivery_date
		newRow.conversion_factor = d.conversion_factor
		total += newRow.qty * newRow.rate;
	});
	frm.set_value('total', total.toFixed(2));
	refresh_field("items");
}

function validateItems(frm, so, validated) {
	if (so.docstatus != 1) {
		validated = false;
		frappe.throw(__("Please select a submitted Sales Order"));
		return validated;
	}
	so.items.forEach((soItem, i) => {
		var itemExists = undefined;
		frm.doc.items.forEach((updationItem) => {
			if (soItem.item_code == updationItem.item_code && soItem.name == updationItem.docname && soItem.rate == updationItem.rate) {
				itemExists = 1;
			}
		});
		if (itemExists == undefined) {
			validated = false;
			frappe.throw(__("The item or rate in row " + [i + 1] + " should not be replaced!"));
			return validated;
		}
	});
	var updationItems = frm.doc.items;
	updationItems.forEach((updationItem) => {
		if (updationItem.qty < updationItem.delivered_qty) {
			validated = false;
			frappe.throw(__("The qty for item " + updationItem.item_code + " can not be less than delivered qty"));
			return validated;
		}
	});
	return validated;
}