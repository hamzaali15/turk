{% include "turk/public/js/utils.js" %}

frappe.ui.form.on("Sales Invoice", "onload", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		if (frm.doc.is_return == 1) { frm.set_df_property("update_stock", "read_only", 1); }
	//	frm.get_field("custom_delivery_warehouse").get_query = function (doc, cdt, cdn) {
	//		return {
	//			filters: { 'company': doc.company }
	//		}
	//	}
		$.each(frm.doc.items || [], function (i, d) {
			if (!frm.doc.cust_sales_order_owner) {
				get_sales_order_owner(d.sales_order);
			}
			if (d.qty != d.sqm && d.item_code != 'undefined') { CalculateSQM(d, "qty", cdt, cdn); }
		})
		$.each(frm.doc.items || [], function (i, d) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Sales Order",
					filters: { "name": d.sales_order },
					fieldname: "cost_center"
				},
				callback: function (r) {
					d.cost_center = r.message.cost_center
					cur_frm.refresh_field("items");
				}
			})
		})
	}
	frappe.after_ajax(function () {
		setup_warehouse_query('warehouse', frm);
	});
});

frappe.ui.form.on("Sales Invoice", "validate", function (frm, cdt, cdn) {
	if (frm.doc.docstatus == 0) {
		validateBoxes(frm);
		update_item_qty_based_on_sales_order(frm);
		calculate_total_boxes(frm);
		if (frm.doc.calculate_so_discount_ == true) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Sales Order",
					filters: { 'name': frm.doc.cust_sales_order_number },
					fields: ['discount_amount', 'total', 'grand_total']
				},
				callback: function (r) {
					var discount_per = (r.message[0].discount_amount * 100) / r.message[0].total;
					frm.set_value("additional_discount_percentage", discount_per);
					frm.set_value("discount_amount", (frm.doc.total * discount_per) / 100);

				}
			})
		}
		var sales_order_no = "0";
		// var ret_obj = setseries(frm.doc.company); cur_frm.set_value("naming_series", ret_obj.series);
	//	if (!frm.doc.custom_delivery_warehouse) { frm.set_value("custom_delivery_warehouse", "Delivery Depot - TC"); }
		$.each(frm.doc.items || [], function (i, d) {
			if (d.item_group != 'Fixed Assets') {
				if (d.qty == 0 || d.rate == 0) {
					frappe.throw("0 Qty or Rate is not allowed. Please check item " + d.item_code);
					frappe.validated = false; return;
				}
				if (frm.doc.update_stock) {
					if (d.qty > d.actual_qty) {
						frappe.throw("Stock Is not availabe in selected warehouse for item code " + d.item_code);
						frappe.validated = false; return;
					}
				}
			}
			if (typeof d.sales_order !== "undefined") { sales_order_no = d.sales_order; }
		//	if (frm.doc.direct_delivery_from_warehouse && frm.doc.custom_delivery_warehouse != "Delivery Depot - TC") { d.warehouse = frm.doc.custom_delivery_warehouse; }

		})

		$.each(frm.doc.items || [], function (i, d) {

			if (!d.sales_order) { d.sales_order = sales_order_no; }
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Sales Order",
					filters: { "name": d.sales_order },
					fieldname: "cost_center"
				},
				callback: function (r) {
					d.cost_center = r.message.cost_center;
				}
			})
		})
		cur_frm.refresh_field("items");
		if (!frm.doc.ignore_advances_calculation) {
			if (!frm.doc.is_return) {
				return frm.call({
					method: "set_advances",
					doc: frm.doc,
					callback: function (r, rt) {
						refresh_field("advances");
					}
				})
			}
		}
	}
});

frappe.ui.form.on("Sales Invoice", "refresh", function (frm, cdt, cdn) {
	// Validate Items, Update Qty based on Sales Order
	if (frm.doc.docstatus == 0) {
		var item_childtable = frm.fields_dict["items"].$wrapper;
		var grid_buttons = $(item_childtable).find(".grid-buttons");
		if (!$(grid_buttons).find(".custom-update-item-qty").length) {
			$(grid_buttons).append(`
							<button type="reset" class="custom-update-item-qty btn btn-xs btn-default"
									style="margin-left: 4px;">
								Validate Items
							</button>
						`);
		}
		$(grid_buttons).find(".custom-update-item-qty").off().click(function () {
			update_item_qty_based_on_sales_order(frm);
		});
	}
	frappe.after_ajax(function () {
		setup_warehouse_query('warehouse', frm);
	});
	// Split Invoice between Warehouse
	if (frm.doc.docstatus == 0 && !frm.doc.__islocal) {
		var label = __("Split Invoice between Warehouses");
		frm.add_custom_button(label, () => split_invoice_between_warehouse(frm));
	}
});

frappe.ui.form.on('Sales Invoice', {
	// company: function (frm) {
	// 	var ret_obj = setseries(frm.doc.company); frm.set_value("naming_series", ret_obj.series);
	// },
	before_save: function (frm) {
		if (frm.doc.docstatus == 0) {
			update_item_qty_based_on_sales_order(frm);
		}
	},
	// custom_delivery_warehouse: function (frm) {
	// 	$.each(frm.doc.items || [], function (i, d) {
	// 		frappe.model.set_value(d.doctype, d.name, "warehouse", frm.doc.custom_delivery_warehouse);
	// 	})
	// },
 //	direct_delivery_from_warehouse: function (frm) {
// 		if (frm.doc.direct_delivery_from_warehouse) {
// 			frappe.call({
// 				method: "frappe.client.get",
// 				args: {
// 					doctype: "User",
// 					filters: { "name": frappe.session.user },
// 					fieldname: "user_warehouse"
// 				},
// 				callback: function (r) {
// 					if (r.message.user_warehouse) {
// 						frm.set_value("custom_delivery_warehouse", r.message.user_warehouse);
// 					}
// 				}
// 			})
// 		}
// 	}
 });

frappe.ui.form.on('Sales Invoice Item',
	{
		pieces: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "pieces", cdt, cdn); },
		sqm: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "sqm", cdt, cdn); },
		boxes: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "boxes", cdt, cdn); },
		qty: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		item_name: function (frm, cdt, cdn) { CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn); },
		items_add: function (frm, cdt, cdn) {
			var sales_order_no = "";
			$.each(frm.doc.items || [], function (i, d) {
				// if (d.sales_order) { sales_order_no = d.sales_order; }
			});

			if (sales_order_no) {
				var item = locals[cdt][cdn];
				item.sales_order = sales_order_no;
			}
		},
		item_code: function (frm, cdt, cdn) {
			frappe.model.set_value(cdt, cdn, "qty", 1);
			CalculateSQM(locals[cdt][cdn], "qty", cdt, cdn);
		}
	})



// function setseries(company) {
// 	var ret_obj = { twarehouse: "", series: "" };
// 	switch (company) {
// 		case "Turk Tiles": ret_obj.series = "TT-SI-"; break;
// //		case "T.S ENTERPRISES": ret_obj.series = "TE-SI-"; break;
// //		case "KALE FAISALABAD": ret_obj.series = "KF-SI-"; break;
// //		case "TILE BAZAR": ret_obj.series = "TB-SI-"; break;
// 	}
// 	if (cur_frm.doc.is_return) { ret_obj.series = ret_obj.series + "RT-" }
// 	return ret_obj;
// }

function search_in_roles(roles_array, role_string) {
	for (i = 0; i < roles_array.length; ++i) {
		if (roles_array[i].includes(role_string)) {
			return true;
		}
	}
	return false;
}

function get_sales_order_owner(sales_order) {
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Sales Order",
			filters: { "name": sales_order },
			fieldname: "owner"
		},
		callback: function (r) {
			// cur_frm.set_value("cust_sales_order_owner",r.message.owner);
			cur_frm.set_value("sales_order_owner", r.message.owner);
		}
	})
}

function update_item_qty_based_on_sales_order(frm) {
	var items = [];
	$.each(frm.doc.items || [], function (i, d) {
		items.push({
			name: d.name,
			idx: d.idx,
			item_code: d.item_code,
			sales_order: d.sales_order,
			so_detail: d.so_detail,
			parent: frm.doc.name,
			qty: d.qty
		});
	});

	if (items.length) {
		frappe.call({
			method: "turk.utils.update_item_qty_based_on_sales_order",
			args: {
				"items": items
			},
			freeze: true,
			callback: function (r) {
				if (!r.exc) {
					$.each(r.message || {}, function (cdn, row) {
						$.each(row || {}, function (fieldname, value) {
							frappe.model.set_value("Sales Invoice Item", cdn, fieldname, value);
						});
					});
					frm.refresh_field("items");
				}
			}
		});
	}
}

handlePrintButtonClickEvent(cur_frm);

function handlePrintButtonClickEvent(cur_frm) {
	var btn = document.getElementsByClassName('btn-print-print');
	if (btn) {
		for (var i = 0; i < btn.length; i++) {
			if (btn[i].textContent.trim() == "Print") {
				btn[i].addEventListener("click", function () {
					increase_print_count(cur_frm);
				});
				break;
			}
		}
	}
}

function increase_print_count(frm) {
	frappe.db.get_value(frm.doc.doctype, frm.doc.name, "print_count", (r) => {
		frappe.db.set_value(frm.doc.doctype, frm.doc.name, "print_count", Number(r.print_count) + 1);
	});
}

// cur_frm.cscript.onload = function (frm) {
// 	setup_warehouse_query('warehouse', frm);
// }

function split_invoice_between_warehouse(frm) {
	if(frm.is_dirty()) {
		frappe.throw(__("You have unsaved changes. Please save or reload the document first."))
	} else {
	frappe.confirm(__("Are you sure you want to split this Sales Invoice between Warehouses?"),
		() => frappe.call({
			method: "turk.hook_events.sales_invoice.split_invoice_between_warehouse",
			args: {
				"source_name": frm.doc.name
			},
			freeze: true,
			callback: function (r) {
				if (!r.exc) {
					frm.reload_doc();
				}
			}
		}),
		() => window.close()
	);
	}
}